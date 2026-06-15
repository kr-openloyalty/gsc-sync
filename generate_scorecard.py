#!/usr/bin/env python3
"""
Generate updated scorecard CSV (W9–W24).

- W9–W22: uses cached data from the existing sheet
- W23–W24: fresh GSC queries (W23 now complete; W24 is new)
- Chatbeat: all 4 CSV files processed for all weeks

Output: semicolon-delimited CSV with comma decimal separators (European format).
"""

import csv
import math
import time
import warnings
from collections import defaultdict
from datetime import date, datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

# ---------------------------------------------------------------------------
TOKEN_FILE   = "token.json"
SITE         = "sc-domain:openloyalty.io"
GSC_ENDPOINT = "https://www.googleapis.com/webmasters/v3"
COUNTRY      = "usa"
API_SLEEP    = 0.35
OL_KEYWORDS  = {"open loyalty", "openloyalty"}
LLM_FILTER   = "GPT"

# ---------------------------------------------------------------------------
# Weeks: W9–W24  (ISO Mon–Sun)
# ---------------------------------------------------------------------------
WEEKS = [
    ("W9",  "2026-02-23", "2026-03-01"),
    ("W10", "2026-03-02", "2026-03-08"),
    ("W11", "2026-03-09", "2026-03-15"),
    ("W12", "2026-03-16", "2026-03-22"),
    ("W13", "2026-03-23", "2026-03-29"),
    ("W14", "2026-03-30", "2026-04-05"),
    ("W15", "2026-04-06", "2026-04-12"),
    ("W16", "2026-04-13", "2026-04-19"),
    ("W17", "2026-04-20", "2026-04-26"),
    ("W18", "2026-04-27", "2026-05-03"),
    ("W19", "2026-05-04", "2026-05-10"),
    ("W20", "2026-05-11", "2026-05-17"),
    ("W21", "2026-05-18", "2026-05-24"),
    ("W22", "2026-05-25", "2026-05-31"),
    ("W23", "2026-06-01", "2026-06-07"),
    ("W24", "2026-06-08", "2026-06-14"),
]
N_WEEKS = len(WEEKS)
CACHED_UP_TO = 14  # W9–W22 cached (indices 0–13); re-query W23(14) and W24(15)

# ---------------------------------------------------------------------------
# Cached GSC data  W9–W22  (index 0–13, None = no data → will forward-fill)
# ---------------------------------------------------------------------------
GSC_C1 = {
    "loyalty program software":
        [3.2,3.2,2.9,2.3,2.0,2.0,2.2,2.3,1.9,2.5,2.7,2.7,4.1,4.1],
    "customer loyalty program software":
        [7.7,3.3,6.2,4.2,2.4,2.3,2.8,3.8,2.3,6.2,6.4,3.4,5.6,5.2],
    "loyalty software":
        [6.2,3.4,5.8,3.6,2.0,1.6,2.1,2.6,1.6,1.6,1.6,2.0,4.1,3.1],
    "best loyalty program software":
        [1.0,1.4,1.0,2.6,2.6,3.3,2.9,1.6,3.7,3.9,3.5,1.2,1.7,1.5],
    "enterprise loyalty software":
        [3.2,1.8,2.5,2.5,2.8,4.5,3.0,2.7,1.7,4.1,2.5,2.2,3.2,3.4],
    "best customer loyalty program software":
        [1.4,1.2,1.1,2.3,2.0,2.5,2.7,2.4,2.2,2.3,2.1,2.4,4.1,7.3],
    "best loyalty software":
        [1.0,1.5,1.0,3.0,3.3,3.6,3.3,1.8,3.2,4.2,2.6,1.1,4.1,3.4],
    "loyalty software for business":
        [7.2,3.0,5.5,4.6,4.0,5.5,4.0,4.0,10.0,8.0,6.0,6.0,6.0,7.0],
}

GSC_C2 = {
    "customer loyalty software":
        [5.2,2.5,4.7,3.3,2.2,2.0,2.7,3.5,2.2,2.2,2.2,3.5,3.0,3.5],
    "loyalty management software":
        [9.4,8.0,11.0,5.1,5.0,3.8,4.3,3.1,2.7,2.7,3.5,3.1,3.3,3.1],
    "loyalty program management software":
        [9.7,6.2,9.4,2.9,2.9,3.6,3.6,2.5,2.2,2.4,2.5,2.6,2.4,2.8],
    "loyalty management system":
        [10.7,10.9,9.6,7.9,4.9,6.6,5.1,5.9,7.8,3.4,3.8,5.0,6.7,5.5],
    "gamification software":
        [2.9,21.0,23.0,14.3,12.2,17.8,20.6,24.0,25.5,25.4,27.4,25.7,33.9,32.0],
    "retail loyalty software":
        [4.1,3.7,4.5,1.1,1.7,2.9,2.6,2.6,1.3,3.5,3.2,2.2,1.6,2.5],
    "loyalty points software":
        [3.4,3.6,3.7,4.3,4.4,4.6,4.5,4.3,4.4,5.3,5.0,4.7,4.5,5.5],
}

# ---------------------------------------------------------------------------
# GSC helpers
# ---------------------------------------------------------------------------
def get_gsc_session():
    import json
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    s = AuthorizedSession(creds)
    s.verify = False
    return s

def gsc_post(session, payload, retries=4):
    for attempt in range(retries):
        try:
            r = session.post(f"{GSC_ENDPOINT}/sites/{SITE}/searchAnalytics/query", json=payload)
            r.raise_for_status()
            return r.json().get("rows", [])
        except Exception as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"      retry {attempt+1} after {wait}s: {exc}")
            time.sleep(wait)
    return []

def get_week_position(session, keyword, start, end):
    rows = gsc_post(session, {
        "startDate": start, "endDate": end,
        "dimensions": ["page"],
        "dimensionFilterGroups": [{"filters": [
            {"dimension": "query",   "operator": "equals", "expression": keyword},
            {"dimension": "country", "operator": "equals", "expression": COUNTRY},
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

# ---------------------------------------------------------------------------
# Chatbeat helpers
# ---------------------------------------------------------------------------
def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())

def load_chatbeat_weekly(csv_files):
    scrape_days = defaultdict(set)
    ol_pos      = defaultdict(lambda: defaultdict(list))
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
    ol_daily = {
        p: {d: sum(v)/len(v) for d, v in days.items()}
        for p, days in ol_pos.items()
    }
    filled = {}
    for prompt in scrape_days:
        sorted_days = sorted(scrape_days[prompt])
        last = None
        result = {}
        for d in sorted_days:
            if d in ol_daily.get(prompt, {}):
                last = ol_daily[prompt][d]
                result[d] = last
            elif last is not None:
                result[d] = last
        filled[prompt] = result
    weekly = {}
    for prompt, day_map in filled.items():
        by_week = defaultdict(list)
        for d_str, pos in day_map.items():
            ws = week_start(datetime.strptime(d_str, "%Y-%m-%d").date())
            by_week[ws].append(pos)
        weekly[prompt] = {ws: round(sum(v)/len(v), 1) for ws, v in by_week.items()}
    return weekly

# ---------------------------------------------------------------------------
# Build full data grid
# ---------------------------------------------------------------------------
def forward_fill(values):
    last = None
    result = []
    for v in values:
        if v is not None:
            last = v
            result.append(v)
        elif last is not None:
            result.append(last)
        else:
            result.append(None)
    return result

def build_gsc_row(cached_14, fresh_2):
    """Combine 14 cached values + 2 fresh values, forward-fill."""
    row = list(cached_14) + list(fresh_2)
    return forward_fill(row)

def fmt(v):
    if v is None:
        return ""
    s = f"{v:.1f}"
    return s.replace(".", ",")

def cluster_avg(rows_dict, week_idx):
    vals = [rows_dict[k][week_idx] for k in rows_dict if rows_dict[k][week_idx] is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    # -- GSC: query W23 + W24 for all keywords --
    session = get_gsc_session()
    all_gsc_keywords = list(GSC_C1.keys()) + list(GSC_C2.keys())
    fresh = {kw: [] for kw in all_gsc_keywords}

    requery_weeks = WEEKS[CACHED_UP_TO:]  # W23, W24
    print(f"Querying GSC for {len(requery_weeks)} weeks × {len(all_gsc_keywords)} keywords...")
    for label, start, end in requery_weeks:
        print(f"  {label} ({start} → {end})")
        for kw in all_gsc_keywords:
            pos = get_week_position(session, kw, start, end)
            fresh[kw].append(pos)
            tag = f"{pos:.1f}" if pos is not None else "—"
            print(f"    {kw[:45]:<45} {tag}")

    # Build full GSC rows (W9–W24)
    gsc_c1_rows = {}
    for kw, cached in GSC_C1.items():
        gsc_c1_rows[kw] = build_gsc_row(cached, fresh[kw])

    gsc_c2_rows = {}
    for kw, cached in GSC_C2.items():
        gsc_c2_rows[kw] = build_gsc_row(cached, fresh[kw])

    # -- Chatbeat --
    cb_files = [
        "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/dbbfb45e-stats26Q1_Open_Loyalty2026030720260607.csv",
        "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/f7e1880b-stats26Q1_Open_Loyalty2026031520260615.csv",
        "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/03899b18-stats26Q22026030720260607.csv",
        "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/bef4b2a7-stats26Q22026031520260615.csv",
    ]
    print("\nProcessing Chatbeat files...")
    cb_weekly = load_chatbeat_weekly(cb_files)
    print(f"  Prompts found: {sorted(cb_weekly.keys())}")

    CB_C1_ORDER = [
        "best loyalty software",
        "best enterprise loyalty software",
        "best customer loyalty program software",
        "best loyalty program software",
        "best loyalty software for business",
    ]
    CB_C2_ORDER = [
        "loyalty management system",
        "loyalty points software",
        "loyalty program management software",
        "loyalty management software",
        "customer loyalty software",
        "retail loyalty software",
        "gamification software",
    ]

    def cb_row(prompt):
        week_map = cb_weekly.get(prompt, {})
        raw = []
        for _, start, _ in WEEKS:
            ws = datetime.strptime(start, "%Y-%m-%d").date()
            raw.append(week_map.get(ws))
        return forward_fill(raw)

    cb_c1_rows = {p: cb_row(p) for p in CB_C1_ORDER}
    cb_c2_rows = {p: cb_row(p) for p in CB_C2_ORDER}

    # -- Build CSV --
    week_labels = [w[0] for w in WEEKS]
    start_dates = [w[1] for w in WEEKS]
    end_dates   = [w[2] for w in WEEKS]

    SEP = ";"

    def row_to_csv(label, owner, values):
        cells = [label, owner] + [fmt(v) for v in values]
        return SEP.join(cells)

    def avg_row(label, rows_dict):
        avgs = [cluster_avg(rows_dict, i) for i in range(N_WEEKS)]
        return row_to_csv(label, "", avgs)

    lines = []

    # Header rows
    lines.append(SEP.join(["Marketing team", "Owner"] + week_labels))
    lines.append(SEP.join(["Start week", ""] + start_dates))
    lines.append(SEP.join(["End week", ""]   + end_dates))

    # Google section
    lines.append(avg_row("Google position for Cluster 1 & 2", {**gsc_c1_rows, **gsc_c2_rows}))
    lines.append(avg_row("Google position for Cluster 1", gsc_c1_rows))
    for kw in GSC_C1.keys():
        lines.append(row_to_csv(kw, "", gsc_c1_rows[kw]))
    lines.append(avg_row("Google position for Cluster 2", gsc_c2_rows))
    for kw in GSC_C2.keys():
        lines.append(row_to_csv(kw, "", gsc_c2_rows[kw]))

    # ChatGPT section
    lines.append(avg_row("ChatGPT position for Cluster 1 & 2", {**cb_c1_rows, **cb_c2_rows}))
    lines.append(avg_row("ChatGPT position for Cluster 1", cb_c1_rows))
    for p in CB_C1_ORDER:
        lines.append(row_to_csv(p, "", cb_c1_rows[p]))
    lines.append(avg_row("ChatGPT position for Cluster 2", cb_c2_rows))
    for p in CB_C2_ORDER:
        lines.append(row_to_csv(p, "", cb_c2_rows[p]))

    out = "/tmp/scorecard_w24.csv"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nCSV written → {out}")
    print(f"Rows: {len(lines)}, Weeks: {N_WEEKS}")

if __name__ == "__main__":
    main()
