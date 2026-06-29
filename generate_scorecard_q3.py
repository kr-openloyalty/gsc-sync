#!/usr/bin/env python3
"""
Generate Q3 scorecard CSV (W27–W39).

GSC Cluster 1: US-only positions (country=usa)
GSC Cluster 2: Global positions (no country filter)
Chatbeat: Q3 CSV files

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
API_SLEEP    = 0.35
OL_KEYWORDS  = {"open loyalty", "openloyalty"}
LLM_FILTER   = "GPT"

# ---------------------------------------------------------------------------
# Q3 Weeks: W27–W39  (ISO Mon–Sun)
# ---------------------------------------------------------------------------
WEEKS = [
    ("W27", "2026-06-29", "2026-07-05"),
    ("W28", "2026-07-06", "2026-07-12"),
    ("W29", "2026-07-13", "2026-07-19"),
    ("W30", "2026-07-20", "2026-07-26"),
    ("W31", "2026-07-27", "2026-08-02"),
    ("W32", "2026-08-03", "2026-08-09"),
    ("W33", "2026-08-10", "2026-08-16"),
    ("W34", "2026-08-17", "2026-08-23"),
    ("W35", "2026-08-24", "2026-08-30"),
    ("W36", "2026-08-31", "2026-09-06"),
    ("W37", "2026-09-07", "2026-09-13"),
    ("W38", "2026-09-14", "2026-09-20"),
    ("W39", "2026-09-21", "2026-09-27"),
]
N_WEEKS = len(WEEKS)

# ---------------------------------------------------------------------------
# Q3 Keyword sets
# ---------------------------------------------------------------------------

# Cluster 1: US positions (tracked via country=usa filter)
GSC_C1 = [
    "customer loyalty software",
    "best customer loyalty software",
    "loyalty program software",
    "customer loyalty program software",
    "customer loyalty platform",
    "loyalty system",
    "loyalty program api",
    "loyalty software",
    "loyalty program saas",
    "loyalty card system",
    "voucher management system",
    "loyalty rewards management system",
    "coupon management software",
]

# Cluster 2: Global positions (new ranking keywords, no country filter)
GSC_C2 = [
    "luxury brand loyalty programs",
    "fashion loyalty programs",
    "beauty loyalty programs",
    "retail gamification",
    "gift card software",
    "best rewards programs",
    "how to calculate roi for loyalty programs",
    "ecommerce loyalty platform",
    "card linked loyalty programs",
    "loyalty program best practices",
    "b2b loyalty programs",
]

# ChatGPT prompts (Chatbeat)
CB_ORDER = [
    "Best customer loyalty software",
    "Best loyalty program software",
    "Best customer loyalty program software",
    "Best customer loyalty platform",
    "Best loyalty system",
    "Best loyalty program api",
    "Best loyalty software",
    "Best loyalty program saas",
    "Best loyalty card system",
    "Best voucher software",
    "Best loyalty rewards management system",
    "Best coupon management software",
]

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


def get_position_us(session, keyword, start, end):
    """US-only position using best-page selection (Cluster 1)."""
    rows = gsc_post(session, {
        "startDate": start, "endDate": end,
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


def get_position_global(session, keyword, start, end):
    """Global position (Cluster 2)."""
    rows = gsc_post(session, {
        "startDate": start, "endDate": end,
        "dimensions": ["query"],
        "dimensionFilterGroups": [{"filters": [
            {"dimension": "query", "operator": "equals", "expression": keyword},
        ]}],
        "rowLimit": 1,
    })
    time.sleep(API_SLEEP)
    if not rows:
        return None
    return math.floor(rows[0]["position"] * 10) / 10


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
        p: {d: sum(v) / len(v) for d, v in days.items()}
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
        weekly[prompt] = {ws: round(sum(v) / len(v), 1) for ws, v in by_week.items()}
    return weekly


# ---------------------------------------------------------------------------
# Formatting helpers
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


def fmt(v):
    if v is None:
        return ""
    return f"{v:.1f}".replace(".", ",")


def cluster_avg(rows_list, week_idx):
    vals = [row[week_idx] for row in rows_list if row[week_idx] is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    today = date.today()

    session = get_gsc_session()

    # Only query weeks that have started
    active_weeks = [(lbl, s, e) for lbl, s, e in WEEKS
                    if datetime.strptime(s, "%Y-%m-%d").date() <= today]

    # ── GSC Cluster 1 (US) ──────────────────────────────────────────────────
    print(f"Querying GSC Cluster 1 (US) — {len(active_weeks)} week(s) × {len(GSC_C1)} keywords")
    c1_data = {kw: [] for kw in GSC_C1}
    for lbl, s, e in active_weeks:
        print(f"  {lbl} ({s} → {e})")
        for kw in GSC_C1:
            pos = get_position_us(session, kw, s, e)
            c1_data[kw].append(pos)
            print(f"    {'US'} {kw[:42]:<42} {f'{pos:.1f}' if pos else '—'}")

    # ── GSC Cluster 2 (global) ───────────────────────────────────────────────
    print(f"\nQuerying GSC Cluster 2 (global) — {len(active_weeks)} week(s) × {len(GSC_C2)} keywords")
    c2_data = {kw: [] for kw in GSC_C2}
    for lbl, s, e in active_weeks:
        print(f"  {lbl} ({s} → {e})")
        for kw in GSC_C2:
            pos = get_position_global(session, kw, s, e)
            c2_data[kw].append(pos)
            print(f"    {'GL'} {kw[:42]:<42} {f'{pos:.1f}' if pos else '—'}")

    # Pad remaining (future) weeks with None
    future = N_WEEKS - len(active_weeks)
    for kw in GSC_C1:
        c1_data[kw] = forward_fill(c1_data[kw]) + [None] * future
    for kw in GSC_C2:
        c2_data[kw] = forward_fill(c2_data[kw]) + [None] * future

    # ── Chatbeat ─────────────────────────────────────────────────────────────
    cb_files = [
        "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/c4b43ccc-stats26Q3C12026062520260629.csv",
    ]
    print("\nProcessing Chatbeat files...")
    cb_weekly = load_chatbeat_weekly(cb_files)
    print(f"  Prompts found: {sorted(cb_weekly.keys())}")

    def cb_row(prompt):
        week_map = cb_weekly.get(prompt, {})
        raw = []
        for _, s, _ in WEEKS:
            ws = datetime.strptime(s, "%Y-%m-%d").date()
            raw.append(week_map.get(ws))
        return forward_fill(raw)

    cb_rows = {p: cb_row(p) for p in CB_ORDER}

    # ── Build CSV ─────────────────────────────────────────────────────────────
    SEP = ";"
    week_labels = [w[0] for w in WEEKS]
    start_dates = [w[1] for w in WEEKS]
    end_dates   = [w[2] for w in WEEKS]

    def row_csv(label, owner, values):
        return SEP.join([label, owner] + [fmt(v) for v in values])

    def avg_csv(label, rows_list):
        avgs = [cluster_avg(rows_list, i) for i in range(N_WEEKS)]
        return row_csv(label, "", avgs)

    lines = []
    lines.append(SEP.join(["Marketing team", "Owner"] + week_labels))
    lines.append(SEP.join(["Start week", ""] + start_dates))
    lines.append(SEP.join(["End week", ""]   + end_dates))

    # Google section
    all_gsc = list(c1_data.values()) + list(c2_data.values())
    lines.append(avg_csv("Google position for Cluster 1 & 2", all_gsc))
    lines.append(avg_csv("Google position for Cluster 1", list(c1_data.values())))
    for kw in GSC_C1:
        lines.append(row_csv(kw, "", c1_data[kw]))
    lines.append(avg_csv("Google position for Cluster 2", list(c2_data.values())))
    for kw in GSC_C2:
        lines.append(row_csv(kw, "", c2_data[kw]))

    # ChatGPT section
    lines.append(avg_csv("ChatGPT position for all prompts", list(cb_rows.values())))
    for p in CB_ORDER:
        lines.append(row_csv(p, "", cb_rows[p]))

    out = "/tmp/scorecard_q3_w27.csv"
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nCSV written → {out}")
    print(f"Rows: {len(lines)}, Weeks: {N_WEEKS} ({len(active_weeks)} active)")


if __name__ == "__main__":
    main()
