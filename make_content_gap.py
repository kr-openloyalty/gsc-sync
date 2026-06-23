#!/usr/bin/env python3
"""Generate content_gap_analysis.docx from competitor keyword & content gap data."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── palette ──────────────────────────────────────────────────────────────────
BRAND_BLUE = RGBColor(0x1A, 0x56, 0xDB)
DARK_GRAY  = RGBColor(0x11, 0x18, 0x27)
MED_GRAY   = RGBColor(0x6B, 0x72, 0x80)
LIGHT_BG   = RGBColor(0xF3, 0xF4, 0xF6)
WARN_RED   = RGBColor(0xDC, 0x26, 0x26)
GREEN      = RGBColor(0x05, 0x96, 0x69)
AMBER      = RGBColor(0xF5, 0x9E, 0x0B)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
FONT       = "Calibri"


# ── helpers ───────────────────────────────────────────────────────────────────
def set_cell_bg(cell, rgb):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}")
    tcPr.append(shd)


def add_run(para, text, bold=False, italic=False, color=None, size=10):
    r = para.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.name = FONT
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    return r


def sp(para, before=0, after=4):
    pf = para.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after  = Pt(after)


def h1(doc, text):
    p = doc.add_paragraph()
    sp(p, before=14, after=6)
    add_run(p, text, bold=True, color=BRAND_BLUE, size=16)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    "4")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "1A56DB")
    pBdr.append(bot)
    pPr.append(pBdr)


def h2(doc, text):
    p = doc.add_paragraph()
    sp(p, before=10, after=4)
    add_run(p, text, bold=True, color=DARK_GRAY, size=12)


def h3(doc, text):
    p = doc.add_paragraph()
    sp(p, before=8, after=3)
    add_run(p, text, bold=True, color=MED_GRAY, size=10)


def body(doc, text, size=9):
    p = doc.add_paragraph()
    sp(p, before=0, after=4)
    add_run(p, text, color=DARK_GRAY, size=size)
    return p


def make_table(doc, headers, col_widths, rows_data):
    """headers: list[str], col_widths: list[Cm], rows_data: list[list[(text, color|None, bold)]]"""
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

    # header row
    hr = tbl.rows[0]
    for i, (h, w) in enumerate(zip(headers, col_widths)):
        c = hr.cells[i]
        c.width = w
        set_cell_bg(c, BRAND_BLUE)
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after  = Pt(2)
        r = p.add_run(h)
        r.bold = True
        r.font.name = FONT
        r.font.size = Pt(7.5)
        r.font.color.rgb = WHITE

    for idx, row in enumerate(rows_data):
        tr = tbl.add_row()
        bg = LIGHT_BG if idx % 2 == 0 else WHITE
        for i, (text, color, bold) in enumerate(row):
            c = tr.cells[i]
            c.width = col_widths[i]
            set_cell_bg(c, bg)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if i in (0, 4) else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after  = Pt(2)
            r = p.add_run(text or "")
            r.bold = bold
            r.font.name = FONT
            r.font.size = Pt(7.5)
            r.font.color.rgb = color or DARK_GRAY

    doc.add_paragraph()
    return tbl


def pos_color(gsc_pos):
    if gsc_pos is None:
        return WARN_RED
    if gsc_pos <= 10:
        return GREEN
    if gsc_pos <= 20:
        return AMBER
    return WARN_RED


# ── data ─────────────────────────────────────────────────────────────────────

KW_TABLES = [
    {
        "competitor": "Antavo",
        "rows": [
            # (keyword, vol, comp_pos, ol_gsc_pos, ol_page)
            ("b2b loyalty programs",              450, 2,    16.6, "/insider/b2b-loyalty-program"),
            ("brand loyalty examples",            400, 4,    41.7, "/insider/building-brand-loyalty"),
            ("luxury brand loyalty programs",     150, 2,    None, "—"),
            ("referral loyalty program",          200, 2,    72.5, "help.openloyalty.io/faq/referral-programs ⚠"),
            ("loyalty program best practices",    150, 2,    43.5, "/insider/designing-a-loyalty-program-strategy-…"),
            ("nft loyalty program",               100, 2,    None, "—"),
            ("grocery store loyalty programs",    200, 5,    22.0, "/insider/restaurant-loyalty-programs-… ⚠"),
            ("financial services loyalty program", 50, 2,     3.7, "/insider/bank-loyalty-programs-…"),
            ("fashion loyalty programs",          150, 6,    16.0, "/insider/fashion-loyalty-programs"),
            ("loyalty program email examples",    150, 3,     3.8, "/insider/loyalty-program-email-examples"),
        ],
    },
    {
        "competitor": "Talon.One",
        "rows": [
            ("loyalty program platforms",             350, 6,   2.8, "/ (homepage)"),
            ("generation z consumer behavior",        300, 3,  None, "—"),
            ("card linked loyalty programs",          150, 3,  None, "—"),
            ("promotion engine",                      100, 2,  None, "—"),
            ("retail gamification",                    80, 2,  27.9, "/insider/how-to-use-gamification-in-retail-…"),
            ("enterprise loyalty program software",   200, 5,  None, "—"),
            ("loyalty trends",                        150, 4,   2.3, "/resources/loyalty-program-trends"),
            ("packaged business capabilities",        150, 2,  None, "—"),
            ("what are loyalty cards",                 90, 2,  23.2, "/product/loyalty-card-system"),
            ("customer engagement analytics platform",150, 2,  None, "—"),
        ],
    },
    {
        "competitor": "Voucherify",
        "rows": [
            ("coupon marketing strategy",          200,  2,  21.2, "/insider/effective-coupon-marketing-…"),
            ("bogo",                            21000,  8,  None, "—"),
            ("sales promotion examples",           700,  4,  None, "—"),
            ("gift card promotion ideas",          100,  2,  None, "—"),
            ("retail promotions",                  150,  2,  76.0, "/insider/time-limited-offer ⚠"),
            ("loyalty program fraud",              150,  3,  34.0, "/insider/loyalty-fraud"),
            ("personalized promotions",            100,  2,  None, "—"),
            ("data platform for loyalty marketing",200,  2,   9.2, "/ (homepage)"),
            ("gift card software",                 200,  7,  None, "—"),
            ("fuel loyalty programs",              100,  1,   6.4, "/insider/loyalty-programs-in-fuel-retail"),
        ],
    },
    {
        "competitor": "LoyaltyLion",
        "rows": [
            ("loyalty program",               2900, 4,  13.0, "/ (homepage)"),
            ("customer loyalty programs",     1000, 3,  23.9, "/insider/best-loyalty-software-comparison-guide ⚠"),
            ("loyalty program benefits",      2900, 4,  18.1, "/insider/effective-tiered-loyalty-programs ⚠"),
            ("loyalty marketing",              800, 4,  42.3, "/insider/customer-loyalty-marketing"),
            ("beauty loyalty programs",        150, 2,  25.4, "/insider/sephora-beauty-insider"),
            ("fashion loyalty programs",       150, 1,  16.0, "/insider/fashion-loyalty-programs"),
            ("types of loyalty program",       150, 3,  10.0, "/insider/types-of-loyalty-programs-…"),
            ("loyalty program cost",            80, 2,  41.5, "/insider/loyalty-points ⚠"),
            ("personalized loyalty programs",  100, 1,  62.5, "/ (homepage) ⚠"),
            ("ecommerce customer retention rate",100,1, None, "—"),
        ],
    },
]

CONTENT_RECS = [
    # (priority, title, why, source_competitor, type_)
    (1,  "Loyalty Program Benefits: The Business Case for Customer Retention",
         "LoyaltyLion's #2 traffic page (937 US/mo). OL is surfacing tiered-programs page for this query — wrong intent. "
         "Pillar page capturing 'loyalty program benefits', 'why loyalty programs work', 'benefits of customer loyalty'. "
         "Highest single traffic opportunity in the entire gap analysis.",
         "LoyaltyLion", "Pillar / BOFU"),

    (2,  "Loyalty Marketing: The Complete Strategy Guide with Examples",
         "LoyaltyLion pos 4 (800 vol). OL has /insider/customer-loyalty-marketing stuck at pos 42 — page exists but needs "
         "a full rewrite as a proper pillar. Hub page linking all vertical loyalty articles. Captures 'loyalty marketing "
         "strategy', 'what is loyalty marketing', 'loyalty marketing examples' cluster.",
         "LoyaltyLion", "Pillar / TOFU"),

    (3,  "B2B Loyalty Programs: How to Build Channel & Partner Loyalty at Scale",
         "Antavo's top content asset (509 US/mo, pos 2). OL has /insider/b2b-loyalty-program stuck at GSC pos 16.6 "
         "with 731 impressions and zero clicks — the page exists but is underperforming. Rewrite as a comprehensive "
         "guide with case studies, ROI data, and program structures for B2B contexts.",
         "Antavo", "Blog / MOFU"),

    (4,  "Customer Loyalty Programs: 25 Best Examples and Why They Work",
         "LoyaltyLion's #1 content page drives 4,448 traffic/mo. OL's comparison guide is appearing at GSC pos 23.9 "
         "for this query — completely wrong page. Build a standalone mega-post targeting 'customer loyalty programs', "
         "'loyalty program examples', 'loyalty programs examples' cluster. Potential to become OL's highest-traffic page.",
         "LoyaltyLion", "Mega-post / TOFU"),

    (5,  "Types of Loyalty Programs: Points, Tiers, Cashback, Coalition — Which Model Fits?",
         "LoyaltyLion pos 3 (150 vol). OL has a page (/insider/types-of-loyalty-programs-…) appearing at pos 10 in GSC "
         "with only 3 impressions — essentially unindexed effectively. Rewrite with structured comparison table, pros/cons, "
         "and use-case matching. Foundational content every buyer reads before evaluating software.",
         "LoyaltyLion", "Educational / TOFU"),

    (6,  "Gen Z and Loyalty Programs: What the Next Generation Expects from Brands",
         "Talon.One pos 3 (300 vol, 241/mo traffic, 61 referring domains). Zero coverage on OL. "
         "High external link magnet — marketing publications cite Gen Z content widely. "
         "Directly relevant to enterprise buyers asking 'does loyalty work for younger audiences?'",
         "Talon.One", "Blog / TOFU"),

    (7,  "How Much Does a Loyalty Program Cost? Full 2026 Pricing Breakdown",
         "LoyaltyLion pos 2 (80 vol). OL has no dedicated page — loyalty points page appearing at pos 41.5 "
         "for this query. Bottom-of-funnel buyer intent: people who search this are evaluating vendors. "
         "Trust-builder, sales asset, and a page that almost guarantees demo requests.",
         "LoyaltyLion", "BOFU / Pricing"),

    (8,  "Loyalty Program Fraud: How to Detect and Prevent Points Abuse",
         "Voucherify pos 3 (150 vol). OL has /insider/loyalty-fraud stuck at pos 34. Page exists but needs "
         "a comprehensive rewrite with taxonomy of fraud types, detection signals, and prevention mechanics. "
         "Strong link bait for security, fintech, and retail publications. Enterprise buyers specifically ask about this.",
         "Voucherify", "Blog / MOFU"),

    (9,  "Referral Loyalty Programs: How to Build, Reward, and Scale Word-of-Mouth",
         "Antavo pos 2 (200 vol). OL's only ranking page is help.openloyalty.io — a support FAQ, not a blog post. "
         "No editorial content exists. Create a proper guide with examples (Dropbox, Uber, Airbnb referral mechanics), "
         "referral reward structures, and tie-in to OL's platform capabilities.",
         "Antavo", "Blog / MOFU"),

    (10, "Luxury Brand Loyalty Programs: What Premium Brands Do Differently",
         "Antavo pos 2 (150 vol). OL not ranking. High DR link magnet — luxury publications, fashion blogs, and brand "
         "strategy sites link to this content. Covers Louis Vuitton, Nordstrom, Net-a-Porter program mechanics. "
         "Positions OL as an enterprise platform for premium retail, not just mass-market.",
         "Antavo", "Blog / TOFU"),

    (11, "Card-Linked Loyalty Programs: How They Work and Why Banks Love Them",
         "Talon.One pos 3 (150 vol). Zero coverage on OL or any competitor outside Talon. Growing mechanic "
         "(Amex, Mastercard, Chase all use it). Unique technical angle that appeals to fintech and banking buyers "
         "— a vertical OL already serves (bank loyalty programs is a top-5 traffic page).",
         "Talon.One", "Blog / MOFU"),

    (12, "Personalized Loyalty Programs: Using Data to Build 1-to-1 Reward Experiences",
         "Voucherify pos 2 + LoyaltyLion pos 1 (100 vol). OL homepage at pos 62.5 — no dedicated page. "
         "Personalization is the #1 loyalty trend in every industry report. Directly showcases OL's headless/API "
         "platform strength. Should link to CDP integration content and real-world case studies.",
         "Voucherify + LoyaltyLion", "Blog / MOFU"),

    (13, "CDP-Based Loyalty Programs: Using Customer Data Platforms to Personalize Rewards",
         "Voucherify pos 2 (200 vol, 'data platform for loyalty marketing'). OL homepage at pos 9.2 — strong "
         "impressions (234) but homepage is not the right landing page. Create a dedicated technical guide "
         "targeting CDP + loyalty integration. Perfect for Segment, mParticle, Tealium partnership content.",
         "Voucherify", "Technical / MOFU"),

    (14, "Grocery Store Loyalty Programs: 10 Best Examples and Winning Strategies",
         "Antavo pos 5 (200 vol). OL's restaurant page being surfaced for grocery queries (pos 22) — "
         "clear content gap signal from Google. Grocery is one of the highest-frequency retail verticals "
         "for loyalty. Kroger, Tesco, Lidl, Albertsons examples. Natural next vertical after restaurant content.",
         "Antavo", "Vertical / TOFU"),

    (15, "Beauty Loyalty Programs: How Top Cosmetics Brands Keep Customers Coming Back",
         "LoyaltyLion pos 2 (150 vol). OL has Sephora deep-dive at pos 25.4 but no beauty vertical roundup. "
         "OL's Sephora page (514 traffic/mo) proves the audience exists — a beauty roundup would consolidate "
         "topical authority and capture 'beauty loyalty programs', 'cosmetics loyalty', 'makeup rewards program' cluster.",
         "LoyaltyLion", "Vertical / TOFU"),

    (16, "Retail Gamification: 9 Game Mechanics That Increase Purchase Frequency",
         "Talon.One pos 2 (80 vol). OL has /insider/how-to-use-gamification-in-retail-… at pos 27.9 "
         "with 92 impressions — page exists but buried. Retail is OL's primary vertical. "
         "Rewrite with specific mechanics (spin-to-win, progress bars, badges, streaks), implementation guide, "
         "and ROI data. Strong internal link to gamification product page.",
         "Talon.One", "Blog / MOFU"),

    (17, "What Is a Promotion Engine? How It Powers Loyalty and Incentive Campaigns",
         "Talon.One pos 2 (100 vol). Zero coverage on OL. Promotion engine is a complementary product category "
         "to loyalty software — buyers evaluating OL often compare promotion engines too. "
         "Definitional content that captures search intent and positions OL's rules engine capabilities.",
         "Talon.One", "Glossary / TOFU"),

    (18, "Fashion Loyalty Programs: 3 Iconic Examples and How to Build Yours",
         "LoyaltyLion pos 1 + Antavo pos 6 (150 vol). OL has /insider/fashion-loyalty-programs at GSC pos 16 "
         "— page exists but weak. Fashion is a top vertical (Nike, Adidas, H&M). Expand with program mechanics, "
         "tier structures, and points-per-purchase benchmarks. Target 'fashion loyalty', 'apparel rewards program', "
         "'clothing brand loyalty program' cluster.",
         "LoyaltyLion + Antavo", "Vertical / TOFU"),

    (19, "Loyalty Program Best Practices: 12 Principles That Drive Retention",
         "Antavo pos 2 (150 vol). OL's designing-loyalty-strategy page at pos 43.5 — interview-style content "
         "not optimized for this query. Create a structured best-practices guide: earn/burn ratios, tier thresholds, "
         "communication cadence, redemption rate benchmarks. High-authority link target from loyalty industry publications.",
         "Antavo", "Blog / MOFU"),

    (20, "Petrol and Fuel Retail Loyalty Programs: Challenges, Examples, and Best Practices",
         "Voucherify pos 1 (100 vol). OL already has /insider/loyalty-programs-in-fuel-retail at GSC pos 6.4 "
         "with 81 impressions — this is the easiest win in the list. The page exists and nearly ranks. "
         "5–10 targeted backlinks from petrol/energy industry publications would push it to pos 1–3 and directly "
         "beat Voucherify on their best vertical ranking.",
         "Voucherify", "Quick Win"),
]


# ── build doc ─────────────────────────────────────────────────────────────────
def write_doc(path):
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin   = Cm(2.0)
    sec.right_margin  = Cm(2.0)
    sec.top_margin    = Cm(2.0)
    sec.bottom_margin = Cm(2.0)

    # cover
    p = doc.add_paragraph(); sp(p, 0, 2)
    add_run(p, "OPEN LOYALTY", bold=True, color=BRAND_BLUE, size=10)
    p = doc.add_paragraph(); sp(p, 0, 6)
    add_run(p, "Content & Keyword Gap Analysis vs. Antavo, Talon.One, Voucherify, LoyaltyLion",
            bold=True, size=20, color=DARK_GRAY)
    p = doc.add_paragraph(); sp(p, 0, 2)
    add_run(p, "Data: Ahrefs Site Explorer + Google Search Console (May 2026, US market)",
            italic=True, size=9, color=MED_GRAY)
    p = doc.add_paragraph(); sp(p, 0, 16)
    add_run(p, "Domain: openloyalty.io  |  GSC period: May 2026  |  Ahrefs date: June 2026",
            size=9, color=MED_GRAY)

    # ── Section 1: keyword gap tables ────────────────────────────────────────
    h1(doc, "Section 1: Keyword Gap — 10 Keywords Per Competitor Where They Rank Better")

    headers = ["Keyword", "Vol", "Comp Pos", "OL GSC Pos", "OL Best Ranking Page"]
    col_w   = [Cm(4.2), Cm(1.2), Cm(1.6), Cm(1.8), Cm(7.6)]

    for comp in KW_TABLES:
        h2(doc, comp["competitor"])
        rows_data = []
        for kw, vol, comp_pos, ol_pos, ol_page in comp["rows"]:
            pc = pos_color(ol_pos)
            ol_pos_str = f"{ol_pos}" if ol_pos else "—"
            # highlight if OL actually beats competitor
            comp_pos_color = GREEN if (ol_pos and ol_pos < comp_pos) else DARK_GRAY
            rows_data.append([
                (kw,          DARK_GRAY,      False),
                (str(vol),    MED_GRAY,       False),
                (str(comp_pos), comp_pos_color, True),
                (ol_pos_str,  pc,             True),
                (ol_page,     MED_GRAY,       False),
            ])
        make_table(doc, headers, col_w, rows_data)

    # notes
    p = doc.add_paragraph(); sp(p, 0, 8)
    add_run(p, "Color guide: ", bold=True, size=8, color=DARK_GRAY)
    add_run(p, "Green = OL pos 1–10  ", size=8, color=GREEN)
    add_run(p, "Amber = pos 11–20  ", size=8, color=AMBER)
    add_run(p, "Red = pos 21+ or not ranking  ", size=8, color=WARN_RED)
    add_run(p, "  ⚠ = wrong page ranking / intent mismatch", size=8, color=WARN_RED)

    # ── Section 2: 20 content recommendations ────────────────────────────────
    h1(doc, "Section 2: 20 Content Recommendations to Create")

    # summary table first
    sum_headers = ["#", "Title", "Type", "Source", "Priority"]
    sum_col_w   = [Cm(0.6), Cm(8.6), Cm(2.4), Cm(2.8), Cm(2.0)]

    PRIORITY_LABEL = {1: "🔴 P1", 2: "🔴 P1", 3: "🔴 P1", 4: "🔴 P1", 5: "🔴 P1",
                      6: "🟡 P2", 7: "🟡 P2", 8: "🟡 P2", 9: "🟡 P2", 10: "🟡 P2",
                      11: "🟡 P2", 12: "🟡 P2", 13: "🟡 P2", 14: "🟡 P2", 15: "🟡 P2",
                      16: "🟢 P3", 17: "🟢 P3", 18: "🟢 P3", 19: "🟢 P3", 20: "🟢 P3"}
    PRIORITY_COLOR = {1: WARN_RED, 2: WARN_RED, 3: WARN_RED, 4: WARN_RED, 5: WARN_RED,
                      6: AMBER,  7: AMBER,  8: AMBER,  9: AMBER,  10: AMBER,
                      11: AMBER, 12: AMBER, 13: AMBER, 14: AMBER, 15: AMBER,
                      16: GREEN, 17: GREEN, 18: GREEN, 19: GREEN, 20: GREEN}

    sum_rows = []
    for pri, title, why, source, type_ in CONTENT_RECS:
        pc = PRIORITY_COLOR[pri]
        sum_rows.append([
            (str(pri),   MED_GRAY,   False),
            (title,      DARK_GRAY,  False),
            (type_,      MED_GRAY,   False),
            (source,     MED_GRAY,   False),
            (PRIORITY_LABEL[pri], pc, True),
        ])
    make_table(doc, sum_headers, sum_col_w, sum_rows)

    # detail cards
    h2(doc, "Detailed Recommendations")
    for pri, title, why, source, type_ in CONTENT_RECS:
        pc = PRIORITY_COLOR[pri]
        p = doc.add_paragraph(); sp(p, before=8, after=2)
        add_run(p, f"{PRIORITY_LABEL[pri]}  ", bold=True, color=pc, size=9)
        add_run(p, f"#{pri} — {title}", bold=True, color=DARK_GRAY, size=10)

        p2 = doc.add_paragraph(); sp(p2, 0, 2)
        add_run(p2, "Source competitor: ", bold=True, size=8, color=MED_GRAY)
        add_run(p2, source, size=8, color=BRAND_BLUE)
        add_run(p2, "   |   Type: ", bold=True, size=8, color=MED_GRAY)
        add_run(p2, type_, size=8, color=MED_GRAY)

        p3 = doc.add_paragraph(); sp(p3, 0, 6)
        add_run(p3, why, size=9, color=DARK_GRAY)

    doc.save(path)
    print(f"DOCX written → {path}")


if __name__ == "__main__":
    from pathlib import Path
    write_doc(Path(__file__).parent / "content_gap_analysis.docx")
