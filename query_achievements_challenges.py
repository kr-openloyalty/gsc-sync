#!/usr/bin/env python3
"""GSC page-level performance for /product/achievements vs /product/challenges,
before and after the Feb 26 2026 rename."""

import json
import warnings

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

TOKEN_FILE = "token.json"
SITE = "sc-domain:openloyalty.io"
GSC_API = "https://www.googleapis.com/webmasters/v3"

PAGES = {
    "achievements": "https://www.openloyalty.io/product/achievements",
    "challenges": "https://www.openloyalty.io/product/challenges",
}

DATE_FROM = "2025-08-01"
DATE_TO = "2026-07-28"


def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def query(session, page_url, dimensions, row_limit=25000, extra=None):
    payload = {
        "startDate": DATE_FROM,
        "endDate": DATE_TO,
        "dimensions": dimensions,
        "dimensionFilterGroups": [
            {"filters": [{"dimension": "page", "operator": "equals", "expression": page_url}]}
        ],
        "rowLimit": row_limit,
    }
    if extra:
        payload.update(extra)
    resp = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
    resp.raise_for_status()
    return resp.json().get("rows", [])


def monthly_bucket(rows):
    buckets = {}
    for r in rows:
        d = r["keys"][0]
        month = d[:7]
        b = buckets.setdefault(month, {"clicks": 0, "impressions": 0, "pos_sum": 0.0, "n": 0})
        b["clicks"] += r["clicks"]
        b["impressions"] += r["impressions"]
        b["pos_sum"] += r["position"] * r["impressions"]
        b["n"] += r["impressions"]
    return buckets


def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    for name, url in PAGES.items():
        print("=" * 100)
        print(f"PAGE: {name} -> {url}")
        print("=" * 100)

        daily_rows = query(session, url, ["date"])
        print(f"\nTotal rows (days with data): {len(daily_rows)}")
        total_clicks = sum(r["clicks"] for r in daily_rows)
        total_impr = sum(r["impressions"] for r in daily_rows)
        print(f"TOTAL over {DATE_FROM}..{DATE_TO}: clicks={total_clicks:.0f}  impressions={total_impr:.0f}")

        buckets = monthly_bucket(daily_rows)
        print(f"\n{'Month':<10} {'Clicks':>8} {'Impr':>10} {'AvgPos':>8}")
        print("-" * 40)
        for month in sorted(buckets):
            b = buckets[month]
            avg_pos = (b["pos_sum"] / b["n"]) if b["n"] else 0
            print(f"{month:<10} {b['clicks']:>8.0f} {b['impressions']:>10.0f} {avg_pos:>8.1f}")

        query_rows = query(session, url, ["query"], row_limit=50, extra={"orderBy": None})
        query_rows_sorted = sorted(query_rows, key=lambda r: (-r["clicks"], -r["impressions"]))
        print(f"\nTop queries driving this page ({DATE_FROM}..{DATE_TO}), n={len(query_rows_sorted)}:")
        print(f"{'Query':<50} {'Clicks':>7} {'Impr':>7} {'CTR':>7} {'Pos':>6}")
        print("-" * 80)
        for r in query_rows_sorted[:25]:
            kw = r["keys"][0]
            print(f"{kw:<50} {r['clicks']:>7.0f} {r['impressions']:>7.0f} {r['ctr']:>6.1%} {r['position']:>6.1f}")
        print()


if __name__ == "__main__":
    main()
