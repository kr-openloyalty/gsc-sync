#!/usr/bin/env python3
"""One-off: query GSC W31 positions for Cluster 3 & 4."""

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
START, END   = "2026-07-27", "2026-08-02"

C3 = [
    "retail loyalty program software",
    "b2b loyalty program software",
    "best loyalty software",
    "best loyalty program software",
    "yotpo alternatives",
    "top loyalty platforms",
    "restaurant loyalty software",
    "smile.io alternatives",
    "loyalty program pricing",
    "loyalty program cost",
    "luxury loyalty program",
    "voucherify alternatives",
    "enterprise loyalty platform",
    "best loyalty management software",
    "enterprise loyalty software",
    "best loyalty platform",
    "talon.one alternatives",
    "loyaltylion alternatives",
    "antavo alternatives",
    "loyalty platform vendors",
    "loyalty platform migration",
]

C4 = [
    "customer retention software",
    "customer retention strategy",
    "how to increase customer lifetime value",
    "how to reduce customer churn",
    "increase customer lifetime value",
    "customer lifetime value software",
    "omnichannel loyalty program",
    "loyalty platform comparison",
    "loyalty program implementation",
    "ecommerce loyalty program software",
    "loyalty program management system",
]

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
            print(f"      retry {attempt+1} after {wait}s: {exc}")
            time.sleep(wait)
    return []

def get_position_us(session, keyword):
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
    return math.floor(best["position"] * 10) / 10

def fmt(v):
    if v is None:
        return ""
    return f"{v:.1f}".replace(".", ",")

def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    lines = ["Keyword\tCluster\tW31 position (US)"]

    print(f"Cluster 3 — {len(C3)} keywords")
    for kw in C3:
        pos = get_position_us(session, kw)
        print(f"  {kw:<45} {fmt(pos) or '—'}")
        lines.append(f"{kw}\tCluster 3\t{fmt(pos)}")

    print(f"\nCluster 4 — {len(C4)} keywords")
    for kw in C4:
        pos = get_position_us(session, kw)
        print(f"  {kw:<45} {fmt(pos) or '—'}")
        lines.append(f"{kw}\tCluster 4\t{fmt(pos)}")

    out = "/tmp/clusters34_w31.tsv"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nDone → {out}")

if __name__ == "__main__":
    main()
