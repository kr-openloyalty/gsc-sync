#!/usr/bin/env python3
"""
Check GSC for ranking pages across all 4 content-plan clusters.
Date range: last 4 weeks (W29–W32) for a stable signal.
"""

import json
import math
import time
import warnings
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

TOKEN_FILE   = "token.json"
SITE         = "sc-domain:openloyalty.io"
GSC_ENDPOINT = "https://www.googleapis.com/webmasters/v3"
API_SLEEP    = 0.35
START, END   = "2026-07-13", "2026-08-09"   # W29–W32

CLUSTERS = {
    "C1": [
        "customer loyalty software",
        "loyalty system",
        "best customer loyalty software",
        "loyalty program software",
        "coupon management software",
        "loyalty software",
        "customer loyalty platform",
        "loyalty card system",
        "customer loyalty program software",
        "loyalty program api",
        "loyalty program saas",
        "loyalty rewards management system",
        "voucher management system",
    ],
    "C2": [
        "b2b loyalty programs",
        "card linked loyalty programs",
        "loyalty program best practices",
        "retail gamification",
        "ecommerce loyalty platform",
        "fashion loyalty programs",
        "best rewards programs",
        "luxury brand loyalty programs",
        "beauty loyalty programs",
        "how to calculate roi for loyalty programs",
    ],
    "C3": [
        "yotpo alternatives",
        "best loyalty program software",
        "retail loyalty program software",
        "b2b loyalty program software",
        "best loyalty software",
        "restaurant loyalty software",
        "enterprise loyalty software",
        "best loyalty management software",
        "best loyalty platform",
        "voucherify alternatives",
        "smile.io alternatives",
        "loyaltylion alternatives",
        "top loyalty platforms",
        "enterprise loyalty platform",
        "loyalty platform vendors",
        "loyalty program cost",
        "loyalty platform migration",
        "talon.one alternatives",
        "antavo alternatives",
        "loyalty program pricing",
        "luxury loyalty program",
    ],
    "C4": [
        "customer retention software",
        "customer lifetime value software",
        "loyalty platform comparison",
        "loyalty program management system",
        "omnichannel loyalty program",
        "ecommerce loyalty program software",
        "how to increase customer lifetime value",
        "customer retention strategy",
        "how to reduce customer churn",
        "loyalty program implementation",
        "increase customer lifetime value",
    ],
}

def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    s = AuthorizedSession(creds)
    s.verify = False
    return s

def gsc_post(session, payload, retries=4):
    for attempt in range(retries):
        try:
            r = session.post(
                f"{GSC_ENDPOINT}/sites/{SITE}/searchAnalytics/query",
                json=payload,
            )
            r.raise_for_status()
            return r.json().get("rows", [])
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            time.sleep(wait)
    return []

def best_page(session, keyword):
    """Return (page_url, position, impressions) for best US page, or None."""
    rows = gsc_post(session, {
        "startDate": START, "endDate": END,
        "dimensions": ["page"],
        "dimensionFilterGroups": [{"filters": [
            {"dimension": "query",   "operator": "equals", "expression": keyword},
            {"dimension": "country", "operator": "equals", "expression": "usa"},
        ]}],
        "rowLimit": 25,
    })
    time.sleep(API_SLEEP)
    valid = [r for r in rows if r["impressions"] > 0]
    if not valid:
        return None
    max_impr   = max(r["impressions"] for r in valid)
    comparable = [r for r in valid if r["impressions"] * 3 >= max_impr]
    best       = min(comparable, key=lambda r: r["position"])
    pos        = math.floor(best["position"] * 10) / 10
    url        = best["keys"][0].replace("https://openloyalty.io", "")
    impr       = int(best["impressions"])
    return url, pos, impr

def fmt_pos(v):
    return f"{v:.1f}".replace(".", ",") if v is not None else "—"

def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    lines = ["Cluster\tKeyword\tRanking page\tPosition (US)\tImpressions (W29-W32)"]
    print(f"{'Cluster':<6} {'Keyword':<48} {'Page':<55} {'Pos':>6} {'Impr':>6}")
    print("-" * 125)

    for cluster, keywords in CLUSTERS.items():
        for kw in keywords:
            result = best_page(session, kw)
            if result:
                url, pos, impr = result
                print(f"{cluster:<6} {kw:<48} {url:<55} {fmt_pos(pos):>6} {impr:>6}")
                lines.append(f"{cluster}\t{kw}\t{url}\t{fmt_pos(pos)}\t{impr}")
            else:
                print(f"{cluster:<6} {kw:<48} {'(no ranking page)':<55} {'—':>6} {'—':>6}")
                lines.append(f"{cluster}\t{kw}\t\t\t")

    out = "/tmp/content_plan_gsc.tsv"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nDone → {out}")

if __name__ == "__main__":
    main()
