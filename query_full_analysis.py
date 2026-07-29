#!/usr/bin/env python3
"""Full visibility analysis for /product/achievements vs /product/challenges.

Pulls the complete query list (not just top N) for each URL, splits into
before/after the Feb 26 2026 rename, and diffs the query sets to see what
was retained, lost, or newly gained.
"""

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

FULL_FROM = "2025-08-01"
FULL_TO = "2026-07-28"
CHANGE_DATE = "2026-02-26"
BEFORE_TO = "2026-02-26"
AFTER_FROM = "2026-02-27"


def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def query(session, page_url, dimensions, date_from, date_to, row_limit=25000):
    payload = {
        "startDate": date_from,
        "endDate": date_to,
        "dimensions": dimensions,
        "dimensionFilterGroups": [
            {"filters": [{"dimension": "page", "operator": "equals", "expression": page_url}]}
        ],
        "rowLimit": row_limit,
    }
    resp = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
    resp.raise_for_status()
    return resp.json().get("rows", [])


def print_query_table(rows, title):
    rows_sorted = sorted(rows, key=lambda r: (-r["impressions"], -r["clicks"]))
    print(f"\n{title} (n={len(rows_sorted)}):")
    if not rows_sorted:
        print("  (none)")
        return
    print(f"  {'Query':<55} {'Clicks':>7} {'Impr':>7} {'CTR':>7} {'Pos':>6}")
    print("  " + "-" * 85)
    for r in rows_sorted:
        kw = r["keys"][0]
        print(f"  {kw:<55} {r['clicks']:>7.0f} {r['impressions']:>7.0f} {r['ctr']:>6.1%} {r['position']:>6.1f}")


def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    all_data = {}

    for name, url in PAGES.items():
        print("#" * 100)
        print(f"# PAGE: {name} -> {url}")
        print("#" * 100)

        full_rows = query(session, url, ["query"], FULL_FROM, FULL_TO)
        before_rows = query(session, url, ["query"], FULL_FROM, BEFORE_TO)
        after_rows = query(session, url, ["query"], AFTER_FROM, FULL_TO)

        all_data[name] = {
            "full": {r["keys"][0]: r for r in full_rows},
            "before": {r["keys"][0]: r for r in before_rows},
            "after": {r["keys"][0]: r for r in after_rows},
        }

        print_query_table(full_rows, f"ALL queries, full window {FULL_FROM}..{FULL_TO}")
        print_query_table(before_rows, f"BEFORE change ({FULL_FROM}..{BEFORE_TO})")
        print_query_table(after_rows, f"AFTER change ({AFTER_FROM}..{FULL_TO})")
        print()

    # Cross-page diff: queries feeding achievements (all-time) vs challenges (all-time)
    ach_queries = set(all_data["achievements"]["full"].keys())
    chal_queries = set(all_data["challenges"]["full"].keys())

    print("#" * 100)
    print("# CROSS-PAGE QUERY SET DIFF (all-time)")
    print("#" * 100)

    only_ach = ach_queries - chal_queries
    only_chal = chal_queries - ach_queries
    both = ach_queries & chal_queries

    print(f"\nQueries that fed ONLY achievements (never showed for challenges), n={len(only_ach)}:")
    for q in sorted(only_ach, key=lambda q: -all_data["achievements"]["full"][q]["impressions"]):
        r = all_data["achievements"]["full"][q]
        print(f"  {q:<55} impr={r['impressions']:.0f} clicks={r['clicks']:.0f} pos={r['position']:.1f}")

    print(f"\nQueries that feed ONLY challenges (new, never showed for achievements), n={len(only_chal)}:")
    for q in sorted(only_chal, key=lambda q: -all_data["challenges"]["full"][q]["impressions"]):
        r = all_data["challenges"]["full"][q]
        print(f"  {q:<55} impr={r['impressions']:.0f} clicks={r['clicks']:.0f} pos={r['position']:.1f}")

    print(f"\nQueries that fed BOTH pages (retained overlap), n={len(both)}:")
    for q in sorted(both, key=lambda q: -(all_data['achievements']['full'][q]['impressions'] + all_data['challenges']['full'][q]['impressions'])):
        ra = all_data["achievements"]["full"][q]
        rc = all_data["challenges"]["full"][q]
        print(f"  {q:<55} achievements: impr={ra['impressions']:.0f} pos={ra['position']:.1f}  |  challenges: impr={rc['impressions']:.0f} pos={rc['position']:.1f}")


if __name__ == "__main__":
    main()
