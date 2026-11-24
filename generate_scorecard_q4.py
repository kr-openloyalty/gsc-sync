#!/usr/bin/env python3
"""
Weekly Q4 2026 scorecard: GSC positions + Chatbeat (LLM) positions, W39 onwards.

    python3 generate_scorecard_q4.py --q3c1 stats-26Q3C1-*.csv --q4 stats-26Q4-*.csv
    python3 generate_scorecard_q4.py ... --comments out/comments_2026-11-28.json   # second pass, adds the Comment column

GSC: US-only, best ranking page per keyword (pages within 3x of the top page's impressions, lowest position),
     re-queried for every week up to the latest day Search Console has data for.
Chatbeat: average Open Loyalty position per prompt and week. Several exports can be passed per type; later files
     win on duplicate runs. Weeks the exports don't fully cover are taken from q4_history.json.
Starting positions (W38) always come from q4_history.json. Complete weeks are written back to it, so commit the
updated history after each weekly run.

Output: semicolon-separated CSV with comma decimals (out/scorecard_q4_<as-of>.csv), ready to upload to Google Drive
as a Sheet, plus an analysis printout for writing the section comments. Comment keys: google, c1, c2, c3, GPT, CLAUDE,
AI_OVERVIEW, PERPLEXITY, GPT2.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

from q4_config import (BASELINE_WEEK, CB_SECTIONS, GSC_ENDPOINT, GSC_SECTIONS, HISTORY_FILE, OL_KEYWORDS,
                       Q4_FIRST_MONDAY, ROOT, SITE, TOKEN_FILE)

SEP = ";"
D = dt.date.fromisoformat


def fmt(v):
    return "" if v is None else f"{v:.1f}".replace(".", ",")


def avg(vals):
    v = [x for x in vals if x is not None]
    return round(sum(v) / len(v), 1) if v else None


def week_label(monday, partial):
    sunday = monday + dt.timedelta(days=6)
    span = (f"{monday:%b} {monday.day}-{sunday.day}" if monday.month == sunday.month
            else f"{monday:%b} {monday.day}-{sunday:%b} {sunday.day}")
    return f"W{monday.isocalendar()[1]} ({span}{', partial' if partial else ''})"


# ── GSC ──────────────────────────────────────────────────────────────────────
class GSC:
    def __init__(self):
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2.credentials import Credentials
        with open(TOKEN_FILE) as f:
            self.s = AuthorizedSession(Credentials.from_authorized_user_info(json.load(f)))

    def query(self, body):
        for attempt in range(4):
            try:
                r = self.s.post(f"{GSC_ENDPOINT}/sites/{SITE}/searchAnalytics/query", json=body)
                r.raise_for_status()
                return r.json().get("rows", [])
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))

    def latest_date(self, as_of):
        rows = self.query({"startDate": str(as_of - dt.timedelta(days=10)), "endDate": str(as_of), "dimensions": ["date"]})
        return max(D(r["keys"][0]) for r in rows)

    def position_us(self, keyword, start, end):
        rows = self.query({"startDate": str(start), "endDate": str(end), "dimensions": ["page"], "rowLimit": 25,
                           "dimensionFilterGroups": [{"filters": [
                               {"dimension": "query", "operator": "equals", "expression": keyword},
                               {"dimension": "country", "operator": "equals", "expression": "usa"}]}]})
        time.sleep(0.35)
        valid = [r for r in rows if r["impressions"] > 0]
        if not valid:
            return None
        top = max(r["impressions"] for r in valid)
        best = min((r for r in valid if r["impressions"] * 3 >= top), key=lambda r: r["position"])
        return math.floor(best["position"] * 10) / 10


# ── Chatbeat ─────────────────────────────────────────────────────────────────
def load_chatbeat(paths):
    """Returns (OL rows [(day, prompt, llm, position)], first day, last day, prompts run per (llm, day))."""
    ol, days, runs = {}, set(), defaultdict(set)
    for p in paths:
        with open(p, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                day = r["date"][:10]
                days.add(day)
                runs[(r["llm"], day)].add(r["prompt"])
                if r["keyword"].strip().lower() in OL_KEYWORDS:
                    try:
                        ol[(r["date"], r["prompt"], r["llm"])] = float(r["position"])
                    except ValueError:
                        pass
    if not days:
        sys.exit(f"no rows in {paths}")
    rows = [(k[0][:10], k[1], k[2], v) for k, v in ol.items()]
    return rows, D(min(days)), D(max(days)), runs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--q3c1", nargs="+", required=True, help="Chatbeat export(s) with the 15 'Best loyalty…' prompts")
    ap.add_argument("--q4", nargs="+", required=True, help="Chatbeat export(s) with the 14 ChatGPT 2nd cluster prompts")
    ap.add_argument("--as-of", type=D, default=dt.date.today(), help="last day to include (default: today)")
    ap.add_argument("--gsc-end", type=D, help="override the last GSC day (default: latest day with data)")
    ap.add_argument("--skip-gsc", action="store_true", help="no GSC queries: complete weeks from history, others blank")
    ap.add_argument("--comments", help="JSON with section comments")
    ap.add_argument("--out", help="output CSV path (default: out/scorecard_q4_<as-of>.csv)")
    ap.add_argument("--no-save-history", action="store_true", help="don't write complete weeks to q4_history.json")
    a = ap.parse_args()

    hist = json.load(open(HISTORY_FILE, encoding="utf-8"))
    mondays = []
    m = D(Q4_FIRST_MONDAY)
    while m <= a.as_of:
        mondays.append(m)
        m += dt.timedelta(days=7)
    wk = {f"W{m.isocalendar()[1]}": m for m in mondays}
    W = list(wk)

    # Chatbeat
    src = {"q3c1": load_chatbeat(a.q3c1), "q4": load_chatbeat(a.q4)}
    cb_end = min(min(s[2] for s in src.values()), a.as_of)
    for name, (_, first, last, _) in src.items():
        print(f"Chatbeat {name}: {first} -> {last}")
    cb, cb_diffs, gaps = {}, [], []
    for key, llm, s, prompts, _ in CB_SECTIONS:
        rows, first, last, _ = src[s]
        for p in prompts:
            pr = [(d, v) for d, pp, l, v in rows if l == llm and pp == p]
            vals = {"start": hist["baseline"]["chatbeat"][key][p]}
            for w, mon in wk.items():
                sun = mon + dt.timedelta(days=6)
                stored = hist["weeks"].get(w, {}).get("chatbeat", {}).get(key, {})
                if first > mon:  # export starts mid-week or later: use history
                    if p in stored:
                        vals[w] = stored[p]
                        continue
                    gaps.append(f"{w} {key} not in history and exports start {first}: partial week computed")
                vals[w] = avg([v for d, v in pr if str(mon) <= d <= str(min(sun, a.as_of))])
                if p in stored and stored[p] != vals[w]:
                    cb_diffs.append((key, p, w, stored[p], vals[w]))
            cb[(key, p)] = vals

    # GSC
    gsc, gsc_diffs = {}, []
    kws = [k for _, _, ks in GSC_SECTIONS for k in ks]
    if a.skip_gsc:
        gsc_end = None
        for k in kws:
            gsc[k] = {w: hist["weeks"].get(w, {}).get("gsc", {}).get(k) for w in W}
    else:
        api = GSC()
        gsc_end = a.gsc_end or min(api.latest_date(a.as_of), a.as_of)
        print(f"GSC data through {gsc_end}")
        for w, mon in wk.items():
            if mon > gsc_end:
                for k in kws:
                    gsc.setdefault(k, {})[w] = None
                continue
            end = min(mon + dt.timedelta(days=6), gsc_end)
            print(f"  GSC {w} {mon} -> {end}", flush=True)
            for k in kws:
                v = api.position_us(k, mon, end)
                gsc.setdefault(k, {})[w] = v
                stored = hist["weeks"].get(w, {}).get("gsc", {})
                if k in stored and stored[k] != v:
                    gsc_diffs.append((k, w, stored[k], v))

    complete = {w for w, mon in wk.items() if mon + dt.timedelta(days=6) <= min(cb_end, gsc_end or cb_end)}
    partial = {w for w in W if w not in complete}

    # ── analysis printout ────────────────────────────────────────────────────
    print(f"\nComplete weeks: {', '.join(w for w in W if w in complete)} | partial: {', '.join(sorted(partial)) or '-'}")
    print(f"Recomputed values differing from q4_history.json: Chatbeat {len(cb_diffs)}, GSC {len(gsc_diffs)}")
    for d in (cb_diffs + gsc_diffs)[:40]:
        print("   ", d)
    for w in sorted(set(gaps))[:10]:
        print("WARNING", w)
    START = hist["baseline"]["gsc"]
    show = W[-3:]
    for key, label, ks in GSC_SECTIONS:
        print(f"\n== {label}: " + " ".join(f"{w}={avg([gsc[k][w] for k in ks])}" for w in W))
        for k in ks:
            print(f"  {k:<36} start {fmt(START[k]):>5} | " + " ".join(f"{w} {fmt(gsc[k][w]):>5}" for w in show))
    for key, llm, s, prompts, label in CB_SECTIONS:
        cols = ["start"] + W
        print(f"\n== {label}: avg " + " ".join(f"{c}={avg([cb[(key, p)][c] for p in prompts])}" for c in cols)
              + f"\n   mentioned (of {len(prompts)}): " + " ".join(f"{c}={sum(cb[(key, p)][c] is not None for p in prompts)}" for c in cols))
        for p in prompts:
            print(f"  {p[:52]:<52} " + " ".join(f"{w} {fmt(cb[(key, p)][w]):>5}" for w in show))
    cur = mondays[-1]
    for name, (_, _, _, runs) in src.items():
        days = [cur + dt.timedelta(days=i) for i in range(7) if cur + dt.timedelta(days=i) <= a.as_of]
        print(f"\nPrompts run per day, current week ({name} export): " + " ".join(f"{d:%d}" for d in days))
        for llm in sorted({l for l, _ in runs}):
            print(f"  {llm:<12} " + " ".join(f"{len(runs.get((llm, str(d)), ())):>2}" for d in days))

    # ── CSV ──────────────────────────────────────────────────────────────────
    comments = json.load(open(a.comments, encoding="utf-8")) if a.comments else {}
    com = lambda k: " ".join(str(comments.get(k, "")).replace(SEP, ",").split())
    header = (["Keyword / Prompt", f"Starting position (W38 {D(BASELINE_WEEK[0]):%b} {D(BASELINE_WEEK[0]).day}-{D(BASELINE_WEEK[1]).day})"]
              + [week_label(wk[w], w in partial) for w in W] + ["Comment"])
    lines = [SEP.join(header)]
    c1, c2 = GSC_SECTIONS[0][2], GSC_SECTIONS[1][2]
    ga = ["Google Average (C1+C2)", fmt(round((round(sum(START[k] for k in c1) / len(c1), 1)
                                               + round(sum(START[k] for k in c2) / len(c2), 1)) / 2, 1))]
    for w in W:
        a1, a2 = avg([gsc[k][w] for k in c1]), avg([gsc[k][w] for k in c2])
        ga.append(fmt(round((a1 + a2) / 2, 1)) if a1 is not None and a2 is not None else "")
    lines.append(SEP.join(ga + [com("google")]))
    for key, label, ks in GSC_SECTIONS:
        lines.append(SEP.join([label, fmt(round(sum(START[k] for k in ks) / len(ks), 1))]
                              + [fmt(avg([gsc[k][w] for k in ks])) for w in W] + [com(key)]))
        for k in ks:
            lines.append(SEP.join([k, fmt(START[k])] + [fmt(gsc[k][w]) for w in W] + [""]))
    for key, _, _, prompts, label in CB_SECTIONS:
        lines.append("")
        lines.append(SEP.join([label] + [fmt(avg([cb[(key, p)][c] for p in prompts])) for c in ["start"] + W] + [com(key)]))
        for p in prompts:
            lines.append(SEP.join([p] + [fmt(cb[(key, p)][c]) for c in ["start"] + W] + [""]))
    bad = [l for l in lines if l and len(l.split(SEP)) != len(header)]
    if bad:
        sys.exit(f"bad field count: {bad[0]}")
    out = a.out or os.path.join(ROOT, "out", f"scorecard_q4_{a.as_of}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print(f"\nWrote {out} ({len(lines)} lines, sha256 {sha})")
    if not comments:
        print("No --comments given: Comment column is empty.")

    # ── history ──────────────────────────────────────────────────────────────
    if not a.no_save_history:
        for w in W:
            if w not in complete:
                continue
            e = hist["weeks"].setdefault(w, {"monday": str(wk[w]), "gsc": {}, "chatbeat": {}})
            if not a.skip_gsc:
                e["gsc"] = {k: gsc[k][w] for k in kws}
            e["chatbeat"] = {key: {p: cb[(key, p)][w] for p in prompts} for key, _, _, prompts, _ in CB_SECTIONS}
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=1, ensure_ascii=False)
        print(f"Updated {os.path.basename(HISTORY_FILE)} with complete weeks: {', '.join(w for w in W if w in complete)}")


if __name__ == "__main__":
    main()
