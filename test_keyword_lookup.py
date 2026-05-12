#!/usr/bin/env python3
"""Test: find top keyword for a given page + date from Google Search Console."""

import json
import warnings
from datetime import date, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

TOKEN_FILE = "token.json"
SITE = "sc-domain:openloyalty.io"
GSC_API = "https://www.googleapis.com/webmasters/v3"

# Input
PAGE_URL = "https://www.openloyalty.io/insider/gamification-healthcare"
VISIT_DATE = date(2026, 5, 7)
# GSC data is typically delayed ~3 days, so we query up to visit_date
# (data for the visit date itself may or may not be available yet)
QUERY_DATE = VISIT_DATE.isoformat()


def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def query_keywords(session, page_url, query_date):
    payload = {
        "startDate": query_date,
        "endDate": query_date,
        "dimensions": ["query"],
        "dimensionFilterGroups": [
            {
                "filters": [
                    {
                        "dimension": "page",
                        "operator": "equals",
                        "expression": page_url,
                    }
                ]
            }
        ],
        "rowLimit": 25,
        "startRow": 0,
    }

    resp = session.post(
        f"{GSC_API}/sites/{SITE}/searchAnalytics/query",
        json=payload,
    )
    resp.raise_for_status()
    return resp.json().get("rows", [])


def top_keyword(rows):
    if not rows:
        return None
    # Primary sort: clicks desc; secondary: impressions desc
    rows_sorted = sorted(rows, key=lambda r: (-r["clicks"], -r["impressions"]))
    return rows_sorted[0]


def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    print(f"Page   : {PAGE_URL}")
    print(f"Date   : {QUERY_DATE}")
    print()

    rows = query_keywords(session, PAGE_URL, QUERY_DATE)

    if not rows:
        print("No GSC data found for this page/date combination.")
        print("Trying ±1 day window...")
        # Widen to a 3-day window centred on the visit date
        start = (VISIT_DATE - timedelta(days=1)).isoformat()
        end = (VISIT_DATE + timedelta(days=1)).isoformat()
        payload = {
            "startDate": start,
            "endDate": end,
            "dimensions": ["query"],
            "dimensionFilterGroups": [
                {
                    "filters": [
                        {
                            "dimension": "page",
                            "operator": "equals",
                            "expression": PAGE_URL,
                        }
                    ]
                }
            ],
            "rowLimit": 25,
        }
        resp = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])
        if rows:
            print(f"Found data in window {start} → {end}\n")

    if not rows:
        print("Still no data. The page may have no GSC impressions for this period.")
        return

    print(f"{'Keyword':<60} {'Clicks':>6}  {'Impr':>6}  {'CTR':>6}  {'Pos':>5}")
    print("-" * 88)
    rows_sorted = sorted(rows, key=lambda r: (-r["clicks"], -r["impressions"]))
    for r in rows_sorted:
        kw = r["keys"][0]
        print(f"{kw:<60} {r['clicks']:>6.0f}  {r['impressions']:>6.0f}  {r['ctr']:>6.1%}  {r['position']:>5.1f}")

    best = top_keyword(rows)
    print()
    print("=" * 88)
    print(f"TOP KEYWORD: '{best['keys'][0]}'")
    print(f"  clicks={best['clicks']:.0f}  impressions={best['impressions']:.0f}  "
          f"ctr={best['ctr']:.1%}  avg_position={best['position']:.1f}")


if __name__ == "__main__":
    main()
