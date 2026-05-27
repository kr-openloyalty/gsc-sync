#!/usr/bin/env python3
"""
sync_gsc_to_sheets.py

Reads a keyword-position scorecard from Google Sheets, queries Google Search
Console for US-only data, finds the best-performing page for each keyword,
then back-fills weekly average positions into the sheet.

Usage:
  python3 sync_gsc_to_sheets.py             # update the sheet
  python3 sync_gsc_to_sheets.py --dry-run   # preview without writing

Expected sheet layout (row 1 = header, column A = keywords):

  |  Keyword                | 2026-02-24 | 2026-03-03 | 2026-03-10 | ...  |
  |-------------------------|-----------|-----------|-----------|------|
  | loyalty program software|    2.8    |    3.1    |    2.9    | ...  |
  | loyalty points system   |   12.9    |   11.4    |   13.2    | ...  |

  - Row 1:  "Keyword" label in A1; week-start dates (any common format) in B1+
  - Col A:  Keyword strings (exact-match query in GSC)
  - Data cells: filled/overwritten by this script

Logic per keyword:
  1. Scan the full tracked period (US only) to find the page that earned
     the most clicks (ties broken by impressions) — the "best page".
  2. For every week column in the sheet, query GSC for that keyword +
     best page + US and write the resulting aggregate position.

Auth:
  Requires token.json with BOTH webmasters.readonly AND spreadsheets scopes.
  If your token was generated with the old single-scope auth.py, delete
  token.json and re-run:  python3 auth.py
"""

import json
import sys
import time
import warnings
from datetime import date, timedelta, datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build

# ── Configuration ──────────────────────────────────────────────────────────────

TOKEN_FILE     = "token.json"
SITE           = "sc-domain:openloyalty.io"
GSC_ENDPOINT   = "https://www.googleapis.com/webmasters/v3"

SPREADSHEET_ID = "1-93tOhuhxSqYwl8bLfzXzwj0JgoQuVqbD9VJNvcymbg"

# Country filter — GSC uses ISO 3166-1 alpha-3 (lowercase)
COUNTRY = "usa"

# Seconds between GSC API calls (stay well under quota)
API_SLEEP = 0.35

# Both scopes must be in the token for this script to work
SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# ── Auth helpers ───────────────────────────────────────────────────────────────


def get_credentials() -> Credentials:
    with open(TOKEN_FILE) as f:
        return Credentials.from_authorized_user_info(json.load(f), SCOPES)


def get_gsc_session(creds: Credentials) -> AuthorizedSession:
    session = AuthorizedSession(creds)
    session.verify = False  # suppress SSL warning (same as auth.py)
    return session


# ── GSC helpers ───────────────────────────────────────────────────────────────


def _gsc_post(session: AuthorizedSession, payload: dict, retries: int = 4) -> list:
    """POST to GSC searchAnalytics with exponential-back-off retry."""
    for attempt in range(retries):
        try:
            resp = session.post(
                f"{GSC_ENDPOINT}/sites/{SITE}/searchAnalytics/query",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json().get("rows", [])
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"      ↻ Retry {attempt + 1}/{retries - 1} after: {exc}  (wait {wait}s)")
            time.sleep(wait)
    return []


def find_best_page(
    session: AuthorizedSession,
    keyword: str,
    start_date: str,
    end_date: str,
) -> tuple[str, float, float] | None:
    """
    Query GSC for all US pages that ranked for *keyword* over the period.
    Returns (page_url, clicks, impressions) for the page with the most clicks
    (ties broken by impressions), or None if no data.
    """
    rows = _gsc_post(session, {
        "startDate":  start_date,
        "endDate":    end_date,
        "dimensions": ["page"],
        "dimensionFilterGroups": [{
            "filters": [
                {"dimension": "query",   "operator": "equals", "expression": keyword},
                {"dimension": "country", "operator": "equals", "expression": COUNTRY},
            ]
        }],
        "rowLimit": 25,
    })
    time.sleep(API_SLEEP)

    if not rows:
        return None

    best = max(rows, key=lambda r: (r["clicks"], r["impressions"]))
    return best["keys"][0], best["clicks"], best["impressions"]


def get_weekly_position(
    session: AuthorizedSession,
    keyword: str,
    page_url: str,
    week_start: str,
    week_end: str,
) -> float | None:
    """
    Query GSC for the aggregate average position of *keyword* on *page_url*
    in the US for the 7-day window [week_start, week_end] (ISO date strings).
    Returns a rounded float, or None if GSC has no data for that window.
    """
    rows = _gsc_post(session, {
        "startDate":  week_start,
        "endDate":    week_end,
        "dimensions": [],          # no dimensions → single aggregate row
        "dimensionFilterGroups": [{
            "filters": [
                {"dimension": "query",   "operator": "equals", "expression": keyword},
                {"dimension": "page",    "operator": "equals", "expression": page_url},
                {"dimension": "country", "operator": "equals", "expression": COUNTRY},
            ]
        }],
    })
    time.sleep(API_SLEEP)

    if not rows:
        return None
    return round(rows[0]["position"], 1)


# ── Google Sheets helpers ──────────────────────────────────────────────────────


def col_to_letter(col: int) -> str:
    """Convert 1-indexed column number to a column letter string (A, B, …, AA, …)."""
    s = ""
    while col > 0:
        col, rem = divmod(col - 1, 26)
        s = chr(ord("A") + rem) + s
    return s


def get_first_sheet_name(service) -> str:
    """Return the title of the first (leftmost) sheet tab."""
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = meta.get("sheets", [])
    if sheets:
        return sheets[0]["properties"]["title"]
    return "Sheet1"


def read_sheet_values(service, sheet_name: str) -> list[list[str]]:
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=SPREADSHEET_ID, range=sheet_name)
        .execute()
    )
    return result.get("values", [])


def batch_write(service, updates: list[dict]) -> None:
    """
    Write multiple cells in one API call.
    Each update: {"range": "SheetName!B3", "values": [[value]]}
    """
    if not updates:
        return
    # Sheets API batchUpdate limit is ~1 000 ranges per request; chunk to be safe
    chunk_size = 200
    for i in range(0, len(updates), chunk_size):
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "RAW", "data": updates[i : i + chunk_size]},
        ).execute()
        if i + chunk_size < len(updates):
            time.sleep(0.5)


# ── Date parsing ──────────────────────────────────────────────────────────────

_DATE_FORMATS = [
    "%Y-%m-%d",    # ISO:       2026-02-24
    "%d/%m/%Y",    # European:  24/02/2026
    "%m/%d/%Y",    # US:        02/24/2026
    "%d.%m.%Y",    # Dot:       24.02.2026
    "%Y/%m/%d",    # Alt ISO:   2026/02/24
    "%d-%m-%Y",    # Dash-EU:   24-02-2026
    "%B %d, %Y",   # Long:      February 24, 2026
    "%b %d, %Y",   # Short:     Feb 24, 2026
    "%d %B %Y",    # EU Long:   24 February 2026
    "%d %b %Y",    # EU Short:  24 Feb 2026
]


def parse_date(s: str) -> date | None:
    """Try common date formats; return date object or None."""
    s = s.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ── Sheet structure detection ─────────────────────────────────────────────────


def detect_header_row(rows: list[list[str]], max_scan: int = 5) -> int:
    """
    Return the 0-indexed row that contains at least 2 parseable dates
    (these are the week-column headers).  Falls back to row 0.
    """
    for row_idx, row in enumerate(rows[:max_scan]):
        date_count = sum(1 for cell in row if parse_date(str(cell)))
        if date_count >= 2:
            return row_idx
    return 0


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("🔍  DRY RUN — no changes will be written to the sheet.\n")

    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    # Authenticate
    creds  = get_credentials()
    gsc    = get_gsc_session(creds)
    sheets = build("sheets", "v4", credentials=creds)

    # ── Read the spreadsheet ───────────────────────────────────────────────────
    print("Reading spreadsheet…")
    sheet_name = get_first_sheet_name(sheets)
    print(f"  Tab: '{sheet_name}'")

    all_rows = read_sheet_values(sheets, sheet_name)
    if not all_rows:
        print("ERROR: The sheet appears to be empty.")
        sys.exit(1)

    print(f"  Loaded {len(all_rows)} rows × "
          f"{max(len(r) for r in all_rows)} cols")

    # ── Find the header row (contains week-start dates) ───────────────────────
    header_row_idx = detect_header_row(all_rows)
    header = all_rows[header_row_idx]
    print(f"\nHeader detected at row {header_row_idx + 1}: {header[:8]}…")

    # Column 0 (A) = keyword label; columns 1+ = week start dates
    KEYWORD_COL = 0
    week_cols: list[tuple[int, date]] = []  # (0-indexed col, date)

    for col_idx, cell in enumerate(header):
        if col_idx == KEYWORD_COL:
            continue
        d = parse_date(str(cell))
        if d:
            week_cols.append((col_idx, d))
        elif str(cell).strip():
            print(f"  ⚠  Col {col_idx + 1}: couldn't parse '{cell}' as a date — skipped")

    if not week_cols:
        print(
            "ERROR: No parseable date columns found in the header row.\n"
            f"  Header row content: {header}\n"
            "  Make sure week-start dates are in a standard format (e.g. 2026-02-24)."
        )
        sys.exit(1)

    week_cols.sort(key=lambda x: x[1])  # ensure chronological order
    print(
        f"\n  {len(week_cols)} week columns found: "
        f"{week_cols[0][1]}  →  {week_cols[-1][1]}"
    )

    # Full date range across all tracked weeks
    full_start = week_cols[0][1].isoformat()
    full_end   = (week_cols[-1][1] + timedelta(days=6)).isoformat()
    print(f"  Full GSC query range: {full_start} → {full_end}")

    # ── Parse keyword rows ─────────────────────────────────────────────────────
    keyword_rows: list[tuple[int, str]] = []  # (0-indexed row, keyword)
    for row_idx in range(header_row_idx + 1, len(all_rows)):
        row = all_rows[row_idx]
        kw = row[KEYWORD_COL].strip() if row and row[KEYWORD_COL].strip() else ""
        if kw:
            keyword_rows.append((row_idx, kw))

    if not keyword_rows:
        print(
            "ERROR: No keywords found in column A (rows below the header)."
        )
        sys.exit(1)

    print(f"\n  {len(keyword_rows)} keyword(s) to process:")
    for _, kw in keyword_rows:
        print(f"    • {kw}")

    # ── Process each keyword ───────────────────────────────────────────────────
    all_updates: list[dict] = []

    for row_idx, keyword in keyword_rows:
        print(f"\n{'─' * 64}")
        print(f"Keyword: '{keyword}'")

        # Step 1 — find the best US page for this keyword over the full period
        result = find_best_page(gsc, keyword, full_start, full_end)
        if not result:
            print("  ⚠  No US GSC data found for this keyword. Skipping.")
            continue

        best_page, clicks, impressions = result
        print(f"  Best page : {best_page}")
        print(f"  Totals    : {int(clicks):,} clicks  |  {int(impressions):,} impressions  (US, full period)")

        # Step 2 — get position for each week column
        week_found = 0
        for col_idx, week_start_date in week_cols:
            week_start_str = week_start_date.isoformat()
            week_end_str   = (week_start_date + timedelta(days=6)).isoformat()

            pos = get_weekly_position(
                gsc, keyword, best_page, week_start_str, week_end_str
            )

            sheet_row = row_idx + 1         # convert to 1-indexed for Sheets API
            sheet_col = col_idx + 1
            cell_ref  = f"{sheet_name}!{col_to_letter(sheet_col)}{sheet_row}"

            if pos is not None:
                week_found += 1
                print(f"    {week_start_str} → {pos:.1f}")
                if not dry_run:
                    all_updates.append({"range": cell_ref, "values": [[pos]]})
            else:
                print(f"    {week_start_str} → (no data)")

        print(f"  ✓ {week_found}/{len(week_cols)} weeks have data")

    # ── Write all results to the sheet in one batch ────────────────────────────
    print(f"\n{'═' * 64}")
    if dry_run:
        print(f"Dry run complete.  Would write {len(all_updates)} cells to the sheet.")
    elif all_updates:
        print(f"Writing {len(all_updates)} position values to Google Sheets…")
        batch_write(sheets, all_updates)
        print("✅  Sheet updated successfully!")
    else:
        print("No data to write (all keywords had empty GSC results).")


if __name__ == "__main__":
    main()
