#!/usr/bin/env python3
"""Convert seo_plan_q3_q4_2026.md to a formatted DOCX."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import re

# ── colour palette ────────────────────────────────────────────────────────────
BRAND_BLUE   = RGBColor(0x1A, 0x56, 0xDB)   # #1A56DB
DARK_GRAY    = RGBColor(0x11, 0x18, 0x27)   # #111827
MED_GRAY     = RGBColor(0x6B, 0x72, 0x80)   # #6B7280
LIGHT_BG     = RGBColor(0xF3, 0xF4, 0xF6)   # #F3F4F6
WARN_RED     = RGBColor(0xDC, 0x26, 0x26)   # #DC2626
GREEN        = RGBColor(0x05, 0x96, 0x69)   # #059669
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)

FONT_NAME = "Calibri"


def set_cell_bg(cell, rgb: RGBColor):
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


def add_run(para, text, bold=False, italic=False, color=None, size=None, font=FONT_NAME):
    run = para.add_run(text)
    run.bold   = bold
    run.italic = italic
    run.font.name = font
    if color:
        run.font.color.rgb = color
    if size:
        run.font.size = Pt(size)
    return run


def style_para(para, space_before=0, space_after=6, line_spacing=None):
    pf = para.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after  = Pt(space_after)
    if line_spacing:
        pf.line_spacing = Pt(line_spacing)


# ── document setup ────────────────────────────────────────────────────────────
doc = Document()

# Margins
sec = doc.sections[0]
sec.left_margin   = Cm(2.5)
sec.right_margin  = Cm(2.5)
sec.top_margin    = Cm(2.0)
sec.bottom_margin = Cm(2.0)

# ── Cover / title block ───────────────────────────────────────────────────────
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
style_para(p, space_before=0, space_after=4)
add_run(p, "SEO Growth Plan", bold=True, color=BRAND_BLUE, size=28)

p2 = doc.add_paragraph()
style_para(p2, space_before=0, space_after=2)
add_run(p2, "2× Organic MQL Leads by December 2026", bold=True, color=DARK_GRAY, size=16)

p3 = doc.add_paragraph()
style_para(p3, space_before=0, space_after=12)
add_run(p3, "Prepared: 15 June 2026  ·  Data: GSC Jan–May 2026, Ahrefs June 2026, HubSpot 157 MQL contacts",
        color=MED_GRAY, size=9)

set_para_border_bottom(p3, "1A56DB")

doc.add_paragraph()  # spacer


# ── Helpers ───────────────────────────────────────────────────────────────────
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
    # Parse bold/italic inline
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
    # strip leading "[ ] "
    cleaned = re.sub(r'^\[ \]\s*', '', text)
    add_run(p, cleaned, color=DARK_GRAY, size=9.5)
    return p


def make_table(headers, rows, col_widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
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

    # Data rows
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

    # Column widths
    if col_widths:
        for ci, w in enumerate(col_widths):
            for row in t.rows:
                row.cells[ci].width = Inches(w)

    doc.add_paragraph()  # spacer after table
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


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: BASELINE
# ═══════════════════════════════════════════════════════════════════════════════

h1("1. Baseline: Where We Are Now")

h2("GSC Traffic Trend (monthly)")
make_table(
    ["Month", "Clicks", "Impressions", "CTR", "Avg Position"],
    [
        ["Dec 2025", "5,993", "1.66M", "0.36%", "10.0"],
        ["Jan 2026", "7,021", "2.23M", "0.31%", "9.8"],
        ["Feb 2026", "7,021", "2.45M", "0.29%", "8.2"],
        ["Mar 2026", "7,038", "2.53M", "0.28%", "6.8 ← PEAK"],
        ["Apr 2026", "5,794", "2.00M", "0.29%", "7.9"],
        ["May 2026", "5,054", "1.88M", "0.27%", "9.8"],
    ],
    col_widths=[1.1, 0.9, 1.1, 0.8, 1.2],
)

alert_box("⚠  Critical: Clicks dropped 28% (March → May). Average position fell from 6.8 → 9.8. 18 pages dropped from Top 10. This requires immediate diagnosis before any growth work begins.", WARN_RED)
doc.add_paragraph()

h2("Ahrefs Snapshot (June 2026)")
make_table(
    ["Metric", "Value"],
    [
        ["Organic keywords", "1,552"],
        ["In positions 1–3", "619"],
        ["Estimated monthly traffic", "16,126"],
        ["Monthly traffic value", "$62,690"],
        ["Site health score", "99 / 100"],
    ],
    col_widths=[2.5, 2.5],
)

h2("MQL Funnel (HubSpot, Jan–May 2026)")
make_table(
    ["Metric", "Value"],
    [
        ["Total MQL contacts (Organic + Direct)", "157 (~31/month)"],
        ["Organic clicks / month (GSC avg)", "~6,600"],
        ["MQL conversion rate", "~0.47% of organic clicks"],
    ],
    col_widths=[3.0, 2.0],
)

h2("Self-Reported Attribution (157 MQLs)")
make_table(
    ["Channel", "Count", "%"],
    [
        ["Google", "49", "31%"],
        ["ChatGPT", "22", "14%"],
        ["AI tools (Gemini, Copilot, Claude, other)", "8", "5.1%"],
        ["Referral / Word-of-mouth", "5", "3.2%"],
        ["Blog / Content", "2", "1.3%"],
        ["Other / unclear", "71", "45%"],
    ],
    col_widths=[3.5, 0.8, 0.7],
)

body("Key insight: ~19% of MQLs explicitly cite AI search tools as their discovery channel — a growing segment with no current strategy.",
     color=BRAND_BLUE, italic=True)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: CORE DIAGNOSIS
# ═══════════════════════════════════════════════════════════════════════════════

h1("2. Core Diagnosis: The Conversion Gap")

body("The fundamental problem is a mismatch between traffic pages and MQL-converting pages.")

h2("Pages with the most organic traffic — but low commercial intent")
make_table(
    ["Page", "Monthly Traffic", "Top Keyword", "Commercial Intent"],
    [
        ["/insider/restaurant-loyalty-programs", "1,692", "restaurant rewards programs", "Low"],
        ["/ (homepage)", "1,714", "retail loyalty program software", "High"],
        ["/insider/sephora-beauty-insider", "514", "sephora tiers", "Very Low"],
        ["/insider/bank-loyalty-programs", "469", "bank loyalty programs", "Low"],
        ["/resources/10-best-mobile-loyalty-apps", "446", "loyalty app", "Low"],
        ["/insider/best-retail-loyalty-programs", "416", "loyalty program retail", "Medium"],
        ["/resources/10-best-gamification-programs", "392", "gamification rewards", "Low"],
    ],
    col_widths=[2.6, 1.1, 2.1, 1.0],
)

h2("Pages where MQLs actually come from — but low traffic")
make_table(
    ["Page", "Est. MQL Count", "Organic Traffic"],
    [
        ["/ (homepage)", "~60+", "1,714 ✅"],
        ["/pricing", "~8", "Low ⚠"],
        ["/applications/white-label-loyalty", "~6", "119 ⚠"],
        ["/technology/loyalty-program-api", "~4", "90 ⚠"],
        ["/insider/best-loyalty-software-comparison-guide", "~4", "107 ⚠"],
    ],
    col_widths=[3.2, 1.2, 1.4],
)

body("The opportunity: the pages that convert MQLs get very little organic traffic. The fastest path to 2× MQLs is routing more commercial-intent traffic to these high-converting pages — not just growing overall traffic.",
     color=GREEN, italic=True)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: PHASE 0
# ═══════════════════════════════════════════════════════════════════════════════

h1("3. Phase 0: Stop the Bleeding (June, Weeks 1–2)")

body("Before building, fix what is breaking.")

h2("3.1  Diagnose the March → May Traffic Drop")
body("18 pages dropped from Top 10; average position fell from 6.8 to 9.8 in two months.")
for t in [
    "Pull the 18 pages that dropped from Top 10 in Ahrefs Site Audit",
    "Check correlation with a Google algorithm update (possible March 2026 core update)",
    "Compare page content freshness — were any key pages not updated recently?",
    "Check if competitors published competing content in February–March",
    "Review page speed / Core Web Vitals regressions in GSC",
]:
    checklist(t)

h2("3.2  Fix the 1 Noindex Page Getting Organic Traffic")
body("Site Audit flagged 1 noindex page receiving organic traffic — this leaks link equity.")
checklist("Identify the page in Site Audit")
checklist("Either remove the noindex tag (if the page should rank) or add a canonical / redirect")

h2("3.3  Submit 34 Pages to IndexNow")
checklist("Submit via IndexNow plugin or API — accelerates recrawling of updated content")

h2("3.4  Address Referring Domain Drop")
body("3 referring domains were lost recently.")
checklist("Identify which domains dropped and why (expired content, redirected links?)")
checklist("Attempt to recover or replace with equivalent links")

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Q3
# ═══════════════════════════════════════════════════════════════════════════════

h1("4. Q3: Convert More, Rank Higher on Commercial Keywords")

body("Q3 Goal: 40 MQL/month by September (from 31 baseline).")
body("Primary levers: improve conversion rate on existing traffic + quick-win keyword rankings.")

# --- 4.1 ---
h2("Initiative 1: Commercial Keyword Quick Wins (July)")

body("These keywords sit in positions 4–10. Pushing them into the top 3 can triple click-through rates (from ~5% to ~25%+).")

make_table(
    ["Keyword", "Volume", "KD", "Current Pos", "Page", "Target"],
    [
        ["customer loyalty software", "700", "49", "5", "Homepage", "Top 3"],
        ["loyalty platform", "600", "62", "4", "Homepage", "Top 3"],
        ["loyalty management software", "350", "54", "4", "Homepage", "Top 3"],
        ["limited time offer", "2,700", "15", "8", "/insider/time-limited-offer", "Top 5"],
        ["loyalty card", "1,400", "9", "9", "/product/loyalty-card-system", "Top 5"],
        ["loyalty management platform", "400", "53", "6", "Homepage", "Top 3"],
        ["reward programs", "450", "34", "7", "/resources/top-40-rewards", "Top 5"],
    ],
    col_widths=[1.7, 0.65, 0.5, 0.85, 1.8, 0.8],
)

h3("Homepage actions (highest priority — 1,714 traffic, $18k monthly value)")
for t in [
    "Add explicit H2/H3 headers targeting 'customer loyalty software', 'loyalty platform', 'loyalty management software'",
    "Add a comparison table vs Antavo, LoyaltyLion, Smile.io with direct keyword mentions",
    "Improve meta title — test: 'Open Loyalty | #1 Customer Loyalty Software & Platform'",
    "Add Schema.org SoftwareApplication markup with explicit category tags",
    "Add internal links from top blog posts to homepage using exact-match anchor text",
]:
    checklist(t)

h3("/insider/time-limited-offer (2,700 vol, KD 15, pos 8 — easiest high-volume win)")
for t in [
    "Expand article depth: add examples, a framework/checklist section, data table",
    "Add internal CTAs linking to promotions module and gamification product pages",
]:
    checklist(t)

# --- 4.2 ---
h2("Initiative 2: Conversion Rate Optimisation on High-Traffic Pages (July–August)")

body("The restaurant, Sephora, bank loyalty, and gamification articles get 1,700+ visits/month combined but send very few MQLs. Adding the right conversion elements changes this without new content.")

h3("For all major blog / insider posts")
for t in [
    "Add a 'See how Open Loyalty powers [topic] programs → Book a Demo' CTA at 30% scroll mark (not just bottom)",
    "Add sticky sidebar or inline widget: 'Building a loyalty program? See our platform →'",
    "Create dedicated 'Loyalty Platform for [Restaurant/Retail/Finance]' landing pages and link from relevant posts",
    "Add exit-intent popup: 'Download our [industry] loyalty program benchmark report'",
]:
    checklist(t)

h3("/insider/best-loyalty-software-comparison-guide (107 traffic, ~4 MQLs — highest converting page)")
for t in [
    "Push from pos 3 → pos 1 for 'best customer loyalty program software'",
    "Expand with a 'vs' comparison section for Antavo, LoyaltyLion, Smile.io, Emarsys, Salesforce Loyalty",
    "Add trust signals: G2 / Capterra badges, customer logos, review quotes",
    "Target keyword cluster: 'loyalty software comparison', 'best loyalty software', 'loyalty platform comparison guide'",
]:
    checklist(t)

# --- 4.3 ---
h2("Initiative 3: Unlock Low-KD Keyword Gaps (August–September)")

body("These keywords have high volume and very low difficulty but Open Loyalty ranks poorly — mainly because the pages are too thin or lack optimisation.")

make_table(
    ["Keyword", "Volume", "KD", "Current Pos", "Action"],
    [
        ["gamification software", "1,600", "5", "37", "Expand existing article"],
        ["customer retention mgmt software", "800", "3", "31", "Expand product page"],
        ["customer retention software", "500", "4", "28", "Same product page"],
        ["brand loyalty", "5,200", "43", "32", "Create cornerstone guide"],
        ["how to build customer loyalty", "800", "24", "45", "Upgrade existing article"],
        ["customer referral program", "600", "37", "50", "Build links to existing page"],
        ["customer loyalty strategies", "450", "12", "49", "Upgrade existing article"],
    ],
    col_widths=[2.0, 0.65, 0.5, 1.0, 2.6],
)

h3("Brand loyalty article (5,200 vol, KD 43, pos 32) — single biggest gap")
body("A top-5 ranking here alone adds ~650 clicks/month.")
for t in [
    "Create a comprehensive 3,000+ word 'What is Brand Loyalty?' guide",
    "Structure: definition → why it matters → 5 stages → how to measure → tactics → how Open Loyalty helps",
    "Include data, examples (Nike, Apple, Amazon), and internal links to all product pages",
]:
    checklist(t)

h3("Customer retention software (800 vol, KD 3–4, pos 28–31)")
for t in [
    "Expand /product/customer-retention-software to 2,000+ words",
    "Add comparison table, case studies, and FAQ schema",
    "With KD of 3–4, this should reach top 5 within 4–6 weeks of publishing",
]:
    checklist(t)

h3("Spanish language pages")
for t in [
    "MQLs already arriving from Spain, Colombia, Peru, Argentina, Honduras",
    "Translate and localise top 5 commercial pages into Spanish",
    "Target: 'software de fidelización', 'plataforma de lealtad', 'programa de fidelización empresarial'",
]:
    bullet(t)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Q4
# ═══════════════════════════════════════════════════════════════════════════════

h1("5. Q4: Scale Volume and AI / GEO Strategy")

body("Q4 Goal: 62 MQL/month by December (true 2× baseline).")
body("Primary levers: content volume, link building, AI search optimisation, industry landing pages.")

# --- 5.1 ---
h2("Initiative 4: Industry Landing Pages (October)")

body("Your MQL contacts span many industries. Dedicated 'loyalty platform for [industry]' pages capture intent that blog posts cannot.")

make_table(
    ["Page URL", "Primary Keyword", "Volume", "Rationale"],
    [
        ["/applications/loyalty-platform-for-retail", "loyalty program for retail", "350", "Best-retail blog ranks #3 — no product CTA destination"],
        ["/applications/loyalty-platform-for-finance", "loyalty program for banks", "200", "Bank loyalty article gets 469 traffic/month"],
        ["/applications/loyalty-platform-for-restaurants", "restaurant loyalty software", "250", "Restaurant article gets 1,692 traffic/month"],
        ["/applications/loyalty-platform-for-healthcare", "loyalty for healthcare", "150", "'gamification healthcare' keyword already converting MQLs"],
        ["/applications/loyalty-platform-for-saas", "saas loyalty program", "200", "/applications/saas-enrichment already ranks #1"],
    ],
    col_widths=[2.2, 1.7, 0.65, 2.2],
)

body("Each page must include: value prop for that industry, client case study, industry-specific features, FAQ schema, demo CTA above the fold.")

# --- 5.2 ---
h2("Initiative 5: AI / GEO Search Optimisation (October–November)")

body("14% of MQLs cite ChatGPT; 19% cite AI tools overall. This will grow. Being cited by LLMs requires different optimisation than traditional Google SEO.")

h3("Entity optimisation")
for t in [
    "Create or update an Open Loyalty Wikipedia / Wikidata entry (AI models cite structured knowledge graphs)",
    "Ensure consistent name, address, product description across Crunchbase, G2, Capterra, LinkedIn",
    "Create a factual /about/company page: founding year, HQ, product category, team size, deployment options",
]:
    checklist(t)

h3("Structured data")
for t in [
    "Add SoftwareApplication schema on all product pages (applicationCategory, operatingSystem, offers, aggregateRating)",
    "Add FAQPage schema on all blog posts — LLMs pull directly from FAQ structured data",
    "Add Organization schema on homepage with sameAs links to Crunchbase, G2, LinkedIn, Wikipedia",
]:
    checklist(t)

h3("AI-friendly content")
for t in [
    "Add a 'Quick Summary' box at the top of key pages with 3–5 bullet points — what LLMs excerpt when citing",
    "Publish a quarterly 'State of Loyalty' data report — LLMs and journalists cite original data heavily",
]:
    checklist(t)

h3("G2 / Capterra review volume")
for t in [
    "Actively solicit reviews from existing clients (minimum 25 reviews needed to appear in AI recommendation lists)",
    "Ensure category tags on G2/Capterra match target keywords: 'loyalty management software', 'customer loyalty software'",
]:
    checklist(t)

# --- 5.3 ---
h2("Initiative 6: Competitor Comparison Pages (November)")

body("People searching 'Open Loyalty vs Antavo' are deep in the buying journey — highest-intent visitors you can get.")

make_table(
    ["Page", "Competitor", "Common Keywords", "Their DR"],
    [
        ["/vs/antavo", "Antavo", "260", "73"],
        ["/vs/loyaltylion", "LoyaltyLion", "236", "76"],
        ["/vs/salesforce-loyalty", "Salesforce Loyalty Mgmt", "90", "92"],
    ],
    col_widths=[2.0, 2.0, 1.3, 0.9],
)

for t in [
    "Create /vs/antavo — 'Open Loyalty vs Antavo: API-First vs Managed Service'",
    "Create /vs/loyaltylion — 'Open Loyalty vs LoyaltyLion: Enterprise vs SMB'",
    "Upgrade /best-loyalty-software to include 10 competitors with a structured comparison table",
]:
    checklist(t)

# --- 5.4 ---
h2("Initiative 7: Link Building (October–December, ongoing)")

body("You are competing for KD 49–62 keywords against DR 73–78 sites (LoyaltyLion, Antavo, Smile.io). Closing the authority gap is essential for Q4 and beyond.")

h3("Tier 1: Digital PR (highest leverage)")
for t in [
    "Publish the '2026 Loyalty Program Benchmarks' data report (use anonymised HubSpot + GSC data)",
    "Pitch to Loyalty360, RetailCustomerExperience, CustomerThink",
    "Target journalists covering loyalty marketing via LinkedIn + HARO",
]:
    checklist(t)

h3("Tier 2: Guest posts")
for t in [
    "Target: CustomerThink, Business2Community, Smile.io blog",
    "Topic angles: 'Why loyalty programs fail without API-first architecture', 'ROI of white-label loyalty in 2026'",
]:
    checklist(t)

h3("Tier 3: Partnership links")
for t in [
    "Request links from technology partners, integration partners, and enterprise clients",
    "Ensure all client case studies on your site are linked from the client's press / partner page",
]:
    checklist(t)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: TECHNICAL SEO
# ═══════════════════════════════════════════════════════════════════════════════

h1("6. Technical SEO Cleanup (Parallel, Ongoing)")

make_table(
    ["Issue", "Pages Affected", "Priority", "Action"],
    [
        ["Missing alt text", "383", "Medium", "Bulk fix — describe image AND include keyword where natural"],
        ["Meta description too long", "84", "Medium", "Trim to 150–160 characters"],
        ["Meta description too short", "47", "Medium", "Expand to 120–160 characters"],
        ["Title too long", "80", "Medium", "Trim to 55–60 characters"],
        ["SERP title ≠ page title", "79", "High", "Google is rewriting your titles — align them"],
        ["Title too short", "10", "Low", "Expand with keyword + brand"],
        ["Noindex page getting traffic", "1", "Critical", "Remove noindex or add canonical"],
        ["Noindex follow pages", "5", "Medium", "Review if intentional"],
    ],
    col_widths=[2.2, 0.9, 0.8, 2.9],
)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: MEASUREMENT
# ═══════════════════════════════════════════════════════════════════════════════

h1("7. Measurement Framework")

h2("Weekly (every Monday)")
for t in [
    "GSC clicks by landing page — focus on homepage, /pricing, /applications/*, /technology/*",
    "Ranking changes for 20 priority keywords (see table below)",
    "MQL count from previous week (HubSpot: source = organic/direct, lifecycle = MQL)",
]:
    bullet(t)

h2("Monthly")
for t in [
    "Total organic MQL count vs 31/month baseline",
    "Organic clicks vs 7,038/month March 2026 peak",
    "Conversion rate: organic clicks → MQL (baseline: 0.47%)",
    "AI attribution: % of MQLs citing ChatGPT/AI (baseline: 19%)",
]:
    bullet(t)

h2("20 Priority Keywords to Track Weekly")
make_table(
    ["Keyword", "Volume", "Current Pos", "Target"],
    [
        ["customer loyalty software", "700", "5", "1–2"],
        ["loyalty platform", "600", "4", "1–2"],
        ["loyalty management software", "350", "4", "1–3"],
        ["loyalty platform saas", "150", "1", "Hold"],
        ["loyalty program software", "500", "3", "1–2"],
        ["loyalty software", "600", "1", "Hold"],
        ["loyalty program api", "200", "1", "Hold"],
        ["brand loyalty", "5,200", "32", "5–10"],
        ["gamification software", "1,600", "37", "5–10"],
        ["customer retention software", "500", "28", "5–10"],
        ["customer retention management software", "800", "31", "5–10"],
        ["limited time offer", "2,700", "8", "4–6"],
        ["loyalty card", "1,400", "9", "4–6"],
        ["best loyalty software", "300", "3", "1–2"],
        ["white label loyalty", "—", "2", "1"],
        ["loyalty program management", "500", "2", "1"],
        ["referral program software", "800", "20", "5–10"],
        ["b2b loyalty platform", "—", "converting", "Monitor"],
        ["loyalty platform for retail", "350", "not ranking", "5–10"],
        ["plataforma de fidelización", "—", "1", "Hold"],
    ],
    col_widths=[2.5, 0.8, 1.0, 0.9],
)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8: SPRINT PLAN
# ═══════════════════════════════════════════════════════════════════════════════

h1("8. 12-Week Sprint Plan")

make_table(
    ["Period", "Focus", "Key Deliverables"],
    [
        ["Weeks 1–2\nJun 16–30", "Triage", "• Diagnose 18 pages that dropped from Top 10\n• Fix noindex page\n• Submit 34 pages to IndexNow\n• Audit homepage meta title/description"],
        ["Weeks 3–6\nJul 1–31", "Quick Wins", "• Homepage H2/H3 + Schema.org markup\n• Expand /insider/time-limited-offer\n• Expand /product/customer-retention-software\n• Bulk fix: alt text (383 pages), meta descriptions, titles\n• Mid-funnel CTAs on top 10 traffic pages\n• Brief 'brand loyalty' cornerstone article"],
        ["Weeks 7–10\nAug 4–31", "Content Push", "• Publish 'brand loyalty' cornerstone (5,200 vol, KD 43)\n• Expand /insider/best-gamification-software\n• Upgrade /insider/best-loyalty-software-comparison-guide\n• Launch /applications/loyalty-platform-for-retail\n• Launch /applications/loyalty-platform-for-finance\n• Begin Spanish commercial page translations"],
        ["Weeks 11–12\nSep 1–15", "CRO Review", "• Review traffic / ranking changes from 8 weeks of work\n• A/B test homepage hero CTA text\n• Assess: are we at 40 MQL/month? Adjust Q4 priorities"],
        ["Oct–Dec", "Q4 Scale", "• Industry pages: restaurants, healthcare, SaaS\n• AI/GEO: structured data, G2 reviews, Wikipedia entity\n• Competitor pages: /vs/antavo, /vs/loyaltylion\n• Link building outreach campaign\n• Publish 2026 Loyalty Benchmarks data report"],
    ],
    col_widths=[1.2, 1.0, 4.6],
)

doc.add_page_break()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9: EXPECTED OUTCOMES
# ═══════════════════════════════════════════════════════════════════════════════

h1("9. Expected Outcomes")

make_table(
    ["Metric", "Baseline (May 2026)", "Q3 Target (Sep)", "Q4 Target (Dec)"],
    [
        ["Organic MQLs / month", "31", "40", "62"],
        ["Organic clicks / month", "5,054", "7,500", "10,000+"],
        ["Homepage commercial KW ranking", "pos 3–5 avg", "pos 1–3 avg", "pos 1–2 avg"],
        ["Keywords in top 3", "619", "750+", "900+"],
        ["AI / GEO MQL attribution", "19%", "22%", "28%"],
    ],
    col_widths=[2.5, 1.5, 1.5, 1.5],
)

body("The 2× MQL target is achievable via three levers working together:")

for t in [
    "Recover lost rankings (the March→May drop = ~2,000 clicks/month lost — fixing this alone recovers significant ground)",
    "Improve conversion rate on existing traffic (0.47% → 0.70% via better CTAs on high-traffic pages — adds ~15 MQLs/month with zero new content)",
    "Grow commercial keyword rankings (homepage, product pages, comparison pages push the rest of the way)",
]:
    bullet(t)

body("\nLever 2 alone — if the top 5 traffic pages each yield 1 additional MQL/month via better CTAs — adds 5 MQLs immediately with no new content required.",
     color=GREEN, italic=True)

# ── save ─────────────────────────────────────────────────────────────────────
doc.save("seo_plan_q3_q4_2026.docx")
print("Saved: seo_plan_q3_q4_2026.docx")
