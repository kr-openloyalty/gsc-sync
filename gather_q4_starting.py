#!/usr/bin/env python3
"""
Gather Q4 starting positions (one-time baseline, run once at Q4 start).

GSC baseline: W38 (Sep 14-20) — last complete week before Q4.
  C1 (15 kws) + C2 (10 kws) + C3 (6 kws), US filter, best-page selection.

Chatbeat baseline: average across all dates in the provided CSV files.
  Q3 C1 CSV  → ChatGPT / Claude / AI Overview / Perplexity clusters (GPT/CLAUDE/AI_OVERVIEW/PERPLEXITY)
  Q4 CSV     → ChatGPT 2nd Cluster (GPT, 14 new prompts)

Output: JSON + prints a per-row summary.
Fallback: 100 when no position data exists.

For future Q4 WEEKLY updates, see generate_scorecard_q4.py (to be created).
To re-run with updated Chatbeat files, update CB_Q3_FILE and CB_Q4_FILE below.
"""
import csv, json, math, time, warnings
from collections import defaultdict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession

TOKEN_FILE   = "/home/user/gsc-sync/token.json"
SITE         = "sc-domain:openloyalty.io"
GSC_ENDPOINT = "https://www.googleapis.com/webmasters/v3"
API_SLEEP    = 0.35
OL_KEYWORDS  = {"open loyalty", "openloyalty"}

# W38 as baseline (last complete week before Q4)
W38_START = "2026-09-14"
W38_END   = "2026-09-20"

# Q4 Sheet keywords
C1_KEYWORDS = [
    "loyalty platform",
    "loyalty program software",
    "customer loyalty software",
    "loyalty software",
    "customer loyalty program software",
    "customer loyalty platform",
    "loyalty system",
    "loyalty card system",
    "voucher management system",
    "coupon management software",
    "loyalty program saas",
    "loyalty rewards management system",
    "best customer loyalty software",
    "loyalty program api",
    "loyalty management software",
]

C2_KEYWORDS = [
    "loyalty points",
    "loyalty program cost",
    "loyalty program app",
    "white label loyalty",
    "b2b loyalty programs",
    "b2b loyalty program software",
    "ecommerce loyalty program",
    "retail loyalty",
    "omnichannel loyalty program",
    "loyalty gamification",
]

C3_KEYWORDS = [
    "yotpo alternatives",
    "smile.io alternatives",
    "voucherify competitors",
    "loyaltylion alternatives",
    "talon.one alternatives",
    "antavo alternatives",
]

LLM_PROMPTS = [
    "Best customer loyalty software",
    "Best loyalty program software for enterprise",
    "Best white label loyalty platform",
    "Best B2B loyalty program software",
    "Best API-first loyalty platform",
    "Best loyalty platform",
    "Best loyalty program software",
    "Best customer loyalty program software",
    "Best loyalty system",
    "Best loyalty software",
    "Best customer loyalty platform",
    "Best loyalty card system",
    "Best coupon management software",
    "Best voucher software",
    "Best loyalty program saas",
]

GPT2_PROMPTS = [
    "Alternatives to Salesforce Loyalty Management",
    "Antavo alternatives",
    "Headless loyalty platform",
    "How much does loyalty program software cost",
    "Is it cheaper to build a loyalty program in-house or buy one",
    "Loyalty program for restaurants",
    "Loyalty program pricing models explained",
    "Loyalty program software for ecommerce",
    "LoyaltyLion alternatives",
    "Omnichannel loyalty platform",
    "Talon.One alternatives",
    "Voucherify alternatives",
    "What are the best alternatives to Smile.io",
    "Yotpo alternatives",
]

CB_Q3_FILE = "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/11ec0c8b-stats-26Q3C1-20260827-20260925_1.csv"
CB_Q4_FILE = "/root/.claude/uploads/429803ff-2598-58d6-93c1-b17332904b6d/920fc14d-stats-26Q4-20260921-20260925.csv"


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
    with open(csv_path, newline="") as fh:
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
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
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
    chatgpt_pos = load_chatbeat(CB_Q3_FILE, "GPT")
    claude_pos  = load_chatbeat(CB_Q3_FILE, "CLAUDE")
    aiov_pos    = load_chatbeat(CB_Q3_FILE, "AI_OVERVIEW")
    perp_pos    = load_chatbeat(CB_Q3_FILE, "PERPLEXITY")

    print(f"  ChatGPT prompts found: {len(chatgpt_pos)}")
    print(f"  Claude  prompts found: {len(claude_pos)}")
    print(f"  AIOverview prompts:    {len(aiov_pos)}")
    print(f"  Perplexity prompts:    {len(perp_pos)}")

    print("\nProcessing Chatbeat Q4 file (GPT for 2nd cluster)...")
    gpt2_pos = load_chatbeat(CB_Q4_FILE, "GPT")
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
    out = "/tmp/claude-0/-home-user-gsc-sync/429803ff-2598-58d6-93c1-b17332904b6d/scratchpad/q4_starting_positions.json"
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
