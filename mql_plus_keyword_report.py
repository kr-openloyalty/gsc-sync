#!/usr/bin/env python3
"""
MQL+ contact keyword report (Jun 2025 – Jun 2026)

Reads contacts from hs_contacts_all.json (MQL, SQL, Opportunity, Customer),
queries GSC for the best keyword on the contact's first visit date,
and writes two CSVs:
  - mql_plus_keywords_2025_2026.csv  — one row per contact
  - top_keywords_pages_2025_2026.csv — aggregated keyword / page analysis

Usage:
  python3 mql_plus_keyword_report.py
"""

import csv
import json
import re
import time
import warnings
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

# ── config ────────────────────────────────────────────────────────────────────
TOKEN_FILE     = "token.json"
CONTACTS_FILE  = "/tmp/claude-0/-home-user-gsc-sync/f50a975a-1f60-5601-8971-46eb9d92c41e/scratchpad/hs_contacts_all.json"
OUTPUT_CSV     = "mql_plus_keywords_2025_2026.csv"
KEYWORDS_CSV   = "top_keywords_pages_2025_2026.csv"
SITE           = "sc-domain:openloyalty.io"
GSC_API        = "https://www.googleapis.com/webmasters/v3"
DATE_START     = date(2025, 6, 1)
DATE_END       = date(2026, 6, 19)

AB_RE = re.compile(r"^/ab/", re.IGNORECASE)

# ISO 3166-1 alpha-2 → alpha-3
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
    "MO":"mac","PR":"pri","GU":"gum","VI":"vir","CI":"civ","SX":"sxm","CW":"cuw",
    "BW":"bwa","TZ":"tza","DO":"dom","HN":"hnd","KI":"kir","MX":"mex","BO":"bol",
}

CSV_FIELDS = [
    "contact_id","name","lifecycle_stage","source","country","country_code",
    "first_page","visit_date","date_source","create_date",
    "keyword","clicks","impressions","position","gsc_tier",
    "sra_category","sra_raw",
]


def normalise_url(raw):
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


def categorise_sra(val):
    if not val or val.strip() in ("-", ""):
        return "—"
    v = val.lower().strip()
    if any(x in v for x in ["chatgpt","chat gpt","chaptgpt","chat-gpt"]):
        return "ChatGPT"
    if "claude" in v:
        return "Claude"
    if "gemini" in v:
        return "Gemini"
    if "copilot" in v or "co-pilot" in v:
        return "Copilot"
    if "perplexity" in v:
        return "Perplexity"
    if "grok" in v:
        return "Grok"
    if "ahrefs" in v:
        return "Ahrefs"
    if any(x in v for x in ["gpt"," ai ","ai search","ai ref","artificial"]):
        return "AI (other)"
    if "bing" in v:
        return "Bing"
    if any(x in v for x in ["google","googel","gogle"]):
        return "Google"
    if any(x in v for x in ["linkedin","linked in"]):
        return "LinkedIn"
    if any(x in v for x in ["reddit"]):
        return "Reddit"
    if any(x in v for x in ["youtube","video"]):
        return "YouTube/Video"
    if any(x in v for x in ["referral","recommend","colleague","word of mouth","partner","team","friend","referred"]):
        return "Referral/Word-of-mouth"
    if any(x in v for x in ["blog","article","post","content","read"]):
        return "Blog/Content"
    if any(x in v for x in ["twitter","x.com","facebook","instagram","social"]):
        return "Social media"
    return "Other"


# ── GSC session ───────────────────────────────────────────────────────────────
with open(TOKEN_FILE) as f:
    t = json.load(f)

creds = Credentials(
    token=t["token"],
    refresh_token=t["refresh_token"],
    token_uri=t["token_uri"],
    client_id=t["client_id"],
    client_secret=t["client_secret"],
)
session = AuthorizedSession(creds)


def gsc_query(page_url, visit_dt, country_a2):
    """Return (keyword, clicks, impressions, position, tier) for a page+date+country."""
    visit_d = visit_dt.date() if isinstance(visit_dt, datetime) else visit_dt
    country_a3 = A2_TO_A3.get((country_a2 or "").upper(), "")

    def _call(start, end, use_country=True):
        dims = ["query"]
        filters = [{"dimension": "page", "operator": "equals", "expression": page_url}]
        if use_country and country_a3:
            filters.append({"dimension": "country", "operator": "equals", "expression": country_a3})
        payload = {
            "startDate": str(start),
            "endDate": str(end),
            "dimensions": dims,
            "dimensionFilterGroups": [{"filters": filters}],
            "rowLimit": 1,
            "orderBy": [{"fieldName": "clicks", "sortOrder": "DESCENDING"}],
        }
        r = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
        r.raise_for_status()
        rows = r.json().get("rows", [])
        return rows[0] if rows else None

    # Tier 0: exact date + country
    row = _call(visit_d, visit_d, use_country=True)
    if row:
        return row["keys"][0], int(row["clicks"]), int(row["impressions"]), round(row["position"], 1), 0

    # Tier 1: ±1 day + country
    row = _call(visit_d - timedelta(days=1), visit_d + timedelta(days=1), use_country=True)
    if row:
        return row["keys"][0], int(row["clicks"]), int(row["impressions"]), round(row["position"], 1), 1

    # Tier 2: 7-day window + country
    row = _call(visit_d - timedelta(days=3), visit_d + timedelta(days=3), use_country=True)
    if row:
        return row["keys"][0], int(row["clicks"]), int(row["impressions"]), round(row["position"], 1), 2

    # Tier 3: 30-day window, no country
    row = _call(visit_d - timedelta(days=14), visit_d + timedelta(days=14), use_country=False)
    if row:
        return row["keys"][0], int(row["clicks"]), int(row["impressions"]), round(row["position"], 1), 3

    return "no GSC data", "—", "—", "—", -1


# ── Load and deduplicate contacts ─────────────────────────────────────────────
with open(CONTACTS_FILE) as f:
    raw_contacts = json.load(f)

seen_ids = set()
contacts = []
for c in raw_contacts:
    p = c.get("properties", {})
    cid = str(p.get("hs_object_id", c.get("id", "")))
    if cid in seen_ids:
        continue
    seen_ids.add(cid)
    contacts.append(c)

print(f"Loaded {len(contacts)} unique contacts")

# Filter: only those with openloyalty.io first URL and within date window
valid = []
for c in contacts:
    p = c.get("properties", {})
    raw_url = p.get("hs_analytics_first_url", "")
    norm = normalise_url(raw_url)
    if not norm:
        continue

    # Determine visit date
    ts = p.get("hs_analytics_first_visit_timestamp") or p.get("createdate") or ""
    try:
        visit_dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
        if visit_dt:
            visit_dt = visit_dt.astimezone(timezone.utc)
            vd = visit_dt.date()
        else:
            vd = None
    except Exception:
        vd = None

    cdate_str = (p.get("createdate") or "")[:10]
    try:
        cdate = date.fromisoformat(cdate_str) if cdate_str else None
    except Exception:
        cdate = None

    # Use visit date for range check; fallback to createdate
    check_date = vd or cdate
    if check_date and (check_date < DATE_START or check_date > DATE_END):
        continue

    valid.append((c, norm, visit_dt, vd, cdate))

print(f"Contacts with valid OL URL in date range: {len(valid)}")

from collections import Counter
stage_counts = Counter(c[0].get("properties", {}).get("lifecyclestage", "?") for c in valid)
print("By stage:", dict(stage_counts))


# ── GSC enrichment ────────────────────────────────────────────────────────────
rows_out = []
gsc_cache = {}  # (page, date_str, country) -> result

for idx, (c, norm_url, visit_dt, vd, cdate) in enumerate(valid):
    p = c.get("properties", {})
    cid = str(p.get("hs_object_id", ""))
    name = p.get("hs_full_name_or_email", "").strip()
    stage = p.get("lifecyclestage", "")
    source = p.get("hs_analytics_source", "")
    country = (p.get("ip_country") or "").title()
    country_code = (p.get("ip_country_code") or "").upper()
    sra_raw = (p.get("self_reported_attribution") or "").strip()
    sra_cat = categorise_sra(sra_raw)
    create_date = (p.get("createdate") or "")[:10]

    # Determine visit date and date_source
    if vd:
        visit_date = str(vd)
        date_source = "first_visit_timestamp"
    elif cdate:
        visit_date = str(cdate)
        date_source = "createdate"
        vd = cdate
    else:
        visit_date = ""
        date_source = "unknown"

    # Skip if no visit date
    if not vd:
        rows_out.append({
            "contact_id": cid, "name": name, "lifecycle_stage": stage,
            "source": source, "country": country, "country_code": country_code,
            "first_page": norm_url, "visit_date": visit_date,
            "date_source": date_source, "create_date": create_date,
            "keyword": "no date", "clicks": "—", "impressions": "—",
            "position": "—", "gsc_tier": -1,
            "sra_category": sra_cat, "sra_raw": sra_raw[:200],
        })
        continue

    # Only query GSC for Organic/Direct sources (others unlikely to have GSC data)
    cache_key = (norm_url, str(vd), country_code)
    if cache_key in gsc_cache:
        kw, clicks, impressions, position, tier = gsc_cache[cache_key]
    elif source in ("ORGANIC_SEARCH", "DIRECT_TRAFFIC", ""):
        try:
            kw, clicks, impressions, position, tier = gsc_query(norm_url, vd, country_code)
            gsc_cache[cache_key] = (kw, clicks, impressions, position, tier)
        except Exception as e:
            kw, clicks, impressions, position, tier = f"error:{e}", "—", "—", "—", -1
    else:
        kw, clicks, impressions, position, tier = "no GSC data", "—", "—", "—", -1

    rows_out.append({
        "contact_id": cid, "name": name, "lifecycle_stage": stage,
        "source": source, "country": country, "country_code": country_code,
        "first_page": norm_url, "visit_date": visit_date,
        "date_source": date_source, "create_date": create_date,
        "keyword": kw, "clicks": clicks, "impressions": impressions,
        "position": position, "gsc_tier": tier,
        "sra_category": sra_cat, "sra_raw": sra_raw[:200],
    })

    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx + 1}/{len(valid)} contacts…")

print(f"\nDone. Writing {len(rows_out)} rows to {OUTPUT_CSV}")

# ── Write main CSV ────────────────────────────────────────────────────────────
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    w.writeheader()
    w.writerows(rows_out)

print(f"Wrote {OUTPUT_CSV}")


# ── Keyword + Page analysis CSV ───────────────────────────────────────────────
# Aggregate: keyword -> count by stage, total, top pages
kw_stats = defaultdict(lambda: {
    "total": 0, "mql": 0, "sql": 0, "opp": 0, "customer": 0,
    "pages": Counter(), "countries": Counter(),
})
page_stats = defaultdict(lambda: {
    "total": 0, "mql": 0, "sql": 0, "opp": 0, "customer": 0,
    "keywords": Counter(),
})

STAGE_MAP = {
    "marketingqualifiedlead": "mql",
    "salesqualifiedlead": "sql",
    "opportunity": "opp",
    "customer": "customer",
}

for row in rows_out:
    kw   = row["keyword"]
    page = row["first_page"]
    stage_key = STAGE_MAP.get(row["lifecycle_stage"], "mql")
    country = row["country"]

    # Skip non-keyword entries
    if kw in ("no GSC data", "no date", "") or kw.startswith("error:"):
        kw = "(no keyword)"

    kw_stats[kw]["total"] += 1
    kw_stats[kw][stage_key] += 1
    kw_stats[kw]["pages"][page] += 1
    kw_stats[kw]["countries"][country] += 1

    page_stats[page]["total"] += 1
    page_stats[page][stage_key] += 1
    page_stats[page]["keywords"][kw] += 1

# Top keywords CSV
KW_FIELDS = [
    "keyword", "total_contacts", "mqls", "sqls", "opps", "customers",
    "top_page_1", "top_page_1_count",
    "top_page_2", "top_page_2_count",
    "top_countries",
]

sorted_kws = sorted(kw_stats.items(), key=lambda x: -x[1]["total"])
kw_rows = []
for kw, s in sorted_kws:
    if kw == "(no keyword)":
        continue
    top_pages = s["pages"].most_common(2)
    tp1 = top_pages[0][0] if len(top_pages) > 0 else ""
    tp1c = top_pages[0][1] if len(top_pages) > 0 else 0
    tp2 = top_pages[1][0] if len(top_pages) > 1 else ""
    tp2c = top_pages[1][1] if len(top_pages) > 1 else 0
    top_countries = ", ".join(f"{c}({n})" for c, n in s["countries"].most_common(3))
    kw_rows.append({
        "keyword": kw, "total_contacts": s["total"],
        "mqls": s["mql"], "sqls": s["sql"], "opps": s["opp"], "customers": s["customer"],
        "top_page_1": tp1, "top_page_1_count": tp1c,
        "top_page_2": tp2, "top_page_2_count": tp2c,
        "top_countries": top_countries,
    })

# Top pages CSV
PAGE_FIELDS = [
    "first_page", "total_contacts", "mqls", "sqls", "opps", "customers",
    "top_keyword_1", "top_keyword_1_count",
    "top_keyword_2", "top_keyword_2_count",
    "top_keyword_3", "top_keyword_3_count",
]

sorted_pages = sorted(page_stats.items(), key=lambda x: -x[1]["total"])

# Combined into one CSV with sections — write keyword CSV and page CSV separately
with open(KEYWORDS_CSV, "w", newline="", encoding="utf-8") as f:
    f.write("# SECTION 1: TOP KEYWORDS (by total MQL+ contacts)\n")
    w = csv.DictWriter(f, fieldnames=KW_FIELDS)
    w.writeheader()
    w.writerows(kw_rows[:100])

    f.write("\n\n# SECTION 2: TOP FIRST-SEEN PAGES (by total MQL+ contacts)\n")
    w2 = csv.DictWriter(f, fieldnames=PAGE_FIELDS)
    w2.writeheader()
    for page, s in sorted_pages:
        top_kws = [(k, n) for k, n in s["keywords"].most_common(3) if k != "(no keyword)"]
        while len(top_kws) < 3:
            top_kws.append(("", 0))
        w2.writerow({
            "first_page": page,
            "total_contacts": s["total"],
            "mqls": s["mql"], "sqls": s["sql"], "opps": s["opp"], "customers": s["customer"],
            "top_keyword_1": top_kws[0][0], "top_keyword_1_count": top_kws[0][1],
            "top_keyword_2": top_kws[1][0], "top_keyword_2_count": top_kws[1][1],
            "top_keyword_3": top_kws[2][0], "top_keyword_3_count": top_kws[2][1],
        })

print(f"Wrote {KEYWORDS_CSV}")
print(f"\nTop 10 pages by MQL+ contacts:")
for page, s in sorted_pages[:10]:
    print(f"  {s['total']:3d} total ({s['mql']} MQL / {s['sql']} SQL / {s['opp']} Opp / {s['customer']} Cust)  {page}")

print(f"\nTop 20 keywords by MQL+ contacts:")
for kw, s in sorted_kws[:20]:
    if kw == "(no keyword)": continue
    print(f"  {s['total']:3d}  {kw}")
