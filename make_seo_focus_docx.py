#!/usr/bin/env python3
"""Generate SEO one-pager: top 10 keywords + ~40 pages to optimize."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BRAND_BLUE  = RGBColor(0x1A, 0x56, 0xDB)
DARK_GRAY   = RGBColor(0x11, 0x18, 0x27)
MED_GRAY    = RGBColor(0x6B, 0x72, 0x80)
GREEN       = RGBColor(0x05, 0x96, 0x69)
WARN_RED    = RGBColor(0xDC, 0x26, 0x26)
AMBER       = RGBColor(0xD9, 0x77, 0x06)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BLUE  = RGBColor(0xDB, 0xEA, 0xFE)   # #DBEAFE
LIGHT_GREEN = RGBColor(0xD1, 0xFA, 0xE5)   # #D1FAE5
LIGHT_AMBER = RGBColor(0xFE, 0xF3, 0xC7)   # #FEF3C7
LIGHT_RED   = RGBColor(0xFE, 0xE2, 0xE2)   # #FEE2E2
FONT_NAME   = "Calibri"


def set_cell_bg(cell, rgb):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    hex_color = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

def set_para_border_bottom(para, color="1A56DB"):
    pPr  = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "4")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), color)
    pBdr.append(bot)
    pPr.append(pBdr)

def add_run(para, text, bold=False, italic=False, color=None, size=None):
    run = para.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.name = FONT_NAME
    if color:  run.font.color.rgb = color
    if size:   run.font.size = Pt(size)
    return run

def style_para(para, space_before=0, space_after=4):
    pf = para.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after  = Pt(space_after)

doc = Document()
sec = doc.sections[0]
sec.left_margin   = Cm(1.8)
sec.right_margin  = Cm(1.8)
sec.top_margin    = Cm(1.5)
sec.bottom_margin = Cm(1.5)

# ── helpers ───────────────────────────────────────────────────────────────────
def h1(text):
    p = doc.add_paragraph()
    style_para(p, space_before=14, space_after=5)
    add_run(p, text, bold=True, color=BRAND_BLUE, size=13)
    set_para_border_bottom(p)
    return p

def h2(text):
    p = doc.add_paragraph()
    style_para(p, space_before=10, space_after=3)
    add_run(p, text, bold=True, color=DARK_GRAY, size=10.5)
    return p

def body(text, color=DARK_GRAY, italic=False, size=9.5):
    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=3)
    add_run(p, text, color=color, italic=italic, size=size)
    return p

def make_table(headers, rows, col_widths=None, header_bg=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr_bg = header_bg or BRAND_BLUE
    hdr = t.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, hdr_bg)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = WHITE if hdr_bg == BRAND_BLUE else DARK_GRAY
        run.font.size = Pt(8)
        run.font.name = FONT_NAME
    for ri, row_data in enumerate(rows):
        tr = t.rows[ri + 1]
        row_bg_override = None
        if isinstance(row_data, dict) and "_bg" in row_data:
            row_bg_override = row_data.pop("_bg")
            row_data = list(row_data.values())
        alt_bg = RGBColor(0xF9, 0xFA, 0xFB) if ri % 2 == 0 else WHITE
        bg = row_bg_override or alt_bg
        for ci, val in enumerate(row_data):
            cell = tr.cells[ci]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            run.font.size = Pt(8)
            run.font.name = FONT_NAME
            run.font.color.rgb = DARK_GRAY
    if col_widths:
        for ci, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[ci].width = Inches(w)
    doc.add_paragraph()
    return t


# ══════════════════════════════════════════════════════════════════════════════
# COVER
# ══════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
style_para(p, space_before=0, space_after=3)
add_run(p, "SEO Optimization Focus — Keywords & Pages", bold=True, color=BRAND_BLUE, size=20)

p2 = doc.add_paragraph()
style_para(p2, space_before=0, space_after=2)
add_run(p2, "Q3 2026 action list  ·  Data: HubSpot 1,268 MQL+ contacts (Jun 2025–Jun 2026), GSC Nov 2025 vs May 2026",
        color=MED_GRAY, size=8.5)
set_para_border_bottom(p2)

# Legend note
p3 = doc.add_paragraph()
style_para(p3, space_before=4, space_after=6)
add_run(p3, "Lifecycle score = MQL×1 + SQL×3 + Opportunity×5 + Customer×10. Excludes homepage, pricing, demo pages. "
            "Traffic trend = Nov 2025 → May 2026 GSC clicks.", color=MED_GRAY, italic=True, size=8)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: TOP 10 KEYWORDS
# ══════════════════════════════════════════════════════════════════════════════
h1("1. Top 10 Keywords to Track & Optimize")

body("Non-brand keywords with highest business outcome (Opportunity + Customer weighted). "
     "Sorted by lifecycle score. Traffic = GSC clicks Nov 2025 → May 2026.",
     color=MED_GRAY, italic=True)

kw_rows = [
    # keyword | score | contacts | SQL | Opp | Nov clicks | May clicks | trend | nov pos | may pos | optimize page
    ["customer loyalty software",           "33", "10", "1", "3", "9",   "0",  "▼ −100%", "4.0", "—",   "/insider/best-loyalty-software-comparison-guide"],
    ["best white label loyalty app",        "20", "10", "1", "2", "0",   "0",  "— no clicks", "—",  "—",   "/applications/white-label-loyalty"],
    ["best customer loyalty software",      "19",  "7", "2", "2", "0",   "0",  "— no clicks", "—",  "—",   "/insider/best-loyalty-software-comparison-guide"],
    ["loyalty program software",            "18", "10", "2", "1", "23", "11",  "▼ −52%",  "5.1", "8.4", "/"],
    ["customer loyalty program software",   "18", "12", "1", "1", "2",   "1",  "▼ −50%",  "5.1", "9.0", "/technology/loyalty-program-api"],
    ["customer loyalty platform",           "16",  "8", "0", "2", "1",   "0",  "▼ −100%", "6.3", "—",   "/insider/best-loyalty-software-comparison-guide"],
    ["loyalty system",                      "16",  "8", "0", "2", "22",  "6",  "▼ −73%",  "6.5","11.6", "/"],
    ["loyalty program api",                 "15*", "—", "—", "—", "48", "14",  "▼ −71%",  "5.1", "6.5", "/technology/loyalty-program-api"],
    ["gamification in loyalty programs",    "10",  "4", "0", "2", "0",   "2",  "▲ new",   "—",  "5.2", "/resources/10-best-gamification-loyalty-programs"],
    ["loyalty points",                       "9",  "5", "0", "1", "45",  "8",  "▼ −82%",  "6.0","14.0", "/product/loyalty-points-system"],
]

make_table(
    ["Keyword", "Score", "Contacts", "SQL", "Opp", "Nov Clicks", "May Clicks", "Trend", "Nov Pos", "May Pos", "Primary Page"],
    kw_rows,
    col_widths=[1.9, 0.45, 0.6, 0.4, 0.4, 0.7, 0.7, 0.85, 0.65, 0.65, 2.2],
)

body("* loyalty program api score derived from page-level analysis (/technology/loyalty-program-api: score 63, 6 Opportunities).",
     color=MED_GRAY, italic=True, size=7.5)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: LANDING PAGES
# ══════════════════════════════════════════════════════════════════════════════
h1("2. Landing Pages to Optimize (~18 pages)")

body("Product, application, and technology pages. Sorted by priority then lifecycle score. "
     "Position shown as Nov 2025 → May 2026.",
     color=MED_GRAY, italic=True)

# P0
h2("P0 — Critical (high lifecycle value + major traffic loss)")

lp_p0 = [
    ["/applications/white-label-loyalty",    "72", "42", "1", "7", "64→34",  "−47%", "8.0→16.6", "best white label loyalty app · white label loyalty program"],
    ["/technology/loyalty-program-api",       "63", "37", "1", "6", "121→41", "−66%", "5.0→6.1",  "loyalty program api · customer loyalty program software"],
]
make_table(
    ["Page", "Score", "Contacts", "SQL", "Opp", "Clicks Nov→May", "Δ%", "Position Nov→May", "Focus Keywords"],
    lp_p0,
    col_widths=[2.1, 0.45, 0.65, 0.4, 0.4, 0.9, 0.5, 1.2, 2.65],
)

# P1
h2("P1 — High (good value + significant loss)")

lp_p1 = [
    ["/product/loyalty-points-system",   "30", "18", "0", "3", "140→43", "−69%", "7.1→21.7", "loyalty points · earn loyalty points"],
    ["/product/coupon-software",         "23", "13", "1", "2", "69→9",   "−87%", "8.5→20.7", "coupon maker software · coupon code generator software"],
    ["/resources/10-best-gamification-loyalty-programs", "25", "9", "0", "4", "138→64", "−54%", "4.8→5.7", "gamification in loyalty programs · gamification rewards program"],
    ["/resources/10-best-mobile-loyalty-program-apps",   "21", "13", "0", "2", "220→66", "−70%", "8.3→13.4", "loyalty program app · app based loyalty programs"],
]
make_table(
    ["Page", "Score", "Contacts", "SQL", "Opp", "Clicks Nov→May", "Δ%", "Position Nov→May", "Focus Keywords"],
    lp_p1,
    col_widths=[2.1, 0.45, 0.65, 0.4, 0.4, 0.9, 0.5, 1.2, 2.65],
)

# P2
h2("P2 — Medium / Growing")

lp_p2 = [
    ["/applications/saas-enrichment",        "32", "12", "2", "4", "42→35",  "−17%", "16→48.0 ⚠", "loyalty program saas · customer loyalty saas"],
    ["/product/loyalty-card-system",         "13",  "5", "0", "2", "42→57",  "+36%", "12.8→14.0", "loyalty card system · loyalty cards software"],
    ["/product/loyalty-program-crm-software","10",  "6", "0", "1", "24→7",   "−71%", "6.7→38.0 ⚠","crm and customer loyalty · channel loyalty software"],
    ["/product/vouchers",                    "19", "11", "0", "2", "58→32",  "−45%", "7.7→13.9",  "voucher management system · voucher software"],
    ["/product/reward-management-system",    "17",  "9", "0", "2", "19→13",  "−32%", "7.5→16.9",  "loyalty rewards management system"],
    ["/product/referral-program-software",   "10",  "4", "1", "1", "12→7",   "−42%", "33.7→18.8", "referral program · referral and loyalty programs"],
    ["/product/code-scanning",               "15",  "7", "0", "2", "11→9",   "−18%", "9.9→11.5",  "loyalty program receipt scanning · loyalty qr codes"],
    ["/product/loyalty-campaign-software",    "7",  "3", "0", "1", "5→1",    "−80%", "4.6→10.7",  "loyalty program software · customer loyalty software"],
    ["/product/customer-retention-software",  "5",  "1", "0", "1", "0→1",    "new",  "—→28.0",    "customer retention management software"],
    ["/technology/cloud-loyalty",             "6",  "2", "0", "1", "4→4",    "0%",   "6.5→9.3",   "cloud based loyalty software"],
    ["/product/cashback",                     "7",  "7", "0", "0", "20→11",  "−45%", "15.5→19.4", "cashback software · cashback processing automation"],
    ["/product/customer-gamification-software","5", "5", "0", "0", "2→1",   "−50%", "5.2→20.0",  "gamification platform · customer gamification"],
]
make_table(
    ["Page", "Score", "Contacts", "SQL", "Opp", "Clicks Nov→May", "Δ%", "Position Nov→May", "Focus Keywords"],
    lp_p2,
    col_widths=[2.1, 0.45, 0.65, 0.4, 0.4, 0.9, 0.5, 1.2, 2.65],
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: BLOG / INSIDER PAGES
# ══════════════════════════════════════════════════════════════════════════════
h1("3. Blog & Resource Pages to Optimize (~24 pages)")

body("Insider articles and resource guides. P0–P1 are highest priority (high Opp count + major traffic drop). "
     "P2–P3 are secondary — optimize after landing pages are done.",
     color=MED_GRAY, italic=True)

# P0
h2("P0 — Critical")
blog_p0 = [
    ["/insider/best-loyalty-software-comparison-guide", "68", "32", "4", "7", "137→70", "−49%", "9.7→10.0",
     "customer loyalty software · best customer loyalty software · loyalty software comparison"],
]
make_table(
    ["Page", "Score", "Contacts", "SQL", "Opp", "Clicks Nov→May", "Δ%", "Position Nov→May", "Focus Keywords"],
    blog_p0,
    col_widths=[2.3, 0.45, 0.65, 0.4, 0.4, 0.9, 0.5, 1.1, 2.6],
)

# P1
h2("P1 — High")
blog_p1 = [
    ["/resources/loyalty-program-trends",     "33",  "8", "0", "4+1★", "144→97",  "−33%", "8.8→8.9",   "customer loyalty program trends 2026 · loyalty programs 2026"],
    ["/insider/restaurant-loyalty-programs-…","22", "14", "0", "2",    "390→203", "−48%", "7.0→6.0",   "loyalty program software for restaurants · restaurant loyalty programs"],
    ["/insider/coupon-management-software",   "17",  "5", "0", "3",    "0→41",    "+new", "—→7.0",     "coupon management software · automatic coupon distribution"],
    ["/insider/healthcare-loyalty-programs",  "12",  "4", "0", "2",    "15→24",   "+60%", "6.7→8.6",   "healthcare loyalty programs · affordable patient loyalty programs"],
]
make_table(
    ["Page", "Score", "Contacts", "SQL", "Opp", "Clicks Nov→May", "Δ%", "Position Nov→May", "Focus Keywords"],
    blog_p1,
    col_widths=[2.3, 0.45, 0.65, 0.4, 0.4, 0.9, 0.5, 1.1, 2.6],
)
body("★ /resources/loyalty-program-trends has 1 Customer — highest-maturity signal of all blog content.", color=AMBER, size=7.5, italic=True)

# P2
h2("P2 — Medium / Growing")
blog_p2 = [
    ["/insider/bank-loyalty-programs-…-2022",   "12",  "4", "0", "2", "212→104",  "−51%", "7.7→7.3",   "banking loyalty programs · banks with reward points"],
    ["/insider/ecommerce-loyalty-programs",     "12",  "4", "0", "2", "77→38",    "−51%", "7.0→8.9",   "best ecommerce loyalty programs · ecommerce loyalty platform"],
    ["/insider/10-best-gamification-…-full-report","11","3","0","2", "5→10",     "+100%", "6.4→6.5",   "gamification rewards program · gamification loyalty"],
    ["/insider/best-referral-software",         "10",  "6", "0", "1", "69→16",    "−77%", "12.8→13.2", "best referral programs · affiliate referral software"],
    ["/insider/best-gamification-software",     "10",  "4", "1", "1", "22→14",    "−36%", "11.4→10.9", "gamification software for business · best gamification platform"],
    ["/insider/gamification-case-studies",      "10",  "1", "0", "0+1★","26→12",  "−54%", "6.1→8.9",   "gamification case studies · loyalty gamification examples"],
    ["/insider/coffee-loyalty-programs-…",       "8",  "4", "0", "1", "148→86",   "−42%", "5.5→6.2",   "best coffee shop loyalty programs · coffee loyalty card"],
    ["/insider/top-10-loyalty-programs-for-sports-clubs","7","3","0","1","81→33", "−59%", "6.5→6.6",   "top rated fan loyalty programs · sports loyalty programs"],
    ["/insider/sephora-beauty-insider",          "7",  "3", "0", "1", "331→98",   "−70%", "4.7→7.9",   "sephora beauty insider worth it · beauty insider 2026"],
    ["/resources/the-top-40-best-rewards-…",    "7",  "3", "0", "1", "62→30",    "−52%", "12.7→15.6", "best rewards programs · top loyalty reward programs"],
    ["/insider/10-best-mobile-loyalty-…-full-report","7","3","0","1","42→7",     "−83%", "7.7→10.5",  "mobile loyalty app · loyalty app comparison"],
]
make_table(
    ["Page", "Score", "Contacts", "SQL", "Opp", "Clicks Nov→May", "Δ%", "Position Nov→May", "Focus Keywords"],
    blog_p2,
    col_widths=[2.3, 0.45, 0.65, 0.4, 0.4, 0.9, 0.5, 1.1, 2.6],
)
body("★ /insider/gamification-case-studies has 1 Customer contact — highest-value signal for this cluster.", color=AMBER, size=7.5, italic=True)

# P3 (compact)
h2("P3 — Monitor / Quick-update (lower traffic but Opportunity contacts present)")
blog_p3 = [
    ["/insider/best-retail-loyalty-programs",                "6", "0 Opp", "−77%", "retail loyalty programs · best retail loyalty 2026"],
    ["/insider/headless-loyalty-software",                   "6", "1 Opp", "stable","headless loyalty software · api driven loyalty platform"],
    ["/resources/loyalty-program-roi",                       "6", "1 Opp", "−88%", "how to calculate roi for loyalty programs"],
    ["/insider/loyalty-program-metrics-…",                   "6", "1 Opp", "−42%", "loyalty program metrics · loyalty program health"],
    ["/insider/gamification-healthcare",                     "6", "1 Opp", "−54%", "digital health gamification · healthcare gamification"],
    ["/insider/effective-tiered-loyalty-programs",           "5", "1 Opp", "−52%", "benefits of tiered loyalty program · tier loyalty"],
    ["/resources/loyalty-program-implementation-…",         "5", "0 Opp", "−81%", "loyalty program implementation checklist"],
    ["/insider/how-duolingos-gamification-…",               "5", "1 Opp", "−22%", "duolingo gamification · loyalty gamification mechanics"],
    ["/insider/business-gamification",                       "5", "1 Opp", "+new", "best platforms for business gamification"],
    ["/insider/how-to-solve-the-build-vs-buy-dilemma-…",    "5", "1 Opp", "+new", "build vs buy loyalty platform"],
]
make_table(
    ["Page", "Score", "Opp Signal", "Traffic Trend", "Focus Keyword"],
    blog_p3,
    col_widths=[3.0, 0.5, 0.7, 0.9, 3.2],
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: WHAT TO DO — per-category actions
# ══════════════════════════════════════════════════════════════════════════════
h1("4. Action Guide by Category")

actions = [
    ("P0 Pages — Do first (Week 1–3)",   WARN_RED, [
        "Comparison guide: update all listed vendors with 2026 data; add 'customer loyalty software' in H1/H2; add SoftwareApplication schema.",
        "White-label page: position dropped 8→16.6 — expand content depth, add use-case sections per industry, internal links from blog posts.",
        "Loyalty API page: position 5→6 but −66% clicks — expand keyword coverage: 'loyalty program api', 'loyalty api integration', 'headless loyalty'.",
        "Loyalty points page: position 7→21.7 — check for technical issue (noindex? redirect?). Add FAQ schema for 'loyalty points' variants.",
        "Coupon software page: position 8→20.7 — same check. Expand with 2026 coupon campaign examples, comparison table.",
    ]),
    ("P1–P2 Landing Pages — Week 3–5",   AMBER, [
        "SaaS enrichment: position jumped to 48.0 — likely a crawl/technical issue. Investigate first.",
        "CRM software page: position 6→38 — critical technical check. Then refresh with 2026 CRM integration examples.",
        "Gamification pages: both list and full-report are growing. Merge /insider/10-best-gamification-loyalty-programs-full-report into main page (same cannibalization pattern as mobile apps).",
        "Product pages (vouchers, reward mgmt, cashback): add FAQ schema, 2026 use cases, and internal links from relevant blog posts.",
    ]),
    ("Blog P0–P1 — Parallel with landing pages",   BRAND_BLUE, [
        "Restaurant page: highest absolute traffic of any blog (390→203). Refresh with 2026 program data; add 'loyalty software for restaurants' CTA.",
        "Loyalty trends: only blog page with a Customer contact. Add 2026 stats section, downloadable benchmark report CTA.",
        "Coupon management software: growing from zero — capitalize now. Add structured FAQ and link to /product/coupon-software.",
        "Healthcare loyalty: +60% growth. Expand with 2026 patient engagement examples; link to /applications/ pages.",
    ]),
    ("Top 10 Keywords — Ongoing tracking",   GREEN, [
        "Track all 10 weekly in Ahrefs rank tracker. Set alerts for any drop below position 10.",
        "'customer loyalty software' and 'customer loyalty platform' both show 0 clicks in May — check if rankings dropped or GSC data gap. Recover via comparison guide.",
        "Keywords 4–7 (loyalty program software, system, platform) all lost 50–100% of clicks — homepage + comparison guide need these terms in H2s and meta.",
        "No-click keywords (best white label loyalty app, best customer loyalty software) may be appearing in AI Overviews without clicks — add to Brand Radar monitoring.",
        "Loyalty program api keyword: owned by /technology/loyalty-program-api. Build internal links from all /insider/ pages mentioning APIs.",
    ]),
]

for title, color, bullets in actions:
    h2(title)
    for b in bullets:
        p = doc.add_paragraph()
        style_para(p, space_before=1, space_after=1)
        p.paragraph_format.left_indent = Inches(0.25)
        add_run(p, "→  ", bold=True, color=color, size=9)
        add_run(p, b, color=DARK_GRAY, size=9)

# Footer
doc.add_paragraph()
fp = doc.add_paragraph()
style_para(fp, space_before=6, space_after=0)
set_para_border_bottom(fp, "E5E7EB")
add_run(fp, "Open Loyalty SEO · June 2026  ·  Data: HubSpot MQL+ contacts, GSC Nov 2025 vs May 2026, Ahrefs June 2026",
        color=MED_GRAY, size=7.5)

doc.save("seo_optimization_focus_2026.docx")
print("Saved: seo_optimization_focus_2026.docx")
