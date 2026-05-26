#!/usr/bin/env python3
"""
SEO deal keyword report — 2026 (Jan–May 22)

For each SEO-tagged deal, finds the associated contact's first page seen,
queries GSC for the top keyword on the contact's create date, then prints
5 monthly tables.

Requirements:
  HUBSPOT_TOKEN env var — HubSpot Private App token
  token.json           — GSC OAuth token (run auth.py once)

Usage:
  HUBSPOT_TOKEN=pat-xxx python3 keyword_report_2026.py
"""

import json
import os
import re
import sys
import warnings
from datetime import date, timedelta
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

SEO_TAG_ID    = "22542351"
DATE_START    = "2026-01-01"
DATE_END      = "2026-05-22"   # inclusive

# /ab/* paths are A/B variants of the homepage
AB_VARIANT_RE = re.compile(r"^/ab/", re.IGNORECASE)


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------

def normalise_url(raw_url: str) -> str | None:
    """Strip UTM/tracking params; map A/B variants to homepage."""
    if not raw_url:
        return None
    parsed = urlparse(raw_url)
    # Ensure www prefix is consistent
    netloc = parsed.netloc.lstrip("www.") if parsed.netloc else ""
    netloc = "www.openloyalty.io" if netloc in ("openloyalty.io", "www.openloyalty.io") else netloc
    path = parsed.path.rstrip("/") or "/"

    # A/B variants → homepage
    if AB_VARIANT_RE.match(path):
        path = "/"

    return urlunparse(("https", netloc, path, "", "", ""))


# ---------------------------------------------------------------------------
# HubSpot
# ---------------------------------------------------------------------------

def hs_headers():
    return {"Authorization": f"Bearer {HUBSPOT_TOKEN}", "Content-Type": "application/json"}


def get_seo_deals() -> list[dict]:
    """Return all SEO-tagged deals created Jan 1 – May 22 2026, sorted by date."""
    deals = []
    after = None
    while True:
        body = {
            "filterGroups": [{
                "filters": [
                    {"propertyName": "createdate", "operator": "BETWEEN",
                     "value": "1767225600000", "highValue": "1779494399000"},
                    {"propertyName": "hs_tag_ids", "operator": "CONTAINS_TOKEN",
                     "value": SEO_TAG_ID},
                ]
            }],
            "properties": ["dealname", "createdate"],
            "sorts": [{"propertyName": "createdate", "direction": "ASCENDING"}],
            "limit": 200,
        }
        if after:
            body["after"] = after

        resp = requests.post(f"{HS_API}/crm/v3/objects/deals/search",
                             headers=hs_headers(), json=body)
        resp.raise_for_status()
        data = resp.json()
        deals.extend(data.get("results", []))
        paging = data.get("paging", {}).get("next", {})
        after = paging.get("after")
        if not after:
            break
    return deals


def get_primary_contact(deal_id: int) -> dict | None:
    """Return the first contact associated with a deal that has hs_analytics_first_url."""
    resp = requests.get(
        f"{HS_API}/crm/v3/objects/deals/{deal_id}/associations/contacts",
        headers=hs_headers(),
    )
    if not resp.ok:
        return None
    contact_ids = [r["id"] for r in resp.json().get("results", [])]
    if not contact_ids:
        return None

    # Batch-fetch contact properties
    body = {
        "inputs": [{"id": cid} for cid in contact_ids[:10]],
        "properties": ["hs_analytics_first_url", "createdate"],
    }
    resp = requests.post(f"{HS_API}/crm/v3/objects/contacts/batch/read",
                         headers=hs_headers(), json=body)
    if not resp.ok:
        return None

    contacts = resp.json().get("results", [])
    # Prefer contacts that have hs_analytics_first_url set
    with_url = [c for c in contacts if c["properties"].get("hs_analytics_first_url")]
    pool = with_url if with_url else contacts
    if not pool:
        return None
    # Pick the one created earliest (most likely the original lead)
    pool.sort(key=lambda c: c["properties"].get("createdate", ""))
    return pool[0]


# ---------------------------------------------------------------------------
# GSC
# ---------------------------------------------------------------------------

def get_gsc_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def query_keywords(session, page_url: str, visit_date: date) -> list:
    def _query(start, end):
        payload = {
            "startDate": start, "endDate": end,
            "dimensions": ["query"],
            "dimensionFilterGroups": [{"filters": [{
                "dimension": "page", "operator": "equals", "expression": page_url,
            }]}],
            "rowLimit": 25,
        }
        r = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
        r.raise_for_status()
        return r.json().get("rows", [])

    d = visit_date.isoformat()
    rows = _query(d, d)
    if not rows:
        start = (visit_date - timedelta(days=1)).isoformat()
        end   = (visit_date + timedelta(days=1)).isoformat()
        rows  = _query(start, end)
    return rows


def top_keyword(rows: list) -> dict | None:
    if not rows:
        return None
    rows_sorted = sorted(rows, key=lambda r: (-r["clicks"], -r["impressions"]))
    best = rows_sorted[0]
    return {
        "keyword":     best["keys"][0],
        "clicks":      int(best["clicks"]),
        "impressions": int(best["impressions"]),
        "position":    round(best["position"], 1),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

MONTHS = {
    "2026-01": "January 2026",
    "2026-02": "February 2026",
    "2026-03": "March 2026",
    "2026-04": "April 2026",
    "2026-05": "May 2026 (1–22)",
}

COL_W = {"deal": 34, "page": 48, "date": 11, "keyword": 40, "cl": 7, "im": 8, "pos": 6}


def print_table(rows: list[dict], title: str):
    if not rows:
        print(f"\n  {title}: no data\n")
        return
    print(f"\n{'='*110}")
    print(f"  {title}  ({len(rows)} deals)")
    print(f"{'='*110}")
    hdr = (f"{'Deal':<{COL_W['deal']}}  {'First Page':<{COL_W['page']}}  "
           f"{'Date':<{COL_W['date']}}  {'Top Keyword':<{COL_W['keyword']}}  "
           f"{'Clicks':>{COL_W['cl']}}  {'Impr':>{COL_W['im']}}  {'Pos':>{COL_W['pos']}}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        page_short = r["page"].replace("https://www.openloyalty.io", "")[:COL_W["page"]]
        kw = (r["keyword"] or "—")[:COL_W["keyword"]]
        cl = str(r["clicks"]) if r["clicks"] != "—" else "—"
        im = str(r["impressions"]) if r["impressions"] != "—" else "—"
        pos = str(r["position"]) if r["position"] != "—" else "—"
        print(f"{r['deal']:<{COL_W['deal']}}  {page_short:<{COL_W['page']}}  "
              f"{r['date']:<{COL_W['date']}}  {kw:<{COL_W['keyword']}}  "
              f"{cl:>{COL_W['cl']}}  {im:>{COL_W['im']}}  {pos:>{COL_W['pos']}}")


def main():
    if not HUBSPOT_TOKEN:
        sys.exit("ERROR: set HUBSPOT_TOKEN env variable")

    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    gsc = get_gsc_session()

    print("Fetching SEO deals from HubSpot...", flush=True)
    deals = get_seo_deals()
    print(f"  {len(deals)} deals found", flush=True)

    results_by_month: dict[str, list] = {m: [] for m in MONTHS}

    for i, deal in enumerate(deals, 1):
        deal_id   = int(deal["id"])
        deal_name = deal["properties"]["dealname"]
        deal_date = deal["properties"]["createdate"][:10]   # YYYY-MM-DD
        month_key = deal_date[:7]

        print(f"  [{i}/{len(deals)}] {deal_name} ({deal_date})", end="  ", flush=True)

        contact = get_primary_contact(deal_id)
        row = {
            "deal":        deal_name,
            "page":        "—",
            "date":        deal_date,
            "keyword":     "no contact",
            "clicks":      "—",
            "impressions": "—",
            "position":    "—",
        }

        if contact:
            raw_url = contact["properties"].get("hs_analytics_first_url")
            contact_date_str = contact["properties"].get("createdate", deal_date)[:10]
            contact_date = date.fromisoformat(contact_date_str)
            norm_url = normalise_url(raw_url)
            row["page"] = norm_url or "—"
            row["date"] = contact_date_str

            if norm_url:
                rows = query_keywords(gsc, norm_url, contact_date)
                best = top_keyword(rows)
                if best:
                    row.update({"keyword": best["keyword"], "clicks": best["clicks"],
                                "impressions": best["impressions"], "position": best["position"]})
                else:
                    row["keyword"] = "no GSC data"
            else:
                row["keyword"] = "no URL"

        print(row["keyword"], flush=True)
        results_by_month.get(month_key, results_by_month.setdefault(month_key, [])).append(row)

    print()
    for month_key, title in MONTHS.items():
        print_table(results_by_month.get(month_key, []), title)


if __name__ == "__main__":
    main()
