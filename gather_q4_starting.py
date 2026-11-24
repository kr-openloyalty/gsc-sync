#!/usr/bin/env python3
"""
Gather Q4 starting positions (one-time baseline, run once at Q4 start).

    python3 gather_q4_starting.py --q3c1 stats-26Q3C1-*.csv --q4 stats-26Q4-*.csv [--out out/q4_starting_positions.json]

GSC baseline: W38 (Sep 14-20) — last complete week before Q4.
  C1 (15 kws) + C2 (10 kws) + C3 (6 kws), US filter, best-page selection.

Chatbeat baseline: average across all dates in the provided CSV files.
  Q3 C1 CSV  → ChatGPT / Claude / AI Overview / Perplexity clusters (GPT/CLAUDE/AI_OVERVIEW/PERPLEXITY)
  Q4 CSV     → ChatGPT 2nd Cluster (GPT, 14 new prompts)

Output: JSON + prints a per-row summary.
Fallback: 100 when no position data exists.

The baseline used by the weekly scorecard lives in q4_history.json; weekly updates: generate_scorecard_q4.py.
"""
import argparse, csv, json, math, os, time
from collections import defaultdict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

from q4_config import (BASELINE_WEEK, C1_KEYWORDS, C2_KEYWORDS, C3_KEYWORDS, GPT2_PROMPTS, GSC_ENDPOINT,
                       LLM_PROMPTS, OL_KEYWORDS, ROOT, SITE, TOKEN_FILE)

API_SLEEP = 0.35
W38_START, W38_END = BASELINE_WEEK


def get_session():
    with open(TOKEN_FILE) as f:
        creds = Credentials.from_authorized_user_info(json.load(f))
    return AuthorizedSession(creds)


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


def load_chatbeat(csv_path, llm_filter):
    """Return dict: {prompt: avg_position} filtering by llm and OL keywords."""
    positions = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["llm"] != llm_filter:
                continue
            if row["keyword"].lower() not in OL_KEYWORDS:
                continue
            try:
                pos = float(row["position"])
                positions[row["prompt"]].append(pos)
            except (ValueError, KeyError):
                pass
    return {p: round(sum(v)/len(v), 1) for p, v in positions.items()}


def fmt(v):
    if v is None:
        return "100"  # fallback
    return f"{v:.1f}".replace(".", ",")


def main():
    ap = argparse.ArgumentParser(description="Gather Q4 starting positions (GSC W38 + Chatbeat baseline).")
    ap.add_argument("--q3c1", required=True, help="Chatbeat export with the 15 'Best loyalty…' prompts")
    ap.add_argument("--q4", required=True, help="Chatbeat export with the 14 ChatGPT 2nd cluster prompts")
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "q4_starting_positions.json"))
    args = ap.parse_args()
    results = {}

    # ── GSC queries ──────────────────────────────────────────────────────────
    print(f"Querying GSC W38 ({W38_START} → {W38_END})")
    session = get_session()

    print(f"\n  C1 ({len(C1_KEYWORDS)} keywords, US best-page):")
    gsc_c1 = {}
    for kw in C1_KEYWORDS:
        pos = get_position_us(session, kw, W38_START, W38_END)
        gsc_c1[kw] = pos
        print(f"    {kw:<42} {f'{pos:.1f}' if pos else '—'}")

    print(f"\n  C2 ({len(C2_KEYWORDS)} keywords, US best-page):")
    gsc_c2 = {}
    for kw in C2_KEYWORDS:
        pos = get_position_us(session, kw, W38_START, W38_END)
        gsc_c2[kw] = pos
        print(f"    {kw:<42} {f'{pos:.1f}' if pos else '—'}")

    print(f"\n  C3 ({len(C3_KEYWORDS)} keywords, US best-page):")
    gsc_c3 = {}
    for kw in C3_KEYWORDS:
        pos = get_position_us(session, kw, W38_START, W38_END)
        gsc_c3[kw] = pos
        print(f"    {kw:<42} {f'{pos:.1f}' if pos else '—'}")

    results["gsc_c1"] = gsc_c1
    results["gsc_c2"] = gsc_c2
    results["gsc_c3"] = gsc_c3

    # ── Chatbeat processing ───────────────────────────────────────────────────
    print("\nProcessing Chatbeat Q3 C1 file (GPT/CLAUDE/AI_OVERVIEW/PERPLEXITY)...")
    chatgpt_pos = load_chatbeat(args.q3c1, "GPT")
    claude_pos  = load_chatbeat(args.q3c1, "CLAUDE")
    aiov_pos    = load_chatbeat(args.q3c1, "AI_OVERVIEW")
    perp_pos    = load_chatbeat(args.q3c1, "PERPLEXITY")

    print(f"  ChatGPT prompts found: {len(chatgpt_pos)}")
    print(f"  Claude  prompts found: {len(claude_pos)}")
    print(f"  AIOverview prompts:    {len(aiov_pos)}")
    print(f"  Perplexity prompts:    {len(perp_pos)}")

    print("\nProcessing Chatbeat Q4 file (GPT for 2nd cluster)...")
    gpt2_pos = load_chatbeat(args.q4, "GPT")
    print(f"  ChatGPT 2nd prompts: {len(gpt2_pos)}")

    results["chatgpt"] = chatgpt_pos
    results["claude"]  = claude_pos
    results["ai_overview"] = aiov_pos
    results["perplexity"] = perp_pos
    results["chatgpt2"] = gpt2_pos

    # ── Build sheet update map ────────────────────────────────────────────────
    # Format: {row_number (1-indexed): starting_position_value}
    # Column B = index 1
    # Row 1 = header
    updates = {}  # row_num -> formatted_value

    def set_row(row_num, val):
        updates[row_num] = fmt(val)

    # C1: rows 4-18
    for i, kw in enumerate(C1_KEYWORDS):
        set_row(4 + i, gsc_c1.get(kw))

    # C2: rows 20-29
    for i, kw in enumerate(C2_KEYWORDS):
        set_row(20 + i, gsc_c2.get(kw))

    # C3: rows 31-36
    for i, kw in enumerate(C3_KEYWORDS):
        set_row(31 + i, gsc_c3.get(kw))

    # ChatGPT: rows 38-52
    for i, prompt in enumerate(LLM_PROMPTS):
        set_row(38 + i, chatgpt_pos.get(prompt))

    # Claude: rows 54-68
    for i, prompt in enumerate(LLM_PROMPTS):
        set_row(54 + i, claude_pos.get(prompt))

    # AI Overview: rows 70-84
    for i, prompt in enumerate(LLM_PROMPTS):
        set_row(70 + i, aiov_pos.get(prompt))

    # Perplexity: rows 86-100
    for i, prompt in enumerate(LLM_PROMPTS):
        set_row(86 + i, perp_pos.get(prompt))

    # ChatGPT 2nd: rows 102-115
    for i, prompt in enumerate(GPT2_PROMPTS):
        set_row(102 + i, gpt2_pos.get(prompt))

    # ── Cluster averages (for header rows) ───────────────────────────────────
    def calc_avg(keyword_dict, keywords):
        vals = [v for k in keywords if (v := keyword_dict.get(k)) is not None]
        return round(sum(vals)/len(vals), 1) if vals else None

    def calc_avg_llm(pos_dict, prompts):
        vals = [v for p in prompts if (v := pos_dict.get(p)) is not None]
        return round(sum(vals)/len(vals), 1) if vals else None

    c1_avg = calc_avg(gsc_c1, C1_KEYWORDS)
    c2_avg = calc_avg(gsc_c2, C2_KEYWORDS)
    c3_avg = calc_avg(gsc_c3, C3_KEYWORDS)
    all_gsc = [gsc_c1.get(k) for k in C1_KEYWORDS] + [gsc_c2.get(k) for k in C2_KEYWORDS]
    all_gsc_vals = [v for v in all_gsc if v is not None]
    gsc_overall = round(sum(all_gsc_vals)/len(all_gsc_vals), 1) if all_gsc_vals else None

    gpt_avg  = calc_avg_llm(chatgpt_pos, LLM_PROMPTS)
    cla_avg  = calc_avg_llm(claude_pos, LLM_PROMPTS)
    aio_avg  = calc_avg_llm(aiov_pos, LLM_PROMPTS)
    per_avg  = calc_avg_llm(perp_pos, LLM_PROMPTS)
    gpt2_avg = calc_avg_llm(gpt2_pos, GPT2_PROMPTS)

    # Set cluster rows
    updates[2]   = fmt(gsc_overall)   # Google Average
    updates[3]   = fmt(c1_avg)        # Cluster 1
    updates[19]  = fmt(c2_avg)        # Cluster 2
    updates[30]  = fmt(c3_avg)        # Cluster 3
    updates[37]  = fmt(gpt_avg)       # ChatGPT Cluster
    updates[53]  = fmt(cla_avg)       # Claude Cluster
    updates[69]  = fmt(aio_avg)       # AI Overview Cluster
    updates[85]  = fmt(per_avg)       # Perplexity Cluster
    updates[101] = fmt(gpt2_avg)      # ChatGPT 2nd Cluster

    # Save results
    out = args.out
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump({"updates": updates, "raw": results}, f, indent=2)
    print(f"\nSaved to {out}")

    # Print summary
    print("\n=== STARTING POSITIONS SUMMARY ===")
    print(f"{'Row':<5} {'Label':<50} {'Value':>8}")
    print("-"*65)

    rows_labels = {
        2: "Google Average", 3: "Cluster 1 (Google)",
        30: "Cluster 3 (Google)", 37: "ChatGPT Cluster",
        53: "Claude Cluster", 69: "AI Overview Cluster",
        85: "Perplexity Cluster", 101: "ChatGPT 2nd Cluster",
    }
    # Also add C1/C2 keywords
    for i, kw in enumerate(C1_KEYWORDS): rows_labels[4+i] = kw
    for i, kw in enumerate(C2_KEYWORDS): rows_labels[20+i] = kw
    for i, kw in enumerate(C3_KEYWORDS): rows_labels[31+i] = kw

    for row_num in sorted(updates.keys()):
        label = rows_labels.get(row_num, f"Row {row_num}")
        print(f"{row_num:<5} {label:<50} {updates[row_num]:>8}")

    return updates


if __name__ == "__main__":
    main()
