#!/usr/bin/env python3
"""GSC analysis over equal-length periods before/after the Feb 26 2026 rename.

Before period: N days ending 2026-02-26 (achievements, last day live)
After period:   N days starting 2026-02-27 (challenges, first day live)
N = however many days of "after" data we currently have.
"""

import json
import warnings
from datetime import date, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

TOKEN_FILE = "token.json"
SITE = "sc-domain:openloyalty.io"
GSC_API = "https://www.googleapis.com/webmasters/v3"

PAGES = {
    "achievements": "https://www.openloyalty.io/product/achievements",
    "challenges": "https://www.openloyalty.io/product/challenges",
}

AFTER_FROM = date(2026, 2, 27)
AFTER_TO = date(2026, 7, 28)
BEFORE_TO = date(2026, 2, 26)

PERIOD_DAYS = (AFTER_TO - AFTER_FROM).days + 1
BEFORE_FROM = BEFORE_TO - timedelta(days=PERIOD_DAYS - 1)

PERIODS = {
    "achievements": ("BEFORE (last equal period, old page)", BEFORE_FROM, BEFORE_TO),
    "challenges": ("AFTER (equal period, new page)", AFTER_FROM, AFTER_TO),
}


def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def query(session, page_url, dimensions, date_from, date_to, row_limit=25000):
    payload = {
        "startDate": date_from.isoformat(),
        "endDate": date_to.isoformat(),
        "dimensions": dimensions,
        "dimensionFilterGroups": [
            {"filters": [{"dimension": "page", "operator": "equals", "expression": page_url}]}
        ],
        "rowLimit": row_limit,
    }
    resp = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
    resp.raise_for_status()
    return resp.json()


def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    print(f"Period length: {PERIOD_DAYS} days")
    print(f"BEFORE window: {BEFORE_FROM} .. {BEFORE_TO}")
    print(f"AFTER  window: {AFTER_FROM} .. {AFTER_TO}")
    print()

    results = {}

    for name, url in PAGES.items():
        label, date_from, date_to = PERIODS[name]
        print("=" * 100)
        print(f"PAGE: {name} -> {url}")
        print(f"WINDOW: {label}: {date_from} .. {date_to}")
        print("=" * 100)

        # Aggregate totals (no dimension breakdown)
        agg = query(session, url, [], date_from, date_to)
        rows = agg.get("rows", [])
        if rows:
            r = rows[0]
            clicks, impr, ctr, pos = r["clicks"], r["impressions"], r["ctr"], r["position"]
        else:
            clicks = impr = ctr = pos = 0
        print(f"\nTOTAL clicks={clicks:.0f}  impressions={impr:.0f}  ctr={ctr:.2%}  avg_position={pos:.1f}")
        results[name] = {"clicks": clicks, "impressions": impr}

        # Query-level breakdown for the SAME equal window
        q_rows = query(session, url, ["query"], date_from, date_to).get("rows", [])
        q_rows_sorted = sorted(q_rows, key=lambda r: (-r["impressions"], -r["clicks"]))
        print(f"\nBest-performing queries in this window (n={len(q_rows_sorted)}):")
        print(f"  {'Query':<55} {'Clicks':>7} {'Impr':>7} {'CTR':>7} {'Pos':>6}")
        print("  " + "-" * 85)
        for r in q_rows_sorted[:30]:
            kw = r["keys"][0]
            print(f"  {kw:<55} {r['clicks']:>7.0f} {r['impressions']:>7.0f} {r['ctr']:>6.1%} {r['position']:>6.1f}")
        print()

    print("=" * 100)
    print("SUMMARY (equal periods)")
    print("=" * 100)
    print(f"{'Page':<15} {'Window':<25} {'Clicks':>8} {'Impressions':>13}")
    print("-" * 65)
    print(f"{'achievements':<15} {str(BEFORE_FROM)+' to '+str(BEFORE_TO):<25} {results['achievements']['clicks']:>8.0f} {results['achievements']['impressions']:>13.0f}")
    print(f"{'challenges':<15} {str(AFTER_FROM)+' to '+str(AFTER_TO):<25} {results['challenges']['clicks']:>8.0f} {results['challenges']['impressions']:>13.0f}")


if __name__ == "__main__":
    main()
