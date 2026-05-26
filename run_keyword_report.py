#!/usr/bin/env python3
"""
Keyword report: for each SEO-tagged deal (Jan 1 – May 22 2026),
find the best associated contact's first page, then query GSC for
the top keyword on that page around the contact's create date.
Results grouped by deal month.
"""

import json
import warnings
from datetime import date, timedelta, datetime
from urllib.parse import urlparse, urlunparse

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

warnings.filterwarnings("ignore")

TOKEN_FILE = "/home/user/gsc-sync/token.json"
SITE = "sc-domain:openloyalty.io"
GSC_API = "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query".format(
    site=SITE
)

MONTH_LABELS = {
    1: "January 2026",
    2: "February 2026",
    3: "March 2026",
    4: "April 2026",
    5: "May 2026 (1-22)",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def normalise_url(raw_url: str) -> str | None:
    """
    - Strip query params / fragments
    - Map /ab/* paths -> homepage
    - Ensure https://www.openloyalty.io/ prefix
    Returns None if the URL is empty/None.
    """
    if not raw_url:
        return None
    url = raw_url.strip()
    parsed = urlparse(url)

    # drop query + fragment
    path = parsed.path or "/"

    # /ab/* or /#  -> homepage path
    if path.startswith("/ab/") or path == "/#" or path == "#":
        path = "/"

    # enforce www
    host = parsed.netloc.lower()
    if host in ("openloyalty.io", "www.openloyalty.io"):
        host = "www.openloyalty.io"
    elif host == "":
        host = "www.openloyalty.io"

    # ensure trailing slash on root only
    if path == "":
        path = "/"

    clean = urlunparse(("https", host, path, "", "", ""))
    return clean


def parse_date(dt_str: str) -> date | None:
    """Parse ISO datetime or date string to date object."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return date.fromisoformat(dt_str[:10])
        except Exception:
            return None


def query_gsc(session, page_url: str, query_date: date) -> list:
    """Query GSC for a single day; fallback to ±1 day window."""
    single_date = query_date.isoformat()
    payload = {
        "startDate": single_date,
        "endDate": single_date,
        "dimensions": ["query"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension": "page",
                "operator": "equals",
                "expression": page_url,
            }]
        }],
        "rowLimit": 25,
    }
    try:
        resp = session.post(GSC_API, json=payload)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
    except Exception:
        rows = []

    if rows:
        return rows, single_date

    # fallback: ±1 day
    start = (query_date - timedelta(days=1)).isoformat()
    end = (query_date + timedelta(days=1)).isoformat()
    payload["startDate"] = start
    payload["endDate"] = end
    try:
        resp = session.post(GSC_API, json=payload)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
    except Exception:
        rows = []

    window = f"{start}..{end}"
    return rows, window


def top_keyword(rows: list) -> dict | None:
    if not rows:
        return None
    return sorted(rows, key=lambda r: (-r["clicks"], -r["impressions"]))[0]


# ---------------------------------------------------------------------------
# load data
# ---------------------------------------------------------------------------

def load_deals():
    with open("/home/user/gsc-sync/deals_2026.json") as f:
        return json.load(f)


def load_all_contacts():
    contacts = []
    for i in (1, 2, 3):
        path = f"/home/user/gsc-sync/contacts_batch{i}.json"
        with open(path) as f:
            contacts.extend(json.load(f))
    # deduplicate by id
    seen = set()
    unique = []
    for c in contacts:
        cid = c["id"]
        if cid not in seen:
            seen.add(cid)
            unique.append(c)
    return unique


# ---------------------------------------------------------------------------
# main logic
# ---------------------------------------------------------------------------

def main():
    deals = load_deals()
    all_contacts = load_all_contacts()

    # Pre-filter contacts that have a usable first URL
    contacts_with_url = []
    for c in all_contacts:
        raw = c["properties"].get("hs_analytics_first_url")
        norm = normalise_url(raw)
        if norm:
            cdate = parse_date(c["properties"].get("createdate"))
            if cdate:
                contacts_with_url.append({
                    "id": c["id"],
                    "url": norm,
                    "createdate": cdate,
                    "name": c["properties"].get("hs_full_name_or_email", ""),
                })

    # Sort contacts by createdate descending for faster lookup
    contacts_with_url.sort(key=lambda x: x["createdate"], reverse=True)

    session = get_session()

    # Group results by month
    monthly_rows = {m: [] for m in range(1, 6)}

    total = len(deals)
    for idx, deal in enumerate(deals, 1):
        deal_date = parse_date(deal["createdate"])
        if not deal_date:
            continue
        if deal_date.year != 2026:
            continue
        month = deal_date.month
        if month > 5:
            continue

        print(f"[{idx}/{total}] {deal['dealname']!r} ({deal_date})", flush=True)

        # Pick best contact: has URL, createdate <= deal_date, closest
        best = None
        best_delta = None
        for c in contacts_with_url:
            if c["createdate"] > deal_date:
                continue
            delta = (deal_date - c["createdate"]).days
            if best is None or delta < best_delta:
                best = c
                best_delta = delta

        if best is None:
            monthly_rows[month].append({
                "deal": deal["dealname"],
                "first_page": "no URL",
                "gsc_date": "-",
                "keyword": "-",
                "clicks": "-",
                "impressions": "-",
                "position": "-",
            })
            continue

        page_url = best["url"]
        contact_date = best["createdate"]

        rows, used_date = query_gsc(session, page_url, contact_date)
        kw_row = top_keyword(rows)

        if kw_row:
            monthly_rows[month].append({
                "deal": deal["dealname"],
                "first_page": page_url,
                "gsc_date": used_date,
                "keyword": kw_row["keys"][0],
                "clicks": int(kw_row["clicks"]),
                "impressions": int(kw_row["impressions"]),
                "position": round(kw_row["position"], 1),
            })
        else:
            monthly_rows[month].append({
                "deal": deal["dealname"],
                "first_page": page_url,
                "gsc_date": str(contact_date),
                "keyword": "(no GSC data)",
                "clicks": 0,
                "impressions": 0,
                "position": "-",
            })

    # ---------------------------------------------------------------------------
    # Print tables
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 130)
    for month in range(1, 6):
        label = MONTH_LABELS[month]
        rows_m = monthly_rows[month]
        print(f"\n{'=' * 130}")
        print(f"  {label}  ({len(rows_m)} deals)")
        print(f"{'=' * 130}")

        COL_DEAL = 30
        COL_PAGE = 55
        COL_DATE = 14
        COL_KW = 45
        COL_CLICKS = 7
        COL_IMPR = 8
        COL_POS = 6

        header = (
            f"{'Deal':<{COL_DEAL}}  "
            f"{'First Page':<{COL_PAGE}}  "
            f"{'GSC Date':<{COL_DATE}}  "
            f"{'Top Keyword':<{COL_KW}}  "
            f"{'Clicks':>{COL_CLICKS}}  "
            f"{'Impr':>{COL_IMPR}}  "
            f"{'Pos':>{COL_POS}}"
        )
        print(header)
        print("-" * 130)

        for r in rows_m:
            deal_s = str(r["deal"])[:COL_DEAL]
            page_s = str(r["first_page"])[:COL_PAGE]
            date_s = str(r["gsc_date"])[:COL_DATE]
            kw_s = str(r["keyword"])[:COL_KW]
            clicks_s = str(r["clicks"])
            impr_s = str(r["impressions"])
            pos_s = str(r["position"])

            print(
                f"{deal_s:<{COL_DEAL}}  "
                f"{page_s:<{COL_PAGE}}  "
                f"{date_s:<{COL_DATE}}  "
                f"{kw_s:<{COL_KW}}  "
                f"{clicks_s:>{COL_CLICKS}}  "
                f"{impr_s:>{COL_IMPR}}  "
                f"{pos_s:>{COL_POS}}"
            )

    print(f"\n{'=' * 130}")
    print("Done.")


if __name__ == "__main__":
    main()
