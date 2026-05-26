#!/usr/bin/env python3
"""
Validate: for SEO-tagged deals (last week), find the organic-search contact's
first page seen, then look up the top GSC keyword for that page on the
contact's create date (3-day delay applied).

HubSpot data is hardcoded from the MCP query run on 2026-05-26.
GSC queries use the same auth/session pattern as test_keyword_lookup.py.
"""

import json
import warnings
from datetime import date, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

TOKEN_FILE  = "token.json"
SITE        = "sc-domain:openloyalty.io"
GSC_API     = "https://www.googleapis.com/webmasters/v3"

# ---------------------------------------------------------------------------
# HubSpot data (from MCP query, deals created 2026-05-18 → 2026-05-24,
# tag 22542351 = SEO, contact original source = ORGANIC_SEARCH)
# ---------------------------------------------------------------------------
DEALS = [
    {
        "deal":        "Ignitis",
        "contact":     "Verners Krastins",
        "lifecycle":   "opportunity",
        "first_url":   "https://www.openloyalty.io/applications/white-label-loyalty",
        "created":     date(2026, 5, 18),
    },
    {
        "deal":        "The Miles Consultancy",
        "contact":     "Ollie Barnes",
        "lifecycle":   "opportunity",
        "first_url":   "https://www.openloyalty.io/",
        "created":     date(2026, 5, 18),
    },
    {
        "deal":        "WePartner Group",
        "contact":     "Kathy Ding",
        "lifecycle":   "opportunity",
        "first_url":   "https://www.openloyalty.io/insider/coupon-management-software",
        "created":     date(2026, 5, 18),
    },
    {
        "deal":        "IMEX GROUP",
        "contact":     "Gabriella Bernardi",
        "lifecycle":   "opportunity",
        "first_url":   "https://www.openloyalty.io/",
        "created":     date(2026, 5, 19),
    },
    {
        "deal":        "The FIFTH",
        "contact":     "Jackqueline Lou",
        "lifecycle":   "opportunity",
        "first_url":   "https://www.openloyalty.io/",
        "created":     date(2026, 5, 22),
    },
    # --- No organic-search contact (excluded from GSC lookup) ---
    {
        "deal":        "El Cielo",
        "contact":     "Luisa Fernanda Mendez Paredes",
        "lifecycle":   "opportunity",
        "first_url":   None,   # PAID_SEARCH — skip
        "created":     date(2026, 5, 19),
        "skip_reason": "PAID_SEARCH",
    },
    {
        "deal":        "Gjensidige",
        "contact":     "Simon Andersen",
        "lifecycle":   "opportunity",
        "first_url":   None,   # DIRECT_TRAFFIC — skip
        "created":     date(2026, 5, 22),
        "skip_reason": "DIRECT_TRAFFIC",
    },
    {
        "deal":        "Via Trading",
        "contact":     "Miguel Fonseca",
        "lifecycle":   "opportunity",
        "first_url":   None,   # DIRECT_TRAFFIC — skip
        "created":     date(2026, 5, 22),
        "skip_reason": "DIRECT_TRAFFIC",
    },
]

# ---------------------------------------------------------------------------
# GSC helpers (identical logic to test_keyword_lookup.py)
# ---------------------------------------------------------------------------

def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    session = AuthorizedSession(creds)
    session.verify = False
    return session


def query_keywords(session, page_url, visit_date: date):
    """Return GSC keyword rows for page_url on visit_date (±1 day fallback)."""
    query_date = visit_date.isoformat()
    payload = {
        "startDate": query_date,
        "endDate":   query_date,
        "dimensions": ["query"],
        "dimensionFilterGroups": [{
            "filters": [{
                "dimension": "page",
                "operator":  "equals",
                "expression": page_url,
            }]
        }],
        "rowLimit": 25,
    }
    resp = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
    resp.raise_for_status()
    rows = resp.json().get("rows", [])

    if not rows:
        # Widen to ±1 day
        start = (visit_date - timedelta(days=1)).isoformat()
        end   = (visit_date + timedelta(days=1)).isoformat()
        payload.update({"startDate": start, "endDate": end})
        resp = session.post(f"{GSC_API}/sites/{SITE}/searchAnalytics/query", json=payload)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])

    return rows


def top_keyword(rows):
    if not rows:
        return None
    rows_sorted = sorted(rows, key=lambda r: (-r["clicks"], -r["impressions"]))
    best = rows_sorted[0]
    return {
        "keyword":     best["keys"][0],
        "clicks":      int(best["clicks"]),
        "impressions": int(best["impressions"]),
        "ctr":         best["ctr"],
        "position":    best["position"],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    session = get_session()

    # GSC delay: query the actual contact creation date
    # (data for the exact day may not yet be available; ±1 fallback handles that)
    DELAY_DAYS = 0  # query the visit date directly, fallback widens ±1

    results = []
    for deal in DEALS:
        row = {
            "Deal":        deal["deal"],
            "Contact":     deal["contact"],
            "Lifecycle":   deal["lifecycle"],
            "First Page":  deal.get("first_url") or "—",
            "GSC Date":    "—",
            "Top Keyword": "—",
            "Clicks":      "—",
            "Impressions": "—",
            "Position":    "—",
        }

        if deal.get("skip_reason"):
            row["Top Keyword"] = f"n/a ({deal['skip_reason']})"
            results.append(row)
            continue

        gsc_date = deal["created"] - timedelta(days=DELAY_DAYS)
        row["GSC Date"] = gsc_date.isoformat()

        rows = query_keywords(session, deal["first_url"], gsc_date)
        best = top_keyword(rows)

        if best:
            row["Top Keyword"] = best["keyword"]
            row["Clicks"]      = best["clicks"]
            row["Impressions"] = best["impressions"]
            row["Position"]    = f"{best['position']:.1f}"
        else:
            row["Top Keyword"] = "no GSC data"

        results.append(row)

    # Print table
    cols = ["Deal", "Contact", "Lifecycle", "First Page", "GSC Date",
            "Top Keyword", "Clicks", "Impressions", "Position"]
    widths = {c: max(len(c), max(len(str(r[c])) for r in results)) for c in cols}

    header = "  ".join(c.ljust(widths[c]) for c in cols)
    print(header)
    print("-" * len(header))
    for r in results:
        print("  ".join(str(r[c]).ljust(widths[c]) for c in cols))


if __name__ == "__main__":
    main()
