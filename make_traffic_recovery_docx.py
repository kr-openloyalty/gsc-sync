#!/usr/bin/env python3
"""Generate traffic_recovery_plan.docx from gathered GSC + Ahrefs data."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

BRAND_BLUE = RGBColor(0x1A, 0x56, 0xDB)
DARK_GRAY  = RGBColor(0x11, 0x18, 0x27)
MED_GRAY   = RGBColor(0x6B, 0x72, 0x80)
WARN_RED   = RGBColor(0xDC, 0x26, 0x26)
GREEN      = RGBColor(0x05, 0x96, 0x69)
AMBER      = RGBColor(0xD9, 0x77, 0x06)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
FONT_NAME  = "Calibri"


def set_cell_bg(cell, rgb):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    hex_color = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def set_para_border_bottom(para, color="E5E7EB"):
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
    if color:
        run.font.color.rgb = color
    if size:
        run.font.size = Pt(size)
    return run


def style_para(para, space_before=0, space_after=6):
    pf = para.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after  = Pt(space_after)


doc = Document()
sec = doc.sections[0]
sec.left_margin   = Cm(2.5)
sec.right_margin  = Cm(2.5)
sec.top_margin    = Cm(2.0)
sec.bottom_margin = Cm(2.0)


# ── helpers ───────────────────────────────────────────────────────────────────

def h1(text):
    p = doc.add_paragraph()
    style_para(p, space_before=18, space_after=6)
    add_run(p, text, bold=True, color=BRAND_BLUE, size=15)
    set_para_border_bottom(p, "1A56DB")
    return p

def h2(text):
    p = doc.add_paragraph()
    style_para(p, space_before=14, space_after=4)
    add_run(p, text, bold=True, color=DARK_GRAY, size=12)
    return p

def h3(text):
    p = doc.add_paragraph()
    style_para(p, space_before=10, space_after=3)
    add_run(p, text, bold=True, color=MED_GRAY, size=10.5)
    return p

def body(text, color=DARK_GRAY, italic=False, size=10):
    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=4)
    add_run(p, text, color=color, italic=italic, size=size)
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    style_para(p, space_before=1, space_after=2)
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.25)
    parts = re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            add_run(p, part[2:-2], bold=True, color=DARK_GRAY, size=9.5)
        elif part.startswith('*') and part.endswith('*'):
            add_run(p, part[1:-1], italic=True, color=DARK_GRAY, size=9.5)
        elif part.startswith('`') and part.endswith('`'):
            add_run(p, part[1:-1], color=BRAND_BLUE, size=9.5)
        else:
            add_run(p, part, color=DARK_GRAY, size=9.5)
    return p

def checklist(text):
    p = doc.add_paragraph()
    style_para(p, space_before=1, space_after=2)
    p.paragraph_format.left_indent = Inches(0.3)
    add_run(p, "☐  ", bold=True, color=BRAND_BLUE, size=9.5)
    cleaned = re.sub(r'^\[ \]\s*', '', text)
    add_run(p, cleaned, color=DARK_GRAY, size=9.5)
    return p

def make_table(headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    hdr = t.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, BRAND_BLUE)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = WHITE
        run.font.size = Pt(9)
        run.font.name = FONT_NAME
    for ri, row in enumerate(rows):
        tr = t.rows[ri + 1]
        bg = RGBColor(0xF9, 0xFA, 0xFB) if ri % 2 == 0 else WHITE
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(str(val))
            run.font.size = Pt(8.5)
            run.font.name = FONT_NAME
            run.font.color.rgb = DARK_GRAY
    if col_widths:
        for ci, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[ci].width = Inches(w)
    doc.add_paragraph()
    return t

def alert_box(text, color=WARN_RED):
    p = doc.add_paragraph()
    style_para(p, space_before=4, space_after=4)
    p.paragraph_format.left_indent  = Inches(0.2)
    p.paragraph_format.right_indent = Inches(0.2)
    tc = p._p.get_or_add_pPr()
    shd = OxmlElement("w:pBdr")
    for side in ("top", "bottom", "left", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    "6")
        el.set(qn("w:space"), "4")
        hex_c = f"{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        el.set(qn("w:color"), hex_c)
        shd.append(el)
    tc.append(shd)
    add_run(p, text, bold=True, color=color, size=9.5)
    return p


# ═════════════════════════════════════════════════════════════════════════════
# COVER
# ═════════════════════════════════════════════════════════════════════════════

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
style_para(p, space_before=0, space_after=4)
add_run(p, "Traffic Recovery Action Plan", bold=True, color=BRAND_BLUE, size=28)

p2 = doc.add_paragraph()
style_para(p2, space_before=0, space_after=2)
add_run(p2, "March → May 2026 Decline: Root Causes & Page-Level Actions", bold=True, color=DARK_GRAY, size=16)

p3 = doc.add_paragraph()
style_para(p3, space_before=0, space_after=12)
add_run(p3,
        "Prepared: 16 June 2026  ·  Data: GSC March–May 2026 (actual clicks), Ahrefs March–June 2026 (traffic delta + keyword counts)",
        color=MED_GRAY, size=9)
set_para_border_bottom(p3, "1A56DB")
doc.add_paragraph()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1: EXECUTIVE SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

h1("1. Executive Summary")

alert_box(
    "⚠  Total click loss (GSC): ~2,000 clicks/month from March peak. "
    "Ahrefs shows ~4,900 estimated visits/month lost across top losers. "
    "25+ pages affected. 5 distinct root causes — each requiring a different fix.",
    WARN_RED
)
doc.add_paragraph()

make_table(
    ["#", "Root Cause", "Pages", "Action"],
    [
        ["1", "Brand SERP displacement", "Sephora, Starbucks, Nike", "Reframe as independent commentary + Review schema"],
        ["2", "Keyword cannibalization", "Mobile apps (2 URLs on same topic)", "Merge into one canonical page + 301 redirect"],
        ["3", "Freshness / algorithm drop", "Comparison guide, retail, restaurant, implementation, Phil Hussey, referral", "Full content refresh + E-E-A-T signals"],
        ["4", "Deleted pages with no redirect", "~6 null-URL entries in Ahrefs", "Redirect audit — restore or 301 to closest alternative"],
        ["5", "Product page keyword erosion", "CRM, SaaS enrichment, points, coupon", "FAQ sections + internal link reinforcement"],
    ],
    col_widths=[0.3, 1.6, 2.1, 2.7],
)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2: GROUP 1 — BRAND SERP DISPLACEMENT
# ═════════════════════════════════════════════════════════════════════════════

h1("2. Group 1 — Brand SERP Displacement")

body(
    "These pages ranked by borrowing authority from famous brand names (Sephora, Starbucks, Nike). "
    "In Q2 2026, the official brands strengthened their own SERP presence, pushing our analysis pages "
    "down 2–4 positions into the click-cliff below position 7.",
    italic=True, color=MED_GRAY
)

make_table(
    ["Page", "GSC Click Loss", "Position March", "Position May", "Ahrefs Δ"],
    [
        ["/insider/sephora-beauty-insider", "−249", "3.9", "7.9", "n/a"],
        ["/insider/starbucks-rewards-program", "−242", "5.6", "8.9", "−195"],
        ["/insider/how-the-nike-customer-loyalty-program-works", "−137", "5.2", "6.2", "n/a"],
    ],
    col_widths=[2.7, 1.0, 1.1, 1.1, 0.9],
)

body(
    "Do NOT attempt to outrank Sephora or Starbucks for exact brand head terms — that battle cannot be won. "
    "Focus on sub-queries official brand pages don't cover: 'worth it?', 'how to maximise', 'vs competitors', 'explained'.",
    color=AMBER, italic=True
)
doc.add_paragraph()

h2("2.1  Sephora Beauty Insider  — Priority: HIGH")
body("Current angle: program description (replicates what Sephora already says). New angle needed:")
checklist("Rename article: 'Is Sephora Beauty Insider Worth It? An Independent Analysis (2026)'")
checklist("Add reviewer verdict, comparison table vs. Ulta / NARS, updated earn/burn rates")
checklist("Add Schema.org Review markup with ratingValue and reviewBody")
checklist("Add 'Last updated' timestamp in H1 area + changelog section at bottom")
body("Target: reclaim position 4–5 for 'sephora loyalty program'; own 'sephora beauty insider worth it'  |  Est. effort: 3–4 hrs",
     color=MED_GRAY, size=9)

h2("2.2  Starbucks Rewards Program  — Priority: HIGH")
checklist("Add independent value analysis: 2026 point redemption rates, comparison vs. Dunkin, Panera")
checklist("Add FAQ schema block — Google is showing FAQs for this SERP")
checklist("Target: position 6–8 (acceptable) with push for 5")
body("Est. effort: 2–3 hrs", color=MED_GRAY, size=9)

h2("2.3  Nike Customer Loyalty Program  — Priority: MEDIUM")
checklist("Add Nike vs. Adidas vs. Puma comparison table")
checklist("Add 'NikePlus exclusive benefits' section to capture long-tail")
body("Est. effort: 2 hrs", color=MED_GRAY, size=9)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3: GROUP 2 — CANNIBALIZATION
# ═════════════════════════════════════════════════════════════════════════════

h1("3. Group 2 — Keyword Cannibalization (MERGE REQUIRED)")

alert_box(
    "⚠  CANNIBALIZATION CONFIRMED: Two pages cover identical user intent ('best mobile loyalty apps'). "
    "Both are losing traffic simultaneously. Google cannot determine which to rank and has split authority between them, "
    "causing both to underperform. Action required before any other work on these pages.",
    WARN_RED
)
doc.add_paragraph()

make_table(
    ["Page", "Ahrefs Mar", "Ahrefs Jun", "Δ Traffic", "GSC Click Δ"],
    [
        ["/resources/10-best-mobile-loyalty-program-apps", "1,322", "446", "−876", "−78"],
        ["/insider/10-best-mobile-loyalty-program-apps-full-report", "n/a", "n/a", "−42", "−28"],
    ],
    col_widths=[3.2, 0.8, 0.8, 0.9, 0.9],
)

h2("Merge Action Plan (Step-by-step)")
checklist("Keep canonical URL: /resources/10-best-mobile-loyalty-program-apps (shorter, cleaner, stronger backlink profile)")
checklist("Merge all unique content from /insider/10-best-mobile-loyalty-program-apps-full-report into the /resources/ page")
checklist("Update the combined page with 2026 app store rankings, download counts, feature changes")
checklist("New H1: '10 Best Mobile Loyalty Program Apps (2026): Full Analysis'")
checklist("301 redirect /insider/10-best-mobile-loyalty-program-apps-full-report → /resources/10-best-mobile-loyalty-program-apps")
checklist("Audit internal links — update all pointing to /insider/ URL to use canonical /resources/ URL")
checklist("Submit canonical URL in GSC for re-crawling")
body("Expected outcome: consolidated page recovers ~60–70% of combined lost traffic within 60–90 days.  |  Est. effort: 4–5 hrs",
     color=GREEN, italic=True)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4: GROUP 3 — FRESHNESS / ALGORITHM
# ═════════════════════════════════════════════════════════════════════════════

h1("4. Group 3 — Freshness / Algorithm Visibility Loss")

body(
    "Pages that held strong positions historically but have not been updated recently. "
    "Google freshness signals combined with Q1 2026 minor core updates have pushed these pages down "
    "more than competitors improved.",
    italic=True, color=MED_GRAY
)
doc.add_paragraph()

# 4.1 Comparison guide
h2("4.1  Best Loyalty Software Comparison Guide  — Priority: VERY HIGH")
make_table(
    ["Metric", "March", "May / June"],
    [
        ["GSC Clicks (est.)", "~150", "~35"],
        ["GSC Position", "6.7", "10.0"],
        ["Ahrefs Traffic", "872", "107"],
        ["Ahrefs Keywords", "—", "−66 keywords lost"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)
body("This is a conversion-relevant page (~4 MQLs from it). Treat as highest-priority refresh.")
checklist("Audit all listed vendors — verify current pricing, features, company status")
checklist("Add / update 2026 scoring criteria: AI features, mobile-first, headless API, composable architecture")
checklist("Add comparison table with live pricing columns")
checklist("Expand keyword coverage: 'loyalty software comparison 2026', 'best loyalty platform for enterprise', 'open source loyalty software'")
checklist("Add Schema.org ItemList + SoftwareApplication markup")
checklist("Internal links FROM this page TO /product/* pages — reinforce conversion path")
body("Est. effort: 6–8 hrs", color=MED_GRAY, size=9)

# 4.2 Retail
h2("4.2  Best Retail Loyalty Programs  — Priority: HIGH")
make_table(
    ["Metric", "March", "May / June"],
    [
        ["Ahrefs Traffic", "1,039", "416"],
        ["Ahrefs Keywords", "—", "−29 keywords lost"],
        ["Position", "2", "3"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)
checklist("Replace or update programs that changed / ended their loyalty scheme since 2024")
checklist("Add 2026 data points: NPS scores, redemption rates, member growth where public")
checklist("Expand 'key takeaway for brands' section — what B2B readers (your ICPs) want")
checklist("New section: 'What makes a great retail loyalty program in 2026?' — captures emerging query cluster")
body("Est. effort: 4–5 hrs", color=MED_GRAY, size=9)

# 4.3 Restaurant
h2("4.3  Restaurant Loyalty Programs  — Priority: HIGH")
make_table(
    ["Metric", "March", "May / June"],
    [
        ["GSC Clicks (est.)", "~190", "~49"],
        ["GSC Position", "5.3", "6.0"],
        ["Ahrefs Traffic", "2,065", "1,692"],
        ["Ahrefs Keywords", "—", "−28 keywords lost"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)
checklist("Update all listed programs (Chick-fil-A, McDonald's, etc.) with 2026 offer structures")
checklist("Starbucks section: link out to /insider/starbucks-rewards-program instead of duplicating details")
checklist("Add: mobile ordering tie-in section (biggest growth area for restaurant loyalty in 2026)")
body("Est. effort: 3–4 hrs", color=MED_GRAY, size=9)

doc.add_page_break()

# 4.4 Implementation
h2("4.4  Loyalty Program Implementation Guide  — Priority: VERY HIGH (high conversion potential)")
make_table(
    ["Metric", "March", "May / June"],
    [
        ["GSC Clicks (est.)", "~100", "~14"],
        ["GSC Position", "10.2", "16.8"],
        ["Ahrefs Traffic", "199", "38"],
        ["Ahrefs Keywords", "—", "−27 keywords lost"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)
alert_box(
    "Position 10.2 → 16.8 across many keywords = bottom-of-funnel page slipping off page 1. "
    "Someone searching for 'loyalty program implementation' is late-stage — this page converts. Fix first.",
    BRAND_BLUE
)
doc.add_paragraph()
checklist("Add phased implementation timeline with milestones")
checklist("Add integration checklist: POS, CRM, mobile app, API")
checklist("Add cost estimation guide section")
checklist("Add 'Download implementation checklist' CTA (lead magnet opportunity)")
checklist("Target queries: 'loyalty program implementation checklist', 'how to implement a loyalty program', 'loyalty platform implementation cost'")
body("Est. effort: 5–6 hrs", color=MED_GRAY, size=9)

# 4.5 Phil Hussey
h2("4.5  Phil Hussey Interview  — Priority: LOW–MEDIUM")
make_table(
    ["Metric", "March", "May / June"],
    [
        ["Ahrefs Traffic", "368", "60"],
        ["Ahrefs Keywords", "—", "−16 keywords lost"],
        ["Position", "2", "1 (but traffic collapsed)"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)
body("Position improved but traffic collapsed: Google is ranking this for very niche low-volume queries. High-volume terms it previously captured are gone.")
checklist("Keep the URL and interview content (historical backlinks may exist)")
checklist("Add a '2026 Editor's Note' at top synthesising current best practices from the interview's themes")
checklist("Re-target: 'loyalty program strategy framework' as primary keyword (not Phil's name)")
checklist("Alternative: convert to evergreen 'Loyalty Program Strategy: Expert Guide' with interview as cited source")
body("Est. effort: 3–4 hrs", color=MED_GRAY, size=9)

# 4.6 Referral software
h2("4.6  Best Referral Software  — Priority: MEDIUM")
make_table(
    ["Metric", "March", "May / June"],
    [
        ["Ahrefs Traffic", "247", "13"],
        ["Ahrefs Keywords", "—", "−21 keywords lost"],
        ["Position", "4", "8"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)
body("Catastrophic drop. Position 4→8 explains the click collapse. Topic area (referral software) is heavily contested by G2, Capterra, GetApp.")
checklist("Decision first: is referral software core to Open Loyalty's ICP?")
checklist("If yes: full competitive content audit — check what pages now rank 1–4 and what they have that ours doesn't")
checklist("Key gap likely: no 2025–2026 product data, no pricing tables, no verified user quotes")
checklist("If deprioritising: redirect to /product/ or /applications/ page covering referral within loyalty context")
body("Est. effort: 2 hrs audit + decision; 5–6 hrs full refresh if proceeding", color=MED_GRAY, size=9)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5: GROUP 4 — DELETED PAGES
# ═════════════════════════════════════════════════════════════════════════════

h1("5. Group 4 — Deleted / Moved Pages Without Proper Redirects")

body(
    "Ahrefs identified 6+ null-URL entries — pages that existed in March but returned no URL in June. "
    "Combined lost traffic: ~200 estimated monthly visits. Each lost URL also fragments link equity.",
    italic=True, color=MED_GRAY
)
doc.add_paragraph()

make_table(
    ["Scenario", "Action"],
    [
        ["Page deleted, content still valuable", "Restore the page at its original URL"],
        ["Page merged into another URL", "Ensure 301 redirect exists from old → new"],
        ["Page deleted, content obsolete", "301 to most relevant live alternative"],
        ["URL structure changed (e.g. /blog/ → /insider/)", "Audit redirect chain — ensure no 302s or redirect loops"],
    ],
    col_widths=[3.0, 3.7],
)

h2("Redirect Audit Checklist")
checklist("Pull the 'Lost pages' report in Ahrefs → Site Explorer → Pages → Best by Links (filter: lost pages)")
checklist("For each null URL: determine if content existed, where it went, and whether a 301 is in place")
checklist("Audit all redirect chains — flatten any chain longer than 1 hop to a direct 301")
checklist("Check redirect destination relevance — generic homepage redirects waste link equity")
checklist("Submit updated sitemap in GSC after restoring / redirecting")
body("Est. effort: 3–4 hrs audit + 1–2 hrs implementation", color=MED_GRAY, size=9)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6: GROUP 5 — PRODUCT PAGES
# ═════════════════════════════════════════════════════════════════════════════

h1("6. Group 5 — Product Page Keyword Erosion")

body(
    "Core product pages are losing keyword rankings gradually. These pages are closest to conversion — "
    "keyword erosion here has a direct MQL impact.",
    italic=True, color=MED_GRAY
)
doc.add_paragraph()

make_table(
    ["Page", "Ahrefs Mar", "Ahrefs Jun", "Δ Traffic", "Keywords Lost", "Position"],
    [
        ["/product/loyalty-program-crm-software", "219", "59", "−160", "−11", "2 → 2"],
        ["/applications/saas-enrichment", "289", "168", "−121", "−9", "1 → 1"],
        ["/product/loyalty-points-system", "268", "161", "−107", "−15", "1 → 2"],
        ["/product/coupon-software", "208", "110", "−98", "−7", "1 → 1"],
    ],
    col_widths=[2.5, 0.8, 0.8, 0.8, 1.0, 0.8],
)

h2("6.1  /product/loyalty-program-crm-software  — Priority: HIGH")
checklist("Audit: does the page clearly explain CRM + loyalty integration? (member segmentation, lifecycle campaigns, behavioural triggers)")
checklist("Add feature comparison table vs. generic CRM (Salesforce, HubSpot) — show why loyalty-native CRM wins")
checklist("Add 'How it works' technical section targeting 'loyalty CRM API' queries")
checklist("Ensure prominent demo/contact CTA is above fold")

h2("6.2  /product/loyalty-points-system  — Priority: HIGH")
checklist("Add FAQ section: 'how do loyalty points work', 'types of loyalty points', 'points expiration rules', 'loyalty points vs. cashback'")
checklist("Add Schema.org FAQPage markup")
checklist("Lost 15 keywords despite holding position 1→2 — long-tail variants are the target")

h2("6.3  /applications/saas-enrichment  — Priority: MEDIUM")
checklist("Add industry-specific use case sections (fintech, retail, airline) — generates long-tail keyword clusters")
checklist("Ensure page is internally linked from blog/insider content about enrichment")

h2("6.4  /product/coupon-software  — Priority: MEDIUM")
checklist("Add FAQ section and use-case sections")
checklist("Add integration examples")
checklist("Cross-link with /insider/ content that mentions coupons / promotions")

h2("General — All 4 product pages")
for t in [
    "Ensure clear H2 structure covering: what it is, who it's for, key features, integrations, ROI / outcomes",
    "Add customer quotes or mini case studies scoped to the product feature",
    "Internal linking: ensure every major blog page mentioning these features links back to the product page",
]:
    bullet(t)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7: HOMEPAGE
# ═════════════════════════════════════════════════════════════════════════════

h1("7. Homepage Traffic Loss")

make_table(
    ["Metric", "March", "May"],
    [
        ["GSC Clicks (est.)", "~1,200", "~779"],
        ["GSC Click Loss", "—", "−421"],
        ["GSC Impressions", "105,000", "65,000"],
        ["GSC Position", "11.8", "11.1"],
        ["Ahrefs Traffic", "2,102", "1,714"],
        ["Ahrefs Traffic Δ", "—", "−388"],
    ],
    col_widths=[2.0, 1.5, 2.0],
)

alert_box(
    "Impressions dropped from 105k to 65k — this is the critical signal. "
    "Google is showing the homepage in fewer SERPs, not just getting fewer clicks. "
    "Position actually improved (11.8 → 11.1), ruling out a ranking penalty. "
    "The issue is keyword footprint reduction — ~11 keyword rankings lost entirely.",
    WARN_RED
)
doc.add_paragraph()

h2("7.1  Technical / Crawl Check  — Run First")
checklist("Verify no accidental noindex or crawl issues introduced between March and May")
checklist("Check Core Web Vitals in GSC — any LCP / CLS regressions after site updates?")
checklist("Confirm hreflang tags are correct (homepage ranks for multiple markets)")

h2("7.2  Brand Query Coverage")
checklist("Pull GSC Queries report for homepage specifically — which queries drove impressions in March that disappeared in May?")
checklist("If brand query volume dropped: investigate brand awareness (PR, social, news mentions)")

h2("7.3  Internal Link Audit")
checklist("Ensure no pages were mistakenly removed or noindexed that previously flowed authority to homepage")
checklist("Sitemap: confirm homepage is listed with correct <lastmod>")

h2("7.4  Structured Data")
checklist("Add Organization schema on homepage with sameAs links (LinkedIn, Twitter, G2, Capterra, Crunchbase)")
checklist("Add WebSite schema with SearchAction for sitelinks search box")

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8: ADDITIONAL LOSSES
# ═════════════════════════════════════════════════════════════════════════════

h1("8. Additional Visibility Losses — Monitor + Quick Fixes")

make_table(
    ["Page", "Issue", "GSC Position Change", "Action"],
    [
        ["/insider/how-to-build-customer-loyalty",
         "Fell off page 1 entirely",
         "11.5 → 31.5",
         "Immediate content audit — check for URL changes or duplicate content. Refresh + FAQ + recrawl."],
        ["/insider/building-brand-loyalty",
         "Lost page 2 entirely",
         "7.2 → 16.2",
         "Full content refresh — examples, 2025–2026 statistics, author byline with credentials, cited sources."],
        ["/resources/the-top-40-best-rewards-programs",
         "Steady position drop",
         "9.9 → 15.6",
         "Verify all 40 programs still exist; remove/replace defunct; add 2026 new entrants (B2B, fintech)."],
        ["/insider/bank-loyalty-programs",
         "Small position drop, noticeable click loss",
         "6.5 → 7.3",
         "Add 2026 banking loyalty trends (embedded finance, crypto rewards, sustainability)."],
    ],
    col_widths=[2.0, 1.3, 1.2, 2.2],
)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9: PRIORITIZED SPRINT QUEUE
# ═════════════════════════════════════════════════════════════════════════════

h1("9. Prioritized Action Queue")

h2("Sprint 1 — Immediate (Week 1–2): Fix what's bleeding most")

make_table(
    ["Priority", "Page", "Action", "Est. Hours"],
    [
        ["P0", "/resources/10-best-mobile-loyalty-program-apps\n+ /insider/10-best-mobile-loyalty-program-apps-full-report",
         "MERGE + 301 redirect", "5h"],
        ["P0", "/resources/loyalty-program-implementation", "Full content refresh", "6h"],
        ["P1", "/insider/best-loyalty-software-comparison-guide", "Full content refresh", "8h"],
        ["P1", "Deleted pages (null URLs)", "Redirect audit + restore", "4h"],
        ["P1", "/ (homepage)", "Technical audit + structured data", "3h"],
    ],
    col_widths=[0.7, 2.6, 1.8, 0.8],
)

h2("Sprint 2 — High Impact (Week 3–4): Brand pages + freshness")

make_table(
    ["Priority", "Page", "Action", "Est. Hours"],
    [
        ["P1", "/insider/sephora-beauty-insider", "Reframe + update + Review schema", "4h"],
        ["P1", "/insider/starbucks-rewards-program", "Reframe + update + FAQ schema", "3h"],
        ["P2", "/insider/best-retail-loyalty-programs", "Content update", "5h"],
        ["P2", "/insider/restaurant-loyalty-programs", "Content update", "4h"],
        ["P2", "/product/loyalty-program-crm-software", "Feature / CTA refresh", "3h"],
        ["P2", "/product/loyalty-points-system", "FAQ section + schema", "2h"],
    ],
    col_widths=[0.7, 2.6, 1.8, 0.8],
)

h2("Sprint 3 — Maintenance (Week 5–6): Long tail and monitoring")

make_table(
    ["Priority", "Page", "Action", "Est. Hours"],
    [
        ["P2", "/insider/how-to-build-customer-loyalty", "Content refresh", "3h"],
        ["P2", "/insider/building-brand-loyalty", "Content refresh + E-E-A-T", "3h"],
        ["P3", "/resources/the-top-40-best-rewards-programs", "Update list", "2h"],
        ["P3", "/insider/bank-loyalty-programs", "2026 trend update", "2h"],
        ["P3", "/insider/how-the-nike-customer-loyalty-program-works", "Update + comparison table", "2h"],
        ["P3", "/insider/best-referral-software", "Decision: refresh or deprioritise", "2h"],
        ["P3", "/insider/designing-a-loyalty-program-strategy-phil-hussey", "Repurpose to evergreen guide", "4h"],
    ],
    col_widths=[0.7, 2.6, 1.8, 0.8],
)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 10: CANNIBALIZATION WATCHLIST
# ═════════════════════════════════════════════════════════════════════════════

h1("10. Cannibalization Watchlist")

body("Before creating any new content pages, run a keyword overlap check against existing URLs. "
     "Use Ahrefs Content Gap or GSC to confirm no existing page already targets the same primary keyword.")

make_table(
    ["Cluster", "URLs", "Status"],
    [
        ["Mobile loyalty apps",
         "/resources/10-best-mobile-loyalty-program-apps (canonical after merge)",
         "RESOLVED after merge"],
        ["Loyalty software reviews",
         "/insider/best-loyalty-software-comparison-guide + any future 'loyalty platform reviews' page",
         "Monitor — do not create competing page"],
        ["Restaurant loyalty",
         "/insider/restaurant-loyalty-programs + /insider/starbucks-rewards-program",
         "Low risk — different scope"],
        ["Brand loyalty",
         "/insider/building-brand-loyalty + /insider/how-to-build-customer-loyalty",
         "MEDIUM — check keyword overlap before refreshing"],
    ],
    col_widths=[1.3, 3.2, 1.7],
)

doc.add_page_break()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 11: MEASUREMENT
# ═════════════════════════════════════════════════════════════════════════════

h1("11. Measurement — How to Know It's Working")

body("Track these metrics monthly after each sprint. GSC data lags ~3 days. "
     "Review weekly during sprint execution, monthly for trend analysis.")

make_table(
    ["Metric", "Tool", "Baseline (May 2026)", "Target (Sep 2026)"],
    [
        ["Total organic clicks", "GSC", "~5,054/month", "≥6,500/month"],
        ["Organic MQLs", "HubSpot", "31/month", "40+/month"],
        ["/resources/loyalty-program-implementation clicks", "GSC", "~14/month", "80+/month"],
        ["/insider/best-loyalty-software-comparison-guide clicks", "GSC", "~35/month", "120+/month"],
        ["Mobile apps page clicks (post-merge)", "GSC", "~42/month", "100+/month"],
        ["Pages ranking top-10", "Ahrefs", "track baseline now", "+20%"],
        ["Cannibalization: no 2 pages on same topic", "Ahrefs Content Gap", "1 confirmed case", "0 unresolved cases"],
    ],
    col_widths=[2.5, 0.8, 1.5, 1.5],
)

body("Review cadence: check GSC weekly for refreshed pages; full cross-source review monthly.",
     color=MED_GRAY, italic=True)

# ── save ─────────────────────────────────────────────────────────────────────
doc.save("traffic_recovery_plan.docx")
print("Saved: traffic_recovery_plan.docx")
