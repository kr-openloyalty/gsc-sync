#!/usr/bin/env python3
"""
MQL contact keyword report

Pulls MQL contacts live from HubSpot, queries GSC for the top keyword on
the contact's first visit date (falls back to createdate), and writes a CSV.

Requirements:
  HUBSPOT_TOKEN env var  — HubSpot Private App token
  token.json             — GSC OAuth token (run auth.py once)

Usage:
  HUBSPOT_TOKEN=pat-xxx python3 mql_keyword_report.py \
      --start 2026-05-01 --end 2026-05-31 --output may_mqls.csv
"""

import argparse
import csv
import json
import os
import re
import warnings
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HUBSPOT_TOKEN = os.environ.get("HUBSPOT_TOKEN")
TOKEN_FILE    = "token.json"
SITE          = "sc-domain:openloyalty.io"
GSC_API       = "https://www.googleapis.com/webmasters/v3"
HS_API        = "https://api.hubapi.com"

AB_RE = re.compile(r"^/ab/", re.IGNORECASE)

CONTACT_PROPS = [
    "firstname", "lastname",
    "hs_analytics_source",
    "hs_analytics_first_url",
    "hs_analytics_first_visit_timestamp",
    "ip_country_code", "ip_country",
    "self_reported_attribution",
    "createdate",
]

# ISO 3166-1 alpha-2 → alpha-3  (GSC uses 3-letter lowercase)
A2_TO_A3 = {
    "AF":"afg","AL":"alb","DZ":"dza","AD":"and","AO":"ago","AG":"atg","AR":"arg",
    "AM":"arm","AU":"aus","AT":"aut","AZ":"aze","BS":"bhs","BH":"bhr","BD":"bgd",
    "BB":"brb","BY":"blr","BE":"bel","BZ":"blz","BJ":"ben","BT":"btn","BO":"bol",
    "BA":"bih","BW":"bwa","BR":"bra","BN":"brn","BG":"bgr","BF":"bfa","BI":"bdi",
    "CV":"cpv","KH":"khm","CM":"cmr","CA":"can","CF":"caf","TD":"tcd","CL":"chl",
    "CN":"chn","CO":"col","KM":"com","CD":"cod","CG":"cog","CR":"cri","HR":"hrv",
    "CU":"cub","CY":"cyp","CZ":"cze","DK":"dnk","DJ":"dji","DM":"dma","DO":"dom",
    "EC":"ecu","EG":"egy","SV":"slv","GQ":"gnq","ER":"eri","EE":"est","SZ":"swz",
    "ET":"eth","FJ":"fji","FI":"fin","FR":"fra","GA":"gab","GM":"gmb","GE":"geo",
    "DE":"deu","GH":"gha","GR":"grc","GD":"grd","GT":"gtm","GN":"gin","GW":"gnb",
    "GY":"guy","HT":"hti","HN":"hnd","HU":"hun","IS":"isl","IN":"ind","ID":"idn",
    "IR":"irn","IQ":"irq","IE":"irl","IL":"isr","IT":"ita","JM":"jam","JP":"jpn",
    "JO":"jor","KZ":"kaz","KE":"ken","KI":"kir","KW":"kwt","KG":"kgz","LA":"lao",
    "LV":"lva","LB":"lbn","LS":"lso","LR":"lbr","LY":"lby","LI":"lie","LT":"ltu",
    "LU":"lux","MG":"mdg","MW":"mwi","MY":"mys","MV":"mdv","ML":"mli","MT":"mlt",
    "MH":"mhl","MR":"mrt","MU":"mus","MX":"mex","FM":"fsm","MD":"mda","MC":"mco",
    "MN":"mng","ME":"mne","MA":"mar","MZ":"moz","MM":"mmr","NA":"nam","NR":"nru",
    "NP":"npl","NL":"nld","NZ":"nzl","NI":"nic","NE":"ner","NG":"nga","NO":"nor",
    "OM":"omn","PK":"pak","PW":"plw","PA":"pan","PG":"png","PY":"pry","PE":"per",
    "PH":"phl","PL":"pol","PT":"prt","QA":"qat","RO":"rou","RU":"rus","RW":"rwa",
    "KN":"kna","LC":"lca","VC":"vct","WS":"wsm","SM":"smr","ST":"stp","SA":"sau",
    "SN":"sen","RS":"srb","SC":"syc","SL":"sle","SG":"sgp","SK":"svk","SI":"svn",
    "SB":"slb","SO":"som","ZA":"zaf","SS":"ssd","ES":"esp","LK":"lka","SD":"sdn",
    "SR":"sur","SE":"swe","CH":"che","SY":"syr","TW":"twn","TJ":"tjk","TZ":"tza",
    "TH":"tha","TL":"tls","TG":"tgo","TO":"ton","TT":"tto","TN":"tun","TR":"tur",
    "TM":"tkm","UG":"uga","UA":"ukr","AE":"are","GB":"gbr","US":"usa","UY":"ury",
    "UZ":"uzb","VU":"vut","VE":"ven","VN":"vnm","YE":"yem","ZM":"zmb","ZW":"zwe",
    "KR":"kor","KP":"prk","MK":"mkd","XK":"xkx","PS":"pse","HK":"hkg",
    "MO":"mac","PR":"pri","GU":"gum","VI":"vir",
}

CSV_FIELDS = [
    "contact_id", "name", "source", "country", "country_code",
    "first_page", "visit_date", "date_source", "create_date",
    "keyword", "clicks", "impressions", "position", "gsc_tier",
    "sra_category", "sra_raw",
]


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------
def normalise_url(raw: str) -> str | None:
    if not raw:
        return None
    p = urlparse(raw)
    netloc = p.netloc.lower().replace("www.", "")
    if netloc not in ("openloyalty.io",):
        return None
    path = p.path.rstrip("/") or "/"
    if AB_RE.match(path):
        path = "/"
    return urlunparse(("https", "www.openloyalty.io", path, "", "", ""))


# ---------------------------------------------------------------------------
# Self-reported attribution categoriser
# ---------------------------------------------------------------------------
def categorise_sra(val: str) -> str:
    if not val or val.strip() in ("-", ""):
        return "—"
    v = val.lower().strip()
    if any(x in v for x in ["chatgpt", "chat gpt", "chaptgpt", "chat-gpt"]):
        return "ChatGPT"
    if "claude" in v:
        return "Claude"
    if "gemini" in v:
        return "Gemini"
    if "copilot" in v or "co-pilot" in v:
        return "Copilot"
    if any(x in v for x in ["gpt", " ai ", "ai search", "ai ref", "artificial"]):
        return "AI (other)"
    if "perplexity" in v:
        return "Perplexity"
    if "ahrefs" in v:
        return "Ahrefs"
    if "bing" in v:
        return "Bing"
    if any(x in v for x in ["google", "googel", "gogle"]):
        return "Google"
    if any(x in v for x in ["linkedin", "linked in"]):
        return "LinkedIn"
    if any(x in v for x in ["referral", "recommend", "colleague", "word of mouth",
                              "partner", "team", "friend"]):
        return "Referral/Word-of-mouth"
    if any(x in v for x in ["blog", "article", "post", "content", "read"]):
        return "Blog/Content"
    if any(x in v for x in ["youtube", "video"]):
        return "YouTube/Video"
    if any(x in v for x in ["twitter", "x.com", "facebook", "instagram", "social"]):
        return "Social media"
    return "Other"


# ---------------------------------------------------------------------------
# HubSpot
# ---------------------------------------------------------------------------
def date_to_ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def fetch_mql_contacts(start: date, end: date) -> list:
    if not HUBSPOT_TOKEN:
        raise SystemExit("HUBSPOT_TOKEN environment variable not set")

    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"{HS_API}/crm/v3/objects/contacts/search"

    body = {
        "filterGroups": [
            {
                "filters": [
                    {"propertyName": "lifecyclestage",
                     "operator": "EQ", "value": "marketingqualifiedlead"},
                    {"propertyName": "createdate",
                     "operator": "GTE", "value": str(date_to_ms(start))},
                    {"propertyName": "createdate",
                     "operator": "LTE", "value": str(date_to_ms(end) + 86_399_999)},
                    {"propertyName": "hs_analytics_source",
                     "operator": "IN",
                     "values": ["ORGANIC_SEARCH", "DIRECT_TRAFFIC"]},
                ]
            }
        ],
        "properties": CONTACT_PROPS,
        "limit": 100,
    }

    contacts = []
    after = None
    while True:
        if after:
            body["after"] = after
        resp = requests.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        contacts.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

    return contacts


# ---------------------------------------------------------------------------
# GSC
# ---------------------------------------------------------------------------
def get_gsc_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    s = AuthorizedSession(creds)
    s.verify = False
    return s


def gsc_query(session, page: str, visit_date: date,
              country_a3: str | None) -> tuple[list, int]:
    """Return (rows, tier). tier: 0=exact+country, 1=±1day+country,
    2=exact no-country, 3=±1day no-country, -1=no data."""

    def _call(start: str, end: str, with_country: bool) -> list:
        filters = [{"dimension": "page", "operator": "equals", "expression": page}]
        if with_country and country_a3:
            filters.append({"dimension": "country", "operator": "equals",
                             "expression": country_a3})
        payload = {
            "startDate": start, "endDate": end,
            "dimensions": ["query"],
            "dimensionFilterGroups": [{"filters": filters}],
            "rowLimit": 25,
        }
        r = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
        r.raise_for_status()
        return r.json().get("rows", [])

    d = visit_date.isoformat()
    s = (visit_date - timedelta(days=1)).isoformat()
    e = (visit_date + timedelta(days=1)).isoformat()

    rows = _call(d, d, True)
    if rows:
        return rows, 0

    rows = _call(s, e, True)
    if rows:
        return rows, 1

    if country_a3:
        rows = _call(d, d, False)
        if rows:
            return rows, 2
        rows = _call(s, e, False)
        if rows:
            return rows, 3
    else:
        rows = _call(d, d, False)
        if rows:
            return rows, 2
        rows = _call(s, e, False)
        if rows:
            return rows, 3

    return [], -1


def top_kw(rows: list) -> dict | None:
    if not rows:
        return None
    rows.sort(key=lambda r: (-r["clicks"], -r["impressions"]))
    b = rows[0]
    return {"keyword": b["keys"][0], "clicks": int(b["clicks"]),
            "impressions": int(b["impressions"]), "position": round(b["position"], 1)}


# ---------------------------------------------------------------------------
# Console table helpers
# ---------------------------------------------------------------------------
MONTHS = [
    ("2026-01", "January 2026"),
    ("2026-02", "February 2026"),
    ("2026-03", "March 2026"),
    ("2026-04", "April 2026"),
    ("2026-05", "May 2026"),
]

W = {"name": 28, "src": 8, "country": 14, "page": 42, "date": 11,
     "kw": 38, "sra": 22, "cl": 6, "im": 7, "pos": 5}


def hdr():
    return (f"{'Contact':<{W['name']}}  {'Src':<{W['src']}}  "
            f"{'Country':<{W['country']}}  {'First Page':<{W['page']}}  "
            f"{'Date':<{W['date']}}  {'T':1}  {'Top Keyword':<{W['kw']}}  "
            f"{'Self-Reported':<{W['sra']}}  "
            f"{'Clicks':>{W['cl']}}  {'Impr':>{W['im']}}  {'Pos':>{W['pos']}}")


def fmt_row(r: dict) -> str:
    page = r["first_page"].replace("https://www.openloyalty.io", "")[:W["page"]]
    kw   = (r["keyword"] or "—")[:W["kw"]]
    sra  = r["sra_category"][:W["sra"]]
    cl   = str(r["clicks"]) if isinstance(r["clicks"], int) else "—"
    im   = str(r["impressions"]) if isinstance(r["impressions"], int) else "—"
    pos  = str(r["position"]) if isinstance(r["position"], float) else "—"
    tier = str(r["gsc_tier"]) if isinstance(r["gsc_tier"], int) else "—"
    return (f"{r['name']:<{W['name']}}  {r['source']:<{W['src']}}  "
            f"{r['country']:<{W['country']}}  {page:<{W['page']}}  "
            f"{r['visit_date']:<{W['date']}}  {tier:1}  {kw:<{W['kw']}}  "
            f"{sra:<{W['sra']}}  "
            f"{cl:>{W['cl']}}  {im:>{W['im']}}  {pos:>{W['pos']}}")


def print_table(rows: list, title: str):
    print(f"\n{'='*155}")
    print(f"  {title}  ({len(rows)} MQLs)")
    print(f"{'='*155}")
    h = hdr()
    print(h)
    print("-" * len(h))
    for r in rows:
        print(fmt_row(r))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="MQL keyword report")
    parser.add_argument("--start",  default="2026-05-01",
                        help="Start date YYYY-MM-DD (createdate filter)")
    parser.add_argument("--end",    default="2026-05-31",
                        help="End date YYYY-MM-DD (createdate filter, inclusive)")
    parser.add_argument("--output", default="",
                        help="CSV output path (default: mql_keywords_<start>_<end>.csv)")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start)
    end_date   = date.fromisoformat(args.end)
    csv_path   = args.output or f"mql_keywords_{args.start}_{args.end}.csv"

    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    print(f"Fetching MQL contacts {args.start} → {args.end} from HubSpot...")
    contacts = fetch_mql_contacts(start_date, end_date)
    print(f"Found {len(contacts)} MQL contacts.\n")

    gsc_session = get_gsc_session()

    by_month  = defaultdict(list)
    sra_cats  = Counter()
    all_rows  = []

    for i, c in enumerate(contacts, 1):
        p    = c.get("properties", {})
        cid  = c.get("id", "")
        name = ((p.get("firstname") or "") + " " + (p.get("lastname") or "")).strip() or cid

        source      = "ORGANIC" if p.get("hs_analytics_source") == "ORGANIC_SEARCH" else "DIRECT"
        raw_url     = p.get("hs_analytics_first_url") or ""
        country_a2  = (p.get("ip_country_code") or "").upper()
        country_name = (p.get("ip_country") or country_a2 or "—").title()[:W["country"]]
        country_a3  = A2_TO_A3.get(country_a2) or None
        sra_raw     = p.get("self_reported_attribution") or ""
        sra_cat     = categorise_sra(sra_raw)
        sra_cats[sra_cat] += 1

        create_date_str = (p.get("createdate") or "")[:10]
        month_key = create_date_str[:7]

        # Prefer first_visit_timestamp for accurate GSC date matching
        first_visit_ts = p.get("hs_analytics_first_visit_timestamp")
        if first_visit_ts:
            try:
                visit_date  = datetime.fromtimestamp(int(first_visit_ts) / 1000,
                                                     tz=timezone.utc).date()
                date_source = "first_visit"
            except (ValueError, OSError):
                visit_date  = date.fromisoformat(create_date_str) if create_date_str else None
                date_source = "createdate"
        elif create_date_str:
            visit_date  = date.fromisoformat(create_date_str)
            date_source = "createdate"
        else:
            visit_date  = None
            date_source = "none"

        norm_url = normalise_url(raw_url)

        row = {
            "contact_id":   cid,
            "name":         name[:W["name"]],
            "source":       source,
            "country":      country_name,
            "country_code": country_a2,
            "first_page":   norm_url or raw_url[:W["page"]] or "—",
            "visit_date":   visit_date.isoformat() if visit_date else "—",
            "date_source":  date_source,
            "create_date":  create_date_str,
            "keyword":      "—",
            "clicks":       "—",
            "impressions":  "—",
            "position":     "—",
            "gsc_tier":     "—",
            "sra_category": sra_cat,
            "sra_raw":      sra_raw,
        }

        if norm_url and visit_date:
            gsc_rows, tier = gsc_query(gsc_session, norm_url, visit_date, country_a3)
            best = top_kw(gsc_rows)
            if best:
                row.update({
                    "keyword":     best["keyword"],
                    "clicks":      best["clicks"],
                    "impressions": best["impressions"],
                    "position":    best["position"],
                    "gsc_tier":    tier,
                })
            else:
                row["keyword"]  = "no GSC data"
                row["gsc_tier"] = tier
        elif not norm_url:
            row["keyword"] = "no URL"
        else:
            row["keyword"] = "no date"

        print(f"  [{i:3d}/{len(contacts)}] {name[:28]:<28} {country_a2:<3} "
              f"t={row['gsc_tier']}  {row['keyword'][:40]}", flush=True)

        all_rows.append(row)
        by_month[month_key].append(row)

    # --- Console monthly tables ---
    seen_months = sorted({r["create_date"][:7] for r in all_rows if r["create_date"]})
    month_labels = dict(MONTHS)
    for mk in seen_months:
        title = month_labels.get(mk, mk)
        print_table(by_month.get(mk, []), title)

    # --- Self-reported attribution breakdown ---
    print(f"\n{'='*60}")
    print("  Self-Reported Attribution Breakdown")
    print(f"{'='*60}")
    print(f"{'Category':<30}  {'Count':>6}  {'%':>5}")
    print("-" * 45)
    total = sum(sra_cats.values())
    for cat, cnt in sra_cats.most_common():
        print(f"{cat:<30}  {cnt:>6}  {cnt/total*100:>4.1f}%")
    print(f"{'TOTAL':<30}  {total:>6}")

    # --- CSV output ---
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nCSV written → {csv_path}  ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
