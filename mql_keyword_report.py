#!/usr/bin/env python3
"""
MQL contact keyword report — 2026 (Jan–May 22)

Source: HubSpot MQL contacts (lifecyclestage=marketingqualifiedlead)
        with hs_analytics_source IN [ORGANIC_SEARCH, DIRECT_TRAFFIC]
        created 2026-01-01 → 2026-05-22, hs_analytics_first_url set

For each contact:
  - Normalise first page URL (strip UTM, /ab/* → homepage)
  - Query GSC with page + date + ip_country filter
  - Fallback: widen to ±1 day; then drop country filter if still empty
  - Collect top keyword (most clicks; if 0, most impressions)
  - Also show self_reported_attribution

Outputs:
  1. 5 monthly tables (Jan–May)
  2. Self-reported attribution breakdown
"""

import json
import re
import warnings
from collections import Counter, defaultdict
from datetime import date, timedelta
from urllib.parse import urlparse, urlunparse

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TOKEN_FILE = "token.json"
SITE       = "sc-domain:openloyalty.io"
GSC_API    = "https://www.googleapis.com/webmasters/v3"

AB_RE = re.compile(r"^/ab/", re.IGNORECASE)

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
    "KR":"kor","KP":"prk","TZ":"tza","MK":"mkd","XK":"xkx","PS":"pse","HK":"hkg",
    "MO":"mac","TW":"twn","PR":"pri","GU":"gum","VI":"vir",
}


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
                              "partner", "team", "friend", "colleague"]):
        return "Referral/Word-of-mouth"
    if any(x in v for x in ["blog", "article", "post", "content", "read"]):
        return "Blog/Content"
    if any(x in v for x in ["youtube", "video"]):
        return "YouTube/Video"
    if any(x in v for x in ["twitter", "x.com", "facebook", "instagram", "social"]):
        return "Social media"
    return "Other"


# ---------------------------------------------------------------------------
# GSC
# ---------------------------------------------------------------------------
def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    s = AuthorizedSession(creds)
    s.verify = False
    return s


def gsc_query(session, page: str, visit_date: date,
              country_a3: str | None) -> list:
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
        r = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query",
                         json=payload)
        r.raise_for_status()
        return r.json().get("rows", [])

    d = visit_date.isoformat()
    rows = _call(d, d, True)
    if not rows:
        s = (visit_date - timedelta(days=1)).isoformat()
        e = (visit_date + timedelta(days=1)).isoformat()
        rows = _call(s, e, True)
    if not rows and country_a3:
        # Fallback: drop country filter
        rows = _call(d, d, False)
        if not rows:
            s = (visit_date - timedelta(days=1)).isoformat()
            e = (visit_date + timedelta(days=1)).isoformat()
            rows = _call(s, e, False)
    return rows


def top_kw(rows: list) -> dict | None:
    if not rows:
        return None
    rows.sort(key=lambda r: (-r["clicks"], -r["impressions"]))
    b = rows[0]
    return {"keyword": b["keys"][0], "clicks": int(b["clicks"]),
            "impressions": int(b["impressions"]), "position": round(b["position"], 1)}


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
MONTHS = [
    ("2026-01", "January 2026"),
    ("2026-02", "February 2026"),
    ("2026-03", "March 2026"),
    ("2026-04", "April 2026"),
    ("2026-05", "May 2026 (1–22)"),
]

W = {"name": 28, "src": 8, "country": 14, "page": 42, "date": 11,
     "kw": 38, "sra": 22, "cl": 6, "im": 7, "pos": 5}


def hdr():
    return (f"{'Contact':<{W['name']}}  {'Src':<{W['src']}}  "
            f"{'Country':<{W['country']}}  {'First Page':<{W['page']}}  "
            f"{'Date':<{W['date']}}  {'Top Keyword':<{W['kw']}}  "
            f"{'Self-Reported':<{W['sra']}}  "
            f"{'Clicks':>{W['cl']}}  {'Impr':>{W['im']}}  {'Pos':>{W['pos']}}")


def fmt_row(r: dict) -> str:
    page = r["page"].replace("https://www.openloyalty.io", "")[:W["page"]]
    kw   = (r["keyword"] or "—")[:W["kw"]]
    sra  = r["sra_cat"][:W["sra"]]
    cl   = str(r["clicks"]) if isinstance(r["clicks"], int) else "—"
    im   = str(r["impressions"]) if isinstance(r["impressions"], int) else "—"
    pos  = str(r["position"]) if isinstance(r["position"], float) else "—"
    return (f"{r['name']:<{W['name']}}  {r['source']:<{W['src']}}  "
            f"{r['country']:<{W['country']}}  {page:<{W['page']}}  "
            f"{r['date']:<{W['date']}}  {kw:<{W['kw']}}  "
            f"{sra:<{W['sra']}}  "
            f"{cl:>{W['cl']}}  {im:>{W['im']}}  {pos:>{W['pos']}}")


def print_table(rows: list, title: str):
    print(f"\n{'='*140}")
    print(f"  {title}  ({len(rows)} MQLs)")
    print(f"{'='*140}")
    h = hdr()
    print(h)
    print("-" * len(h))
    for r in rows:
        print(fmt_row(r))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    with open("mql_contacts.json") as f:
        contacts = json.load(f)

    print(f"Processing {len(contacts)} MQL contacts...\n")

    by_month = defaultdict(list)
    sra_cats = Counter()

    for i, c in enumerate(contacts, 1):
        p = c["properties"]
        name    = (p.get("firstname") or "") + " " + (p.get("lastname") or "")
        name    = name.strip() or c.get("displayName", str(c["id"]))
        source  = "ORGANIC" if p.get("hs_analytics_source") == "ORGANIC_SEARCH" else "DIRECT"
        raw_url = p.get("hs_analytics_first_url", "")
        country_a2  = (p.get("ip_country_code") or "").upper()
        country_name = (p.get("ip_country") or country_a2 or "—").title()[:W["country"]]
        country_a3  = A2_TO_A3.get(country_a2, "").lower() or None
        sra_raw = p.get("self_reported_attribution") or ""
        sra_cat = categorise_sra(sra_raw)
        sra_cats[sra_cat] += 1

        cdate_str = p.get("createdate", "")[:10]
        month_key = cdate_str[:7]

        norm_url = normalise_url(raw_url)
        row = {
            "name": name[:W["name"]], "source": source,
            "country": country_name, "page": norm_url or raw_url[:W["page"]] or "—",
            "date": cdate_str, "keyword": "—",
            "clicks": "—", "impressions": "—", "position": "—",
            "sra_raw": sra_raw, "sra_cat": sra_cat,
        }

        if norm_url and cdate_str:
            visit_date = date.fromisoformat(cdate_str)
            rows = gsc_query(session, norm_url, visit_date, country_a3)
            best = top_kw(rows)
            if best:
                row.update({"keyword": best["keyword"], "clicks": best["clicks"],
                             "impressions": best["impressions"], "position": best["position"]})
            else:
                row["keyword"] = "no GSC data"
        else:
            row["keyword"] = "no URL"

        print(f"  [{i:3d}/{len(contacts)}] {name[:28]:<28} {country_a2:<3} "
              f"{row['keyword'][:40]}", flush=True)
        by_month[month_key].append(row)

    # --- Monthly tables ---
    for mk, title in MONTHS:
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

    # --- Notable raw attributions ---
    print(f"\n{'='*60}")
    print("  Notable / Unusual Self-Reported Values")
    print(f"{'='*60}")
    shown = set()
    for c in contacts:
        val = (c["properties"].get("self_reported_attribution") or "").strip()
        cat = categorise_sra(val)
        if cat == "Other" and val and val.lower() not in ("-","") and val not in shown:
            if len(val) > 20:   # only show meaningful ones
                print(f"  [{cat}] {val[:120]}")
                shown.add(val)


if __name__ == "__main__":
    main()
