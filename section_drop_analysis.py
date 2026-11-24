#!/usr/bin/env python3
"""
Before/after visibility analysis for one site section in Google Search Console (all countries).

    python3 section_drop_analysis.py --path /insider/ --before 2026-10-23 2026-11-12 --after 2026-11-14 2026-11-21

Prints: daily impressions and position for the section vs the rest of the site, and per-day before/after
breakdowns by content type, device, country, search appearance and query intent, plus the top lost and held queries.
Writes a page + query table (semicolon CSV, comma decimals, values per day) to out/<section>_drop_<after-end>.csv.
"""
import argparse
import collections
import datetime as dt
import json
import os
import re

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from q4_config import GSC_ENDPOINT, ROOT, SITE, TOKEN_FILE

BRAND_CASES = ["sephora", "starbucks", "ikea", "american-eagle", "kfc", "nike", "home-depot", "tesco", "duolingo",
               "bilt", "football-clubs", "sports-clubs"]
THIRD_PARTY_BRANDS = (r"sephora|starbucks|ikea|american eagle|kfc|nike|home depot|tesco|duolingo|bilt|beauty insider|"
                      r"chick|mcdonald|dunkin|panera|subway|walmart|target|ulta|costco|amazon|marriott|hilton|delta|vib")


def page_type(url):
    s = url.split("/")[-1]
    if re.search(r"-with-[a-z]+-[a-z]+$|phil-hussey|emily-ong|alex-sussel|len-llaguno|cezary", s):
        return "Interviews / podcasts"
    if any(b in s for b in BRAND_CASES):
        return "Brand case studies"
    if re.search(r"software|platform|system-features|loyalty-program-management|rewards-management|apps-full-report|"
                 r"buyers-full-report|headless|wallet", s):
        return "Software / vendor comparisons"
    if (re.search(r"examples|programs|-loyalty-program$", s) and
            re.search(r"restaurant|bank|coffee|fashion|retail|ecommerce|b2b|sports|automotive|beauty|insurance|healthcare|"
                      r"fuel|cpg|marketplace|energy|luxury|omnichannel|qsr|d2c|card-linked|coalition|tiered|innovative|email", s)):
        return "Industry example roundups"
    return "Guides & concepts"


def query_intent(q):
    if re.search(THIRD_PARTY_BRANDS, q):
        return "Third-party brand"
    if re.search(r"software|platform|tool|system|app\b|apps|solution|vendor|provider|saas|api|engine|alternatives", q):
        return "Software / vendor"
    if re.search(r"example|best|top|programs?\b", q):
        return "Examples / best-of"
    return "Concepts / how-to"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", required=True, help="URL path the section's pages contain, e.g. /insider/")
    ap.add_argument("--before", nargs=2, required=True, metavar=("START", "END"))
    ap.add_argument("--after", nargs=2, required=True, metavar=("START", "END"))
    ap.add_argument("--out")
    a = ap.parse_args()

    with open(TOKEN_FILE) as f:
        s = AuthorizedSession(Credentials.from_authorized_user_info(json.load(f)))

    def q(body):
        out, start = [], 0
        while True:
            r = s.post(f"{GSC_ENDPOINT}/sites/{SITE}/searchAnalytics/query", json=dict(body, rowLimit=25000, startRow=start))
            r.raise_for_status()
            rows = r.json().get("rows", [])
            out += rows
            if len(rows) < 25000:
                return out
            start += 25000

    inside = {"dimension": "page", "operator": "contains", "expression": a.path}
    outside = {"dimension": "page", "operator": "notContains", "expression": a.path}
    days = lambda w: (dt.date.fromisoformat(w[1]) - dt.date.fromisoformat(w[0])).days + 1
    DB, DA = days(a.before), days(a.after)

    print(f"Daily: {a.path} vs rest of site (impressions, avg position)")
    sec = {r["keys"][0]: r for r in q({"startDate": a.before[0], "endDate": a.after[1], "dimensions": ["date"], "dimensionFilterGroups": [{"filters": [inside]}]})}
    rest = {r["keys"][0]: r for r in q({"startDate": a.before[0], "endDate": a.after[1], "dimensions": ["date"], "dimensionFilterGroups": [{"filters": [outside]}]})}
    for d in sorted(sec):
        r, o = sec[d], rest.get(d, {"impressions": 0, "position": 0})
        print(f"  {d}  section {r['impressions']:7.0f} {r['position']:5.1f} | rest {o['impressions']:7.0f} {o['position']:5.1f}")

    def pull(dim):
        b = q({"startDate": a.before[0], "endDate": a.before[1], "dimensions": dim, "dimensionFilterGroups": [{"filters": [inside]}]})
        af = q({"startDate": a.after[0], "endDate": a.after[1], "dimensions": dim, "dimensionFilterGroups": [{"filters": [inside]}]})
        return {"|".join(r["keys"]): r for r in b}, {"|".join(r["keys"]): r for r in af}

    def grouped(title, before, after, keyfn):
        g = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        for k, r in before.items():
            x = g[keyfn(k)]; x[0] += r["impressions"] / DB; x[2] += r["position"] * r["impressions"] / DB
        for k, r in after.items():
            x = g[keyfn(k)]; x[1] += r["impressions"] / DA; x[3] += r["position"] * r["impressions"] / DA
        print(f"\n{title} (impressions/day before -> after, avg position)")
        for k, (ib, ia, pb, pa) in sorted(g.items(), key=lambda kv: -kv[1][0]):
            if ib >= 1:
                print(f"  {k:<34} {ib:7.0f} -> {ia:6.0f} ({(ia / ib - 1) * 100:+4.0f}%)  pos {pb / ib:5.1f} -> {(pa / ia if ia else 0):5.1f}")
        return g

    pb, pa = pull(["page"])
    grouped("By content type", pb, pa, page_type)
    for dim in (["device"], ["country"], ["searchAppearance"]):
        b, af = pull(dim)
        top = dict(sorted(b.items(), key=lambda kv: -kv[1]["impressions"])[:10])
        grouped(f"By {dim[0]}", top, {k: v for k, v in af.items() if k in top}, lambda k: k)
    qb, qa = pull(["query"])
    grouped("By query intent", qb, qa, query_intent)

    num = lambda v: "" if v is None else f"{v:.1f}".replace(".", ",")
    pct = lambda b, af: "new" if not b else f"{(af / b - 1) * 100:+.0f}%"
    lines = [f"PAGES ({a.path});Content type;Impressions/day before;Impressions/day after;Change;Avg position before;"
             f"Avg position after;Clicks/day before;Clicks/day after"]
    for p in sorted(set(pb) | set(pa), key=lambda p: -pb.get(p, {}).get("impressions", 0)):
        x, y = pb.get(p, {}), pa.get(p, {})
        ib, ia = x.get("impressions", 0) / DB, y.get("impressions", 0) / DA
        if ib >= 1 or ia >= 1:
            lines.append(";".join(["/" + p.split("://", 1)[-1].split("/", 1)[-1], page_type(p), num(ib), num(ia), pct(ib, ia),
                                   num(x.get("position")), num(y.get("position")), num(x.get("clicks", 0) / DB), num(y.get("clicks", 0) / DA)]))
    lines += [";;;;;;;;", "QUERIES (>= 3 impressions/day before);Status;Impressions/day before;Impressions/day after;Change;"
              "Avg position before;Avg position after;Clicks/day before;Clicks/day after"]
    rows = []
    for k, x in qb.items():
        ib = x["impressions"] / DB
        if ib < 3:
            continue
        y = qa.get(k, {})
        ia = y.get("impressions", 0) / DA
        status = "held / grew" if ia >= ib * 0.9 else "lost all" if ia == 0 else "dropped"
        rows.append((ia - ib, ";".join([k.replace(";", ","), status, num(ib), num(ia), pct(ib, ia), num(x["position"]),
                                        num(y.get("position")), num(x["clicks"] / DB), num(y.get("clicks", 0) / DA)])))
    rows.sort()
    lines += [r for _, r in rows]
    print("\nTop 20 queries by impressions lost per day:")
    for _, r in rows[:20]:
        print("  " + r.replace(";", " | "))
    print("\nQueries that held or grew:")
    for _, r in rows[::-1][:15]:
        if "held" in r:
            print("  " + r.replace(";", " | "))

    out = a.out or os.path.join(ROOT, "out", f"{a.path.strip('/').replace('/', '_') or 'site'}_drop_{a.after[1]}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote {out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
