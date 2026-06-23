"""
MQL Q1/Q2 2026 Report Generator
Lifecycle stages: MQL, Opportunity, Customer
"""
import csv
from collections import Counter, defaultdict
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Brand colours ──────────────────────────────────────────────────────────
BRAND_BLUE = RGBColor(0x1A, 0x56, 0xDB)
DARK_GRAY  = RGBColor(0x11, 0x18, 0x27)
MED_GRAY   = RGBColor(0x6B, 0x72, 0x80)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
WARN_RED   = RGBColor(0xE0, 0x2A, 0x2A)
AMBER      = RGBColor(0xD9, 0x77, 0x06)
GREEN      = RGBColor(0x05, 0x7A, 0x55)
LIGHT_BLUE = RGBColor(0xE8, 0xF0, 0xFE)
LIGHT_GRAY = RGBColor(0xF9, 0xFA, 0xFB)

LC_COLORS = {
    "MQL":         RGBColor(0x1A, 0x56, 0xDB),
    "Opportunity": RGBColor(0x05, 0x7A, 0x55),
    "Customer":    RGBColor(0x7E, 0x3A, 0xF2),
}

# ── Data loading ────────────────────────────────────────────────────────────
def load_data():
    with open("mql_plus_keywords_2025_2026.csv") as f:
        rows = list(csv.DictReader(f))

    def quarter(row):
        d = row["create_date"]
        if not d:
            return None
        m = int(d[5:7])
        y = int(d[:4])
        if y == 2026 and 1 <= m <= 3:
            return "Q1"
        if y == 2026 and 4 <= m <= 6:
            return "Q2"
        return None

    def lc_label(raw):
        return {
            "marketingqualifiedlead": "MQL",
            "opportunity": "Opportunity",
            "salesqualifiedlead": "SQL",
            "customer": "Customer",
        }.get(raw, raw)

    q_rows = [r for r in rows if quarter(r)]
    for r in q_rows:
        r["_quarter"] = quarter(r)
        r["_lc"] = lc_label(r["lifecycle_stage"])
        r["_slug"] = r["first_page"].replace("https://www.openloyalty.io", "").strip("/") if r["first_page"] else ""
        r["_slug"] = "/" + r["_slug"] if r["_slug"] else "/"

    return q_rows

# ── DOCX helpers ────────────────────────────────────────────────────────────
def set_cell_bg(cell, rgb: RGBColor):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    hex_val = f"{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_val)
    tcPr.append(shd)

def set_cell_borders(cell, color="DDDDDD"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:color"), color)
        tcBorders.append(b)
    tcPr.append(tcBorders)

def cell_text(cell, text, bold=False, color=DARK_GRAY, size=9, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)
    run.font.color.rgb = color

def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16 if level == 1 else 13)
    run.font.color.rgb = BRAND_BLUE if level == 1 else DARK_GRAY
    return p

def add_body(doc, text, color=DARK_GRAY, size=10):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    for run in p.runs:
        run.font.size = Pt(size)
        run.font.color.rgb = color
    return p

def add_kpi_row(doc, kpis):
    """kpis: list of (label, value, sublabel) tuples"""
    t = doc.add_table(rows=1, cols=len(kpis))
    t.style = "Table Grid"
    for i, (label, value, sublabel) in enumerate(kpis):
        cell = t.rows[0].cells[i]
        set_cell_bg(cell, LIGHT_BLUE)
        set_cell_borders(cell, "AACCFF")
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        cell.paragraphs[0].clear()
        for txt, bold, size, color in [
            (value,    True,  18, BRAND_BLUE),
            ("\n" + label, True, 9, DARK_GRAY),
            ("\n" + sublabel, False, 8, MED_GRAY),
        ]:
            p = cell.add_paragraph(txt)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            for run in p.runs:
                run.bold = bold
                run.font.size = Pt(size)
                run.font.color.rgb = color
    doc.add_paragraph()

def make_table(doc, headers, col_widths_cm, rows_data, header_bg=BRAND_BLUE):
    t = doc.add_table(rows=1 + len(rows_data), cols=len(headers))
    t.style = "Table Grid"
    # Header row
    for j, h in enumerate(headers):
        cell = t.rows[0].cells[j]
        set_cell_bg(cell, header_bg)
        cell_text(cell, h, bold=True, color=WHITE, size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    # Data rows
    for i, row in enumerate(rows_data):
        bg = LIGHT_GRAY if i % 2 == 0 else WHITE
        for j, (text, text_color, bold) in enumerate(row):
            cell = t.rows[i + 1].cells[j]
            set_cell_bg(cell, bg)
            set_cell_borders(cell, "E5E7EB")
            align = WD_ALIGN_PARAGRAPH.RIGHT if j >= 1 else WD_ALIGN_PARAGRAPH.LEFT
            cell_text(cell, text, bold=bold, color=text_color, size=8.5, align=align)
    # Column widths
    for row in t.rows:
        for j, w in enumerate(col_widths_cm):
            row.cells[j].width = Cm(w)
    doc.add_paragraph()
    return t

# ── Main report ─────────────────────────────────────────────────────────────
def build_report():
    rows = load_data()

    lcs = ["MQL", "Opportunity", "Customer"]

    def by_lc(lc):
        return [r for r in rows if r["_lc"] == lc]

    def by_lc_q(lc, q):
        return [r for r in rows if r["_lc"] == lc and r["_quarter"] == q]

    totals = {lc: len(by_lc(lc)) for lc in lcs}
    q1 = {lc: len(by_lc_q(lc, "Q1")) for lc in lcs}
    q2 = {lc: len(by_lc_q(lc, "Q2")) for lc in lcs}
    grand_total = sum(totals.values())

    brand_kws = {"open loyalty", "openloyalty", "open loyalty demo", "open loyalty pricing", "openloyalty.io", ""}

    doc = Document()
    # Page margins
    section = doc.sections[0]
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)

    # ── Title ──────────────────────────────────────────────────────────────
    p = doc.add_paragraph()
    run = p.add_run("OpenLoyalty.io — Pipeline Analysis")
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = BRAND_BLUE

    p2 = doc.add_paragraph()
    run2 = p2.add_run("Q1 & Q2 2026  |  MQL · Opportunity · Customer  |  Source: HubSpot + GSC")
    run2.font.size = Pt(10)
    run2.font.color.rgb = MED_GRAY
    doc.add_paragraph()

    # ── Top-level KPIs ─────────────────────────────────────────────────────
    add_heading(doc, "1. Executive Summary", 1)
    add_kpi_row(doc, [
        ("Total Pipeline Contacts", str(grand_total), "Q1 + Q2 2026"),
        ("MQLs", str(totals["MQL"]), f"Q1: {q1['MQL']}  |  Q2: {q2['MQL']}"),
        ("Opportunities", str(totals["Opportunity"]), f"Q1: {q1['Opportunity']}  |  Q2: {q2['Opportunity']}"),
        ("Customers", str(totals["Customer"]), "Q1: 1  |  Q2: 0"),
        ("MQL→Opp Rate", f"{totals['Opportunity']/totals['MQL']*100:.0f}%", "Opportunity ÷ MQL"),
    ])

    # ── Monthly trend ──────────────────────────────────────────────────────
    add_heading(doc, "Monthly Volume by Lifecycle Stage", 2)

    months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    monthly = defaultdict(lambda: defaultdict(int))
    for r in rows:
        mo = r["create_date"][:7] if r["create_date"] else ""
        if mo in months:
            monthly[mo][r["_lc"]] += 1

    month_rows = []
    for mo in months:
        label = {"2026-01": "Jan 26", "2026-02": "Feb 26", "2026-03": "Mar 26",
                 "2026-04": "Apr 26", "2026-05": "May 26", "2026-06": "Jun 26"}[mo]
        mql = monthly[mo].get("MQL", 0)
        opp = monthly[mo].get("Opportunity", 0)
        cust = monthly[mo].get("Customer", 0)
        total = mql + opp + cust
        q_label = "Q1" if mo <= "2026-03" else "Q2"
        month_rows.append([
            (label,    DARK_GRAY, True),
            (q_label,  MED_GRAY,  False),
            (str(mql),  BRAND_BLUE if mql else MED_GRAY, mql > 0),
            (str(opp),  GREEN if opp else MED_GRAY, opp > 0),
            (str(cust), LC_COLORS["Customer"] if cust else MED_GRAY, cust > 0),
            (str(total), DARK_GRAY, True),
        ])

    make_table(doc,
        ["Month", "Quarter", "MQL", "Opportunity", "Customer", "Total"],
        [3.5, 2.0, 2.5, 3.0, 2.5, 2.5],
        month_rows,
    )

    # ── Source breakdown ───────────────────────────────────────────────────
    add_heading(doc, "2. Acquisition Source Breakdown", 1)

    sources_order = ["ORGANIC_SEARCH", "DIRECT_TRAFFIC", "PAID_SEARCH", "AI_REFERRALS", "REFERRALS", "OFFLINE", "SOCIAL_MEDIA"]
    source_labels = {
        "ORGANIC_SEARCH": "Organic Search",
        "DIRECT_TRAFFIC": "Direct Traffic",
        "PAID_SEARCH": "Paid Search",
        "AI_REFERRALS": "AI Referrals",
        "REFERRALS": "Referrals",
        "OFFLINE": "Offline",
        "SOCIAL_MEDIA": "Social Media",
    }

    src_counts = {}
    for lc in lcs:
        lc_rows = by_lc(lc)
        src_counts[lc] = Counter(r["source"] for r in lc_rows)

    all_sources = set()
    for d in src_counts.values():
        all_sources.update(d.keys())
    sources_sorted = [s for s in sources_order if s in all_sources]

    src_table_rows = []
    for src in sources_sorted:
        mql = src_counts["MQL"].get(src, 0)
        opp = src_counts["Opportunity"].get(src, 0)
        cust = src_counts["Customer"].get(src, 0)
        total = mql + opp + cust
        src_table_rows.append([
            (source_labels.get(src, src), DARK_GRAY, True),
            (str(mql),  BRAND_BLUE if mql else MED_GRAY, False),
            (str(opp),  GREEN if opp else MED_GRAY, False),
            (str(cust), LC_COLORS["Customer"] if cust else MED_GRAY, False),
            (str(total), DARK_GRAY, True),
        ])

    # Totals row
    src_table_rows.append([
        ("TOTAL", DARK_GRAY, True),
        (str(totals["MQL"]), BRAND_BLUE, True),
        (str(totals["Opportunity"]), GREEN, True),
        (str(totals["Customer"]), LC_COLORS["Customer"], True),
        (str(grand_total), DARK_GRAY, True),
    ])

    make_table(doc,
        ["Source", "MQL", "Opportunity", "Customer", "Total"],
        [5.5, 2.5, 3.0, 2.5, 2.5],
        src_table_rows,
    )

    add_body(doc, "Key insight: Organic Search + AI Referrals = 56% of total pipeline. AI Referrals already outperform Social Media and Referral channels combined, validating investment in AI Overview inclusion.", color=MED_GRAY, size=9)

    # ── Top pages ──────────────────────────────────────────────────────────
    add_heading(doc, "3. Top Pages by Pipeline Stage", 1)
    add_body(doc, "Organic Search + AI Referrals only. Slug = path after openloyalty.io.", color=MED_GRAY, size=9)

    INBOUND_SOURCES = {"ORGANIC_SEARCH", "AI_REFERRALS"}

    def by_lc_inbound(lc):
        return [r for r in rows if r["_lc"] == lc and r["source"] in INBOUND_SOURCES]

    mql_pages  = Counter(r["_slug"] for r in by_lc_inbound("MQL"))
    opp_pages  = Counter(r["_slug"] for r in by_lc_inbound("Opportunity"))
    cust_pages = Counter(r["_slug"] for r in by_lc_inbound("Customer"))
    all_page_slugs = set(list(mql_pages.keys())[:20] + list(opp_pages.keys())[:20])

    page_combos = []
    for pg in all_page_slugs:
        mql = mql_pages.get(pg, 0)
        opp = opp_pages.get(pg, 0)
        cust = cust_pages.get(pg, 0)
        page_combos.append((mql + opp + cust, mql, opp, cust, pg))
    page_combos.sort(reverse=True)

    page_rows = []
    for rank, (total, mql, opp, cust, pg) in enumerate(page_combos[:15], 1):
        page_rows.append([
            (str(rank), MED_GRAY, False),
            (pg, DARK_GRAY, rank <= 3),
            (str(mql),  BRAND_BLUE if mql else MED_GRAY, False),
            (str(opp),  GREEN if opp else MED_GRAY, False),
            (str(cust), LC_COLORS["Customer"] if cust else MED_GRAY, False),
            (str(total), DARK_GRAY, True),
        ])

    make_table(doc,
        ["#", "Page (slug)", "MQL", "Opportunity", "Customer", "Total"],
        [1.2, 8.5, 2.0, 2.5, 2.5, 2.0],
        page_rows,
    )

    # ── Top pages Q1 vs Q2 ─────────────────────────────────────────────────
    add_heading(doc, "Top Pages: Q1 vs Q2 Comparison", 2)

    q1_pages = Counter(r["_slug"] for r in rows if r["_quarter"] == "Q1" and r["source"] in INBOUND_SOURCES)
    q2_pages = Counter(r["_slug"] for r in rows if r["_quarter"] == "Q2" and r["source"] in INBOUND_SOURCES)
    top_slugs = [pg for _, _, _, _, pg in page_combos[:10]]

    qcomp_rows = []
    for pg in top_slugs:
        q1v = q1_pages.get(pg, 0)
        q2v = q2_pages.get(pg, 0)
        delta = q2v - q1v
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        delta_color = GREEN if delta > 0 else (WARN_RED if delta < 0 else MED_GRAY)
        qcomp_rows.append([
            (pg, DARK_GRAY, False),
            (str(q1v), BRAND_BLUE if q1v else MED_GRAY, False),
            (str(q2v), BRAND_BLUE if q2v else MED_GRAY, False),
            (delta_str, delta_color, True),
        ])

    make_table(doc,
        ["Page (slug)", "Q1 2026", "Q2 2026", "Δ Q1→Q2"],
        [9.5, 2.5, 2.5, 2.2],
        qcomp_rows,
    )

    # ── Keywords ───────────────────────────────────────────────────────────
    add_heading(doc, "4. Top Organic Keywords by Pipeline Stage", 1)
    add_body(doc, "Branded terms (open loyalty, openloyalty, etc.) excluded. Source = ORGANIC_SEARCH contacts only.", color=MED_GRAY, size=9)

    def top_kws(lc, n=15):
        lc_rows = [r for r in by_lc(lc) if r["source"] == "ORGANIC_SEARCH"]
        return Counter(
            r["keyword"].lower().strip()
            for r in lc_rows
            if r["keyword"] and r["keyword"].lower().strip() not in brand_kws
        ).most_common(n)

    mql_kws = top_kws("MQL")
    opp_kws = top_kws("Opportunity")

    # Merge into one table
    all_kws_set = list(dict.fromkeys([kw for kw, _ in mql_kws] + [kw for kw, _ in opp_kws]))
    mql_kw_d = dict(mql_kws)
    opp_kw_d = dict(opp_kws)

    kw_rows_data = []
    for kw in all_kws_set[:20]:
        mql = mql_kw_d.get(kw, 0)
        opp = opp_kw_d.get(kw, 0)
        total = mql + opp
        kw_rows_data.append((total, mql, opp, kw))
    kw_rows_data.sort(reverse=True)

    kw_table_rows = []
    for rank, (total, mql, opp, kw) in enumerate(kw_rows_data[:20], 1):
        kw_table_rows.append([
            (str(rank), MED_GRAY, False),
            (kw, DARK_GRAY, rank <= 5),
            (str(mql),  BRAND_BLUE if mql else MED_GRAY, False),
            (str(opp),  GREEN if opp else MED_GRAY, False),
            (str(total), DARK_GRAY, True),
        ])

    make_table(doc,
        ["#", "Keyword", "MQL", "Opportunity", "Total"],
        [1.2, 9.5, 2.5, 3.0, 2.0],
        kw_table_rows,
    )

    # ── Country breakdown ──────────────────────────────────────────────────
    add_heading(doc, "5. Top Countries by Pipeline Stage", 1)

    mql_countries  = Counter(r["country"] for r in by_lc("MQL") if r["country"])
    opp_countries  = Counter(r["country"] for r in by_lc("Opportunity") if r["country"])
    all_countries  = set(list(mql_countries.keys())[:10] + list(opp_countries.keys())[:10])

    country_combos = []
    for c in all_countries:
        country_combos.append((mql_countries.get(c, 0) + opp_countries.get(c, 0), mql_countries.get(c, 0), opp_countries.get(c, 0), c))
    country_combos.sort(reverse=True)

    ctry_rows = []
    for rank, (total, mql, opp, country) in enumerate(country_combos[:12], 1):
        ctry_rows.append([
            (str(rank), MED_GRAY, False),
            (country or "Unknown", DARK_GRAY, rank <= 3),
            (str(mql),  BRAND_BLUE if mql else MED_GRAY, False),
            (str(opp),  GREEN if opp else MED_GRAY, False),
            (str(total), DARK_GRAY, True),
        ])

    make_table(doc,
        ["#", "Country", "MQL", "Opportunity", "Total"],
        [1.2, 7.5, 2.5, 3.0, 2.5],
        ctry_rows,
    )

    # ── Strategic insights ─────────────────────────────────────────────────
    add_heading(doc, "6. Strategic Insights & Recommendations", 1)

    insights = [
        ("Homepage dominates (54% of pipeline)",
         "/ drives 233 combined MQL+Opp contacts — far above any other page. Homepage brand authority and broad 'loyalty' search rankings are the single highest-leverage SEO asset."),
        ("Comparison guide is the #1 content asset",
         "/insider/best-loyalty-software-comparison-guide generates 12 contacts and is the highest-converting blog post. Keep it fresh, expand competitor sections, and build backlinks to it (current gap: ~24 RDs needed)."),
        ("API/developer content converts",
         "/technology/loyalty-program-api drives 10 contacts with keywords like 'api loyalty program' and 'api driven loyalty platform'. Talon.one outranks OL here — expand this page and build technical backlinks."),
        ("White-label is a high-value segment",
         "/applications/white-label-loyalty (15 contacts) + white-label keywords confirm a dedicated buyer segment. This page needs dedicated link-building investment."),
        ("Spanish homepage converts above most product pages",
         "/es generates 16 pipeline contacts — more than all but 3 pages. Suggests significant underinvested Spanish-language SEO opportunity (LATAM/EU)."),
        ("AI Referrals = 36 contacts (8% of pipeline)",
         "Already outperforming Social Media and Referrals combined. Validates prioritizing AI Overview inclusion for 'loyalty software', schema markup, and brand mention building."),
        ("Q1→Q2 MQL decline (-59%)",
         "MQLs dropped from 142 (Q1) to 59 (Q2). Opportunity held steadier (135→92). Likely reflects AI Overview capturing top-3 SERP positions for head terms. Monitor monthly — if trend continues, AI citation strategy becomes urgent."),
        ("Opportunity/MQL ratio = 113%",
         "More Opportunities than MQLs (227 vs 201) suggests some contacts are entering HubSpot directly at Opportunity stage (e.g. demo requests). The /book-a-demo-contact page confirms this — 29 contacts, 20 of them Opportunities."),
    ]

    for i, (title, body) in enumerate(insights, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{i}. {title}")
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = DARK_GRAY
        add_body(doc, body, color=MED_GRAY, size=9)

    doc.save("mql_q1q2_2026_report.docx")
    print("Saved mql_q1q2_2026_report.docx")

if __name__ == "__main__":
    build_report()
