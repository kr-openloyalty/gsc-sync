#!/usr/bin/env python3
"""
sync_chatbeat_to_sheets.py

Reads Chatbeat CSV exports, calculates weekly average ChatGPT positions for
Open Loyalty, and back-fills them into the ChatGPT section of the scorecard.

Usage:
  python3 sync_chatbeat_to_sheets.py <file1.csv> [<file2.csv> ...]
  python3 sync_chatbeat_to_sheets.py --dry-run <file1.csv> [...]

Authentication:
  Uses service_account.json for Sheets (same as sync_gsc_to_sheets.py).
  Share the spreadsheet with the service account email.

CSV format (Chatbeat export):
  date,prompt,llm,keyword,position,brand_score,share_of_voice

Filters applied:
  - llm == 'GPT'  (ChatGPT only)
  - keyword in {'open loyalty', 'openloyalty'}

Logic per prompt row:
  1. Collect daily GPT positions for the prompt from all supplied CSVs.
  2. Group by ISO week (Mon–Sun).
  3. Average positions per week, rounded to 1 decimal.
  4. Forward-fill: if a week has no data, carry the previous week's value.
  5. Write into the matching row in the ChatGPT section of the sheet.

Sheet layout (auto-detected):
  - Row 1 : week labels (W14, W15, …)
  - Row 2 : "Start week" dates  ← used for week matching
  - Row 3 : "End week" dates    ← used for week matching
  - Data rows whose col-A starts with "ChatGPT position for" are cluster
    averages (formula rows) — skipped.
  - The ChatGPT section begins at the row labelled
    "ChatGPT position for Cluster 1 & 2".  Only rows at or below that
    marker are written; duplicate keyword names in the Google section
    above are never touched.
"""

import csv
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

import gspread
from google.oauth2 import service_account

# ── Configuration ──────────────────────────────────────────────────────────────

SERVICE_ACCOUNT_FILE = "service_account.json"
SPREADSHEET_ID       = "1-93tOhuhxSqYwl8bLfzXzwj0JgoQuVqbD9VJNvcymbg"

OL_KEYWORDS  = {"open loyalty", "openloyalty"}
LLM_FILTER   = "GPT"

CHATGPT_SECTION_MARKER = "ChatGPT position for Cluster 1 & 2"
SKIP_ROW_PREFIX        = "ChatGPT position"   # formula/cluster-average rows


# ── Date helpers ───────────────────────────────────────────────────────────────

_FMTS = [
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y",
    "%Y/%m/%d", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y",
    "%d %B %Y", "%d %b %Y",
]


def parse_date(s: str) -> date | None:
    s = s.strip()
    for fmt in _FMTS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def week_start(d: date) -> date:
    """Monday of the ISO week containing d."""
    return d - timedelta(days=d.weekday())


# ── Sheets auth ────────────────────────────────────────────────────────────────


def get_worksheet() -> gspread.Worksheet:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.get_worksheet(0)


# ── CSV processing ─────────────────────────────────────────────────────────────


def load_weekly_averages(csv_files: list[str]) -> dict[str, dict[date, float]]:
    """
    Returns {prompt: {week_start_date: avg_position}} for GPT + Open Loyalty rows.

    Strategy mirrors the GSC forward-fill approach:
      1. Track every scrape day for each prompt (all brands, not just OL).
      2. Record OL's position on days it appeared.
      3. Forward-fill OL's last known position onto scrape days where it was
         absent — same logic as GSC's "carry previous week" rule, but at
         day granularity within the CSV.
      4. Average all scrape-day positions (filled + real) per week.
    """
    # All GPT scrape days per prompt: {prompt: {date_str}}
    scrape_days: dict[str, set[str]] = defaultdict(set)
    # OL positions on days it appeared: {prompt: {date_str: avg_position}}
    ol_pos: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(list))

    for path in csv_files:
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                if row["llm"] != LLM_FILTER:
                    continue
                prompt = row["prompt"]
                d      = row["date"][:10]
                scrape_days[prompt].add(d)
                if row["keyword"].lower() in OL_KEYWORDS:
                    ol_pos[prompt][d].append(float(row["position"]))

    # Collapse multiple same-day OL readings to a daily average
    ol_daily: dict[str, dict[str, float]] = {
        prompt: {d: sum(v) / len(v) for d, v in days.items()}
        for prompt, days in ol_pos.items()
    }

    # Forward-fill OL position across all scrape days (chronological order)
    filled: dict[str, dict[str, float]] = {}
    for prompt in scrape_days:
        sorted_days = sorted(scrape_days[prompt])
        last_known: float | None = None
        result: dict[str, float] = {}
        for d in sorted_days:
            if d in ol_daily.get(prompt, {}):
                last_known = ol_daily[prompt][d]
                result[d]  = last_known
            elif last_known is not None:
                result[d] = last_known   # carry last known position
            # if no OL position seen yet, day stays absent (no entry)
        filled[prompt] = result

    # Aggregate filled daily values → weekly averages
    weekly: dict[str, dict[date, float]] = {}
    for prompt, day_map in filled.items():
        by_week: dict[date, list[float]] = defaultdict(list)
        for d_str, pos in day_map.items():
            ws = week_start(datetime.strptime(d_str, "%Y-%m-%d").date())
            by_week[ws].append(pos)
        weekly[prompt] = {
            ws: round(sum(vals) / len(vals), 1)
            for ws, vals in by_week.items()
        }

    return weekly


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    csv_files = [a for a in args if not a.startswith("--")]

    if not csv_files:
        print("Usage: python3 sync_chatbeat_to_sheets.py [--dry-run] <file1.csv> [...]")
        sys.exit(1)

    if dry_run:
        print("🔍  DRY RUN — no changes will be written to the sheet.\n")

    # ── Load and aggregate CSV data ────────────────────────────────────────────
    print(f"Loading {len(csv_files)} CSV file(s)…")
    weekly_avgs = load_weekly_averages(csv_files)
    print(f"  Found data for {len(weekly_avgs)} prompts (GPT, Open Loyalty)\n")

    # ── Connect to Sheets ──────────────────────────────────────────────────────
    print("Connecting to Google Sheets (service account)…")
    ws = get_worksheet()
    print(f"  Opened: '{ws.spreadsheet.title}' → sheet '{ws.title}'")

    all_values = ws.get_all_values()
    print(f"  Loaded {len(all_values)} rows × {max(len(r) for r in all_values)} cols\n")

    # ── Locate Start/End week rows ─────────────────────────────────────────────
    start_row_idx = end_row_idx = None
    for i, row in enumerate(all_values):
        label = row[0].strip() if row else ""
        if label == "Start week":
            start_row_idx = i
        elif label == "End week":
            end_row_idx = i
        if start_row_idx is not None and end_row_idx is not None:
            break

    if start_row_idx is None or end_row_idx is None:
        print("ERROR: Could not find 'Start week' or 'End week' rows.")
        sys.exit(1)

    start_row = all_values[start_row_idx]
    end_row   = all_values[end_row_idx]

    today = date.today()

    # Build week columns: (col_0idx, week_start_date, week_end_date)
    week_cols: list[tuple[int, date, date]] = []
    for col_idx in range(2, len(start_row)):
        s_raw = start_row[col_idx] if col_idx < len(start_row) else ""
        e_raw = end_row[col_idx]   if col_idx < len(end_row)   else ""
        s = parse_date(s_raw)
        e = parse_date(e_raw)
        if s and e and s <= today:
            week_cols.append((col_idx, s, e))

    if not week_cols:
        print("ERROR: No past/current week columns found.")
        sys.exit(1)

    print(f"Week columns ({len(week_cols)}):")
    for col_idx, s, e in week_cols:
        status = "(current)" if s <= today <= e else ""
        print(f"  col {col_idx + 1:2d}  {s}  →  {e}  {status}")

    # ── Locate the ChatGPT section ─────────────────────────────────────────────
    chatgpt_start_idx = None
    for i, row in enumerate(all_values):
        if (row[0].strip() if row else "") == CHATGPT_SECTION_MARKER:
            chatgpt_start_idx = i
            break

    if chatgpt_start_idx is None:
        print(f"ERROR: Could not find ChatGPT section marker '{CHATGPT_SECTION_MARKER}'.")
        sys.exit(1)

    print(f"\nChatGPT section starts at sheet row {chatgpt_start_idx + 1}")

    # Build {prompt_label: row_0idx} for keyword rows in the ChatGPT section
    chatgpt_rows: dict[str, int] = {}
    for row_idx in range(chatgpt_start_idx, len(all_values)):
        label = all_values[row_idx][0].strip() if all_values[row_idx] else ""
        if not label:
            continue
        if label.startswith(SKIP_ROW_PREFIX):
            continue
        chatgpt_rows[label] = row_idx

    print(f"ChatGPT keyword rows ({len(chatgpt_rows)}):")
    for label in chatgpt_rows:
        print(f"  • {label}")

    # ── Process each prompt row ────────────────────────────────────────────────
    updates: dict[tuple[int, int], float] = {}

    for label, row_idx in chatgpt_rows.items():
        avg_data = weekly_avgs.get(label)
        if avg_data is None:
            print(f"\n  ⚠  No CSV data for '{label}' — skipping")
            continue

        print(f"\n{'─' * 64}")
        print(f"Prompt: '{label}'")

        # Collect position for each week column
        # (col_idx, week_start, week_end, pos_or_None)
        week_results: list[tuple[int, date, date, float | None]] = []
        for col_idx, ws_date, we_date in week_cols:
            pos = avg_data.get(ws_date)
            week_results.append((col_idx, ws_date, we_date, pos))

        # Forward-fill: carry last known value into blank weeks
        last_known: float | None = None
        for i, (col_idx, ws_date, we_date, pos) in enumerate(week_results):
            if pos is not None:
                last_known = pos
            elif last_known is not None:
                week_results[i] = (col_idx, ws_date, we_date, last_known)

        found = filled = 0
        for col_idx, ws_date, we_date, pos in week_results:
            orig_pos = avg_data.get(ws_date)
            if pos is not None:
                found += 1
                updates[(row_idx + 1, col_idx + 1)] = pos   # 1-indexed for gspread
                if orig_pos is None:
                    filled += 1
                    print(f"    {ws_date}  :  {pos:.1f}  [↑ forward-filled]")
                else:
                    print(f"    {ws_date}  :  {pos:.1f}")
            else:
                print(f"    {ws_date}  :  (no data)")

        fill_note = f"  ({filled} forward-filled)" if filled else ""
        print(f"  ✓ {found}/{len(week_cols)} weeks have data{fill_note}")

    # ── Write to sheet ─────────────────────────────────────────────────────────
    print(f"\n{'═' * 64}")
    if not updates:
        print("No data to write.")
        return

    if dry_run:
        print(f"Dry run complete. Would write {len(updates)} position values.")
        return

    print(f"Writing {len(updates)} position values to Google Sheets…")
    cell_list = [
        gspread.Cell(sheet_row, sheet_col, pos)
        for (sheet_row, sheet_col), pos in updates.items()
    ]
    ws.update_cells(cell_list, value_input_option="RAW")
    print("✅  Sheet updated successfully!")


if __name__ == "__main__":
    main()
