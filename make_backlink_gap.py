#!/usr/bin/env python3
"""Generate backlink_gap_analysis.csv and backlink_gap_2026.docx from Ahrefs SERP data."""

import csv
import statistics
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── colour palette ────────────────────────────────────────────────────────────
BRAND_BLUE = RGBColor(0x1A, 0x56, 0xDB)
DARK_GRAY  = RGBColor(0x11, 0x18, 0x27)
MED_GRAY   = RGBColor(0x6B, 0x72, 0x80)
LIGHT_BG   = RGBColor(0xF3, 0xF4, 0xF6)
WARN_RED   = RGBColor(0xDC, 0x26, 0x26)
GREEN      = RGBColor(0x05, 0x96, 0x69)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
FONT_NAME  = "Calibri"

# ── DR50+ referring domains (from Ahrefs site-explorer-referring-domains) ────
# Collected June 2026. Keys = URL fragment (no trailing slash).
OUR_PAGE_RD_DR50 = {
    "openloyalty.io/":                                         100,
    "openloyalty.io/applications/white-label-loyalty":           0,
    "openloyalty.io/insider/best-loyalty-software-comparison-guide": 0,
    "openloyalty.io/product/reward-management-system":           0,
    "openloyalty.io/technology/loyalty-program-api":             0,
    "openloyalty.io/resources/10-best-gamification-loyalty-programs": 0,
    "openloyalty.io/product/loyalty-points-system":              0,
}

COMP_RD_DR50 = {
    "smile.io/":                                                100,
    "loopyloyalty.com/":                                        100,
    "yotpo.com/platform/loyalty/":                               1,
    "en.wikipedia.org/wiki/Loyalty_program":                    100,
    "whitelabel-loyalty.com/":                                  100,
    "squareup.com/us/en/software/loyalty":                      100,
    "epsilon.com/us/products-and-services/epsilon-peoplecloud/loyalty": 100,
    "aa.com/web/i18n/aadvantage-program/discover/loyalty-points-status.html": 2,
    "aa.com/i18n/aadvantage-program/aadvantage-status/loyalty-point-rewards": 0,
    "loyaltylion.com/blog/calculating-loyalty-point-value":      0,
    "mastercard.com/us/en/news-and-trends/Insights/2023/impact-gamification-loyalty-strategies.html": 0,
    "antavo.com/blog/gamification-in-loyalty-programs/":         0,
    "gartner.com/reviews/market/loyalty-program-vendors":        0,
    "g2.com/categories/loyalty-management":                      0,
    "zendesk.com/service/customer-experience/customer-loyalty-software/": 0,
    "brierley.com/blog/the-best-loyalty-software-vendors-for-2025": 0,
    "yotpo.com/blog/loyalty-platform-providers/":                0,
    "enable3.io/white-label-loyalty":                            0,
    "optimove.com/resources/blog/gamification-in-loyalty-programs": 0,
    "developer.squareup.com/docs/loyalty-api/overview":          5,
    "developer.squareup.com/reference/square/loyalty-api":      11,
    "voucherify.io/loyalty-software":                            0,
    "squarespace.com/blog/customer-loyalty-programs":            0,
}


def _lookup_comp_dr50(url):
    """Return DR50+ RD count for a competitor URL, matching on partial path."""
    url_clean = url.split("?")[0].rstrip("/")
    for key, val in COMP_RD_DR50.items():
        if key.rstrip("/") in url_clean or url_clean in key.rstrip("/"):
            return val
    return 0


# ── GSC positions (May 2026, US, avg position) ───────────────────────────────
GSC_POSITIONS = {
    "customer loyalty software":          6.8,
    "best white label loyalty app":       5.9,
    "best customer loyalty software":     5.5,
    "loyalty program software":          12.0,
    "customer loyalty program software": 13.7,
    "customer loyalty platform":         12.1,
    "loyalty system":                    14.4,
    "loyalty program api":               17.1,
    "gamification in loyalty programs":  14.4,
    "loyalty points":                    13.6,
}

# ── Raw SERP data from Ahrefs (June 2026, US) ────────────────────────────────
# Each entry: (position, url, domain_rating, url_rating, refdomains, traffic)
# None = data not available from API (AI overview / PAA slots)

SERP = {
    "customer loyalty software": [
        (2,  "openloyalty.io/",                                                   69, 11, 728,  2066),
        (3,  "gartner.com/reviews/market/loyalty-program-vendors",                92,  4,  14,  4684),
        (4,  "loopyloyalty.com/",                                                 64, 11, 491,  6193),
        (5,  "smile.io/",                                                         78, 17, 4817, 4032),
        (6,  "squareup.com/us/en/software/loyalty",                               93, 16, 179,  8070),
        (7,  "brierley.com/blog/the-best-loyalty-software-vendors-for-2025-…",    35,  4,  22,  1194),
        (8,  "zendesk.com/service/customer-experience/customer-loyalty-software/", 93, 4,  22,   271),
        (10, "yotpo.com/platform/loyalty/",                                        88, 13, 511, 2190),
    ],
    "best white label loyalty app": [
        (1,  "whitelabel-loyalty.com/",                                            65, 14, 462,  336),
        (2,  "openloyalty.io/applications/white-label-loyalty",                    69,  9,   1,  109),  # OUR PAGE
        (4,  "loyalty.kangaroorewards.com/white-labelled-loyalty-app/",            60,  4,   2,   96),
        (5,  "boomerangme.biz/who-its-for/agencies",                               58,  5,   3,   68),
        (6,  "gartner.com/reviews/product/white-label-loyalty-439704575",          92,  4,   0,   32),
        (7,  "enable3.io/white-label-loyalty",                                     32,  7,  15,    4),
        (8,  "rewardoapp.com/en/2024/03/white-label-loyalty-app-what-you-should-know/", 18, 4, 0, 8),
        (9,  "youtube.com/watch?v=pVMhDEvqSQU",                                    99,  0,   0,    3),
    ],
    "best customer loyalty software": [
        (2,  "gartner.com/reviews/market/loyalty-program-vendors",                 92,  4,  14, 4684),
        (4,  "g2.com/categories/loyalty-management",                               91, 15,  53,  315),
        (5,  "zendesk.com/service/customer-experience/customer-loyalty-software/", 93,  4,  22,  271),
        (6,  "brierley.com/blog/the-best-loyalty-software-vendors-for-2025-…",     35,  4,  22, 1194),
        (7,  "yotpo.com/blog/loyalty-platform-providers/",                         88,  4,   4,  290),
        (8,  "youtube.com/watch?v=PV6XveQk2i0",                                    99,  4,   1,   31),
        (9,  "getapp.com/customer-management-software/customer-loyalty/",           85, 15,   9,    7),
        (10, "emarsys.com/learn/blog/best-retail-customer-loyalty-programs/",       81,  6,  77, 7890),
    ],
    "loyalty program software": [
        (2,  "gartner.com/reviews/market/loyalty-program-vendors",                 92,  4,  14, 4684),
        (3,  "yotpo.com/platform/loyalty/",                                         88, 13, 511, 2190),
        (4,  "openloyalty.io/",                                                     69, 11, 728, 2066),  # OUR PAGE
        (5,  "loopyloyalty.com/",                                                   64, 11, 491, 6193),
        (6,  "brierley.com/blog/the-best-loyalty-software-vendors-for-2025-…",      35,  4,  22, 1194),
        (7,  "squareup.com/us/en/software/loyalty",                                 93, 16, 179, 8070),
        (9,  "kognitiv.com/articles-post/top-12-best-loyalty-program-software-…",   53,  6,  17,  385),
        (10, "zendesk.com/service/customer-experience/customer-loyalty-software/",   93,  4,  22,  271),
    ],
    "customer loyalty program software": [
        (2,  "loopyloyalty.com/",                                                    64, 11, 491, 6193),
        (3,  "gartner.com/reviews/market/loyalty-program-vendors",                  92,  4,  14, 4684),
        (4,  "openloyalty.io/",                                                      69, 11, 728, 2066),  # homepage (not focus page)
        (5,  "loopyloyalty.com/",                                                    64, 11, 491, 6193),
        (7,  "smile.io/",                                                            78, 17, 4817, 4032),
        (8,  "squareup.com/us/en/software/loyalty",                                  93, 16, 179, 8070),
        (9,  "brierley.com/blog/the-best-loyalty-software-vendors-for-2025-…",       35,  4,  22, 1194),
        (10, "yotpo.com/platform/loyalty/",                                           88, 13, 511, 2190),
    ],
    "customer loyalty platform": [
        (3,  "gartner.com/reviews/market/loyalty-program-vendors",                   92,  4,  14, 4684),
        (4,  "smile.io/",                                                             78, 17, 4817, 4032),
        (5,  "brierley.com/blog/the-best-loyalty-software-vendors-for-2025-…",        35,  4,  22, 1194),
        (6,  "epsilon.com/us/products-and-services/epsilon-peoplecloud/loyalty",      85, 11, 136,  213),
        (7,  "zendesk.com/service/customer-experience/customer-loyalty-software/",    93,  4,  22,  271),
        (8,  "loopyloyalty.com/",                                                     64, 11, 491, 6193),
        (9,  "kognitiv.com/articles-post/top-12-best-loyalty-program-software-…",     53,  6,  17,  385),
    ],
    "loyalty system": [
        (2,  "squareup.com/us/en/software/loyalty",                                   93, 16, 179, 8070),
        (4,  "openloyalty.io/",                                                        69, 11, 728, 2066),  # OUR PAGE
        (5,  "loopyloyalty.com/",                                                      64, 11, 491, 6193),
        (7,  "smile.io/",                                                              78, 17, 4817, 4032),
        (8,  "squarespace.com/blog/customer-loyalty-programs",                         95,  6,  12,  127),
        (9,  "en.wikipedia.org/wiki/Loyalty_program",                                  97, 15, 1842, 1638),
    ],
    "loyalty program api": [
        (1,  "developer.squareup.com/docs/loyalty-api/overview",                       93,  7,  13,  160),
        (2,  "openloyalty.io/technology/loyalty-program-api",                           69,  9,   0,   43),  # OUR PAGE
        (3,  "developer.salesforce.com/docs/atlas.en-us.loyalty.meta/…",               92,  4,   0,   37),
        (4,  "voucherify.io/loyalty-software",                                          70, 10,  12,   18),
        (5,  "developer.squareup.com/reference/square/loyalty-api",                     93,  5,  19,   30),
        (6,  "nector.io/blog/best-api-integrating-loyalty-programs-pos-systems",        53,  4,   3,   14),
        (9,  "lootly.io/apps/custom-api",                                               50,  6,   2,    6),
    ],
    "gamification in loyalty programs": [
        (2,  "mastercard.com/us/en/news-and-trends/Insights/2023/impact-gamification…", 91, 4,  47,  623),
        (3,  "oracle.com/a/ocom/docs/…gamification-in-loyalty-programs.pdf",             93, 0,   2,  208),
        (4,  "optimove.com/resources/blog/gamification-in-loyalty-programs",             77, 4,   9,   77),
        (5,  "antavo.com/blog/gamification-in-loyalty-programs/",                        73, 6,  41,  225),
        (7,  "trailhead.salesforce.com/content/learn/modules/gamification-in-loyalty-…", 92, 4,   1,   33),
        (8,  "propellocloud.com/blog/gamification-in-loyalty-programs/",                 56, 5,  37,  155),
        (9,  "sciencedirect.com/science/article/abs/pii/S0268401221000013",              94, 4,  17,   70),
    ],
    "loyalty points": [
        (2,  "aa.com/web/i18n/aadvantage-program/discover/loyalty-points-status.html",  85, 28, 126, 4624),
        (3,  "aa.com/i18n/aadvantage-program/aadvantage-status/loyalty-point-rewards…", 85,  6, 202, 1229),
        (4,  "loyaltylion.com/blog/calculating-loyalty-point-value",                     75,  4, 124,   54),
        (7,  "reddit.com/r/americanairlines/…",                                          95,  0,   1, 1089),
        (8,  "nerdwallet.com/travel/learn/loyalty-choice-rewards-american-airlines",     90,  4,   3,   97),
        (9,  "citi.com/credit-cards/credit-card-miles/…",                               84,  4,   0,  275),
        (10, "voucherify.io/glossary/loyalty-points",                                    70,  4,  15,   14),
    ],
}

# ── Keyword metadata ──────────────────────────────────────────────────────────
KEYWORDS = [
    {
        "id": 1,
        "keyword": "customer loyalty software",
        "focus_page": "/ (homepage)",
        "our_position_may": "dropped off",
        "our_page_rd": 728,
        "our_url_in_serp": "openloyalty.io/",
        "our_pos_in_serp": 2,
    },
    {
        "id": 2,
        "keyword": "best white label loyalty app",
        "focus_page": "/applications/white-label-loyalty",
        "our_position_may": "not ranking",
        "our_page_rd": 1,
        "our_url_in_serp": "openloyalty.io/applications/white-label-loyalty",
        "our_pos_in_serp": 2,
    },
    {
        "id": 3,
        "keyword": "best customer loyalty software",
        "focus_page": "/insider/best-loyalty-software-comparison-guide",
        "our_position_may": "not ranking",
        "our_page_rd": 2,
        "our_url_in_serp": None,
        "our_pos_in_serp": "not ranking",
    },
    {
        "id": 4,
        "keyword": "loyalty program software",
        "focus_page": "/ (homepage)",
        "our_position_may": "~8",
        "our_page_rd": 728,
        "our_url_in_serp": "openloyalty.io/",
        "our_pos_in_serp": 4,
    },
    {
        "id": 5,
        "keyword": "customer loyalty program software",
        "focus_page": "/ (homepage)",
        "our_position_may": "~9",
        "our_page_rd": 728,
        "our_url_in_serp": "openloyalty.io/",
        "our_pos_in_serp": 4,
    },
    {
        "id": 6,
        "keyword": "customer loyalty platform",
        "focus_page": "/product/reward-management-system",
        "our_position_may": "dropped off",
        "our_page_rd": 0,
        "our_url_in_serp": None,
        "our_pos_in_serp": "not ranking",
    },
    {
        "id": 7,
        "keyword": "loyalty system",
        "focus_page": "/ (homepage)",
        "our_position_may": "~12",
        "our_page_rd": 728,
        "our_url_in_serp": "openloyalty.io/",
        "our_pos_in_serp": 4,
    },
    {
        "id": 8,
        "keyword": "loyalty program api",
        "focus_page": "/technology/loyalty-program-api",
        "our_position_may": "~6",
        "our_page_rd": 0,
        "our_url_in_serp": "openloyalty.io/technology/loyalty-program-api",
        "our_pos_in_serp": 2,
    },
    {
        "id": 9,
        "keyword": "gamification in loyalty programs",
        "focus_page": "/resources/10-best-gamification-loyalty-programs",
        "our_position_may": "~6",
        "our_page_rd": 0,
        "our_url_in_serp": None,
        "our_pos_in_serp": "not ranking",
    },
    {
        "id": 10,
        "keyword": "loyalty points",
        "focus_page": "/product/loyalty-points-system",
        "our_position_may": "~22",
        "our_page_rd": 0,
        "our_url_in_serp": None,
        "our_pos_in_serp": "not ranking",
    },
]

# SERP character notes
SERP_NOTES = {
    "customer loyalty software": (
        "Mixed SERP: high-DR vendor homepages (Square DR93, Smile DR78) + review aggregators "
        "(Gartner DR92). Top result by refdomains is smile.io (4,817 RD) — an e-commerce loyalty "
        "tool, not enterprise. Brierley blog (DR35) and Zendesk page (DR93, 22 RD) show that DR "
        "alone doesn't determine refdomains. Homepage (pos 2) already has strong presence; the "
        "comparison-guide needs its own backlink profile."
    ),
    "best white label loyalty app": (
        "Low-competition niche SERP dominated by direct white-label vendors. whitelabel-loyalty.com "
        "(DR65, 462 RD) is the clear leader but the remaining top 5 have very few refdomains (0–3). "
        "Our page at pos 2 with just 1 RD is highly vulnerable — even 5–10 targeted links would "
        "solidify the position. No review-site dominance; mostly vendor pages and forums (Reddit, Quora)."
    ),
    "best customer loyalty software": (
        "Dominated by high-DR review/comparison sites: Gartner (DR92), G2 (DR91), GetApp (DR85), "
        "Zendesk (DR93). These are nearly impossible to outrank via backlinks alone — content "
        "quality and brand signals are paramount. Our comparison guide page needs to be listed "
        "in G2/Capterra and cited in industry roundups to build credibility."
    ),
    "loyalty program software": (
        "Our homepage already ranks pos 4 with 728 RD, well above the median. Gartner (DR92) "
        "leads with only 14 RD — demonstrating that DR dominates here. The gap is not backlinks; "
        "it's likely on-page relevance and brand authority signals on the homepage vs. a dedicated "
        "product page."
    ),
    "customer loyalty program software": (
        "Similar to 'loyalty program software' — our homepage ranks at pos 4 but the focus page "
        "(API page) is not ranking. The SERP is dominated by loopyloyalty.com (491 RD × 2 positions) "
        "and high-DR tools. Ranking the API page here requires both backlinks and stronger content "
        "targeting this exact phrase."
    ),
    "customer loyalty platform": (
        "Smile.io (DR78, 4,817 RD) and loopyloyalty (DR64, 491 RD) are the main vendor pages. "
        "High-DR editorial entries (Gartner, Zendesk, Epsilon) hold positions with surprisingly "
        "few RDs (14–136). Our reward-management page has zero backlinks and is not indexed/ranked. "
        "A content + internal-linking refresh plus ~25 targeted links could secure top-10."
    ),
    "loyalty system": (
        "Our homepage already at pos 4 with 728 RD — surplus over the median (491). Wikipedia "
        "(DR97, 1,842 RD) sits at pos 9 but doesn't threaten our page. Squarespace blog (DR95, 12 RD) "
        "at pos 8 shows DR can compensate for few links. Focus should be on moving from pos 4 → pos 1–2 "
        "via content depth and link quality (not quantity)."
    ),
    "loyalty program api": (
        "Technical niche SERP dominated by developer-doc pages (Square DR93, Salesforce DR92). "
        "Our API page ranks at pos 2 with zero backlinks — entirely on domain authority. A small "
        "number of targeted developer/tech backlinks (GitHub mentions, dev blogs, API directories) "
        "would secure pos 1 and provide a buffer."
    ),
    "gamification in loyalty programs": (
        "Informational SERP with high-DR editorial content (Mastercard DR91, Oracle DR93, Salesforce "
        "Trailhead DR92). Antavo (DR73, 41 RD) at pos 5 is the closest comparable vendor blog. Our "
        "/resources/ page is not ranking despite /insider/business-gamification appearing in AI overview. "
        "Need to consolidate content and build links to the priority resource page."
    ),
    "loyalty points": (
        "SERP is almost entirely dominated by American Airlines AAdvantage loyalty-points pages — "
        "a completely different intent (consumer airline programme, not B2B software). This is a "
        "SERP intent mismatch for our product page. Even with 126+ RDs, ranking here for the B2B "
        "angle is unrealistic. Recommend deprioritising this keyword or retargeting to "
        "'loyalty points system' or 'loyalty points software' instead."
    ),
}


def median(values):
    v = [x for x in values if x is not None]
    if not v:
        return None
    return statistics.median(v)


def compute_gap_dr50(kw_meta, serp_rows):
    """Same logic as compute_gap but using DR50+ referring-domain counts."""
    our_url_key = (kw_meta.get("our_url_in_serp") or "").rstrip("/")
    # map our focus page URL to DR50+ count — use exact match, then prefix match
    our_rd50 = 0
    if our_url_key:
        # Try exact match first
        for key, val in OUR_PAGE_RD_DR50.items():
            if our_url_key == key.rstrip("/"):
                our_rd50 = val
                break
        else:
            # Fall back to substring (longer key wins to avoid homepage matching everything)
            best_key, best_val = "", 0
            for key, val in OUR_PAGE_RD_DR50.items():
                if key.rstrip("/") in our_url_key and len(key) > len(best_key):
                    best_key, best_val = key, val
            if best_key:
                our_rd50 = best_val

    seen = set()
    top5_rds = []
    for pos, url, dr, ur, rd, traffic in sorted(serp_rows, key=lambda r: r[0]):
        url_clean = url.split("?")[0].rstrip("/")
        if url_clean in seen:
            continue
        seen.add(url_clean)
        if our_url_key and our_url_key in url_clean:
            continue
        if len(top5_rds) < 5:
            top5_rds.append(_lookup_comp_dr50(url_clean))

    med = median(top5_rds)
    if med is None:
        return None, None
    gap = max(0, round(med) - our_rd50)
    return our_rd50, round(med), gap


def compute_gap(kw_meta, serp_rows):
    our_rd = kw_meta["our_page_rd"]
    our_url_fragment = kw_meta.get("our_url_in_serp", "")

    # Top-5 positions (deduplicated by URL, excluding our own page)
    seen = set()
    top5_rds = []
    for pos, url, dr, ur, rd, traffic in sorted(serp_rows, key=lambda r: r[0]):
        url_clean = url.split("?")[0].rstrip("/")
        if url_clean in seen:
            continue
        seen.add(url_clean)
        # skip our own page
        if our_url_fragment and our_url_fragment.rstrip("/") in url_clean:
            continue
        if len(top5_rds) < 5 and rd is not None:
            top5_rds.append(rd)

    med = median(top5_rds)
    if med is None:
        return None, None, None

    gap = max(0, round(med) - our_rd)
    target = round(med) + 10   # slightly above median
    return round(med), gap, target


def build_rows():
    rows = []
    for kw in KEYWORDS:
        serp_rows = SERP[kw["keyword"]]
        med, gap, target = compute_gap(kw, serp_rows)
        our_rd50, med50, gap50 = compute_gap_dr50(kw, serp_rows)
        rows.append({
            "id":          kw["id"],
            "keyword":     kw["keyword"],
            "focus_page":  kw["focus_page"],
            "our_pos":     kw["our_pos_in_serp"],
            "our_pos_gsc": GSC_POSITIONS.get(kw["keyword"]),
            "our_rd":      kw["our_page_rd"],
            "median_rd":   med,
            "gap":         gap,
            "target_rd":   target,
            "new_bl":      gap if gap and gap > 0 else 0,
            "our_rd50":    our_rd50,
            "median_rd50": med50,
            "gap50":       gap50,
            "note":        SERP_NOTES[kw["keyword"]],
        })
    return rows


# ── CSV ───────────────────────────────────────────────────────────────────────

def write_csv(rows, path):
    fieldnames = [
        "id", "keyword", "focus_page",
        "our_position_ahrefs", "our_position_gsc_may2026",
        "our_page_refdomains", "median_competitor_refdomains_top5",
        "gap",
        "our_page_refdomains_dr50plus", "median_competitor_refdomains_dr50plus",
        "gap_dr50plus",
        "recommended_target_refdomains", "new_backlinks_to_acquire",
        "serp_character_notes",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "id":                                      r["id"],
                "keyword":                                 r["keyword"],
                "focus_page":                              r["focus_page"],
                "our_position_ahrefs":                     r["our_pos"],
                "our_position_gsc_may2026":                r["our_pos_gsc"] if r["our_pos_gsc"] else "—",
                "our_page_refdomains":                     r["our_rd"],
                "median_competitor_refdomains_top5":       r["median_rd"],
                "gap":                                     r["gap"],
                "our_page_refdomains_dr50plus":            r["our_rd50"],
                "median_competitor_refdomains_dr50plus":   r["median_rd50"],
                "gap_dr50plus":                            r["gap50"],
                "recommended_target_refdomains":           r["target_rd"],
                "new_backlinks_to_acquire":                r["new_bl"],
                "serp_character_notes":                    r["note"],
            })
    print(f"CSV written → {path}")


# ── DOCX helpers ─────────────────────────────────────────────────────────────

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


def add_run(para, text, bold=False, italic=False, color=None, size=None):
    run = para.add_run(text)
    run.bold       = bold
    run.italic     = italic
    run.font.name  = FONT_NAME
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


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    if level == 1:
        style_para(p, space_before=14, space_after=6)
        add_run(p, text, bold=True, color=BRAND_BLUE, size=16)
        set_para_border_bottom(p, "1A56DB")
    elif level == 2:
        style_para(p, space_before=10, space_after=4)
        add_run(p, text, bold=True, color=DARK_GRAY, size=12)
    else:
        style_para(p, space_before=8, space_after=3)
        add_run(p, text, bold=True, color=MED_GRAY, size=10)
    return p


def add_body(doc, text, size=10):
    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=4)
    add_run(p, text, size=size, color=DARK_GRAY)
    return p


def add_kpi_row(doc, items):
    """items = list of (label, value) tuples, up to 4."""
    tbl = doc.add_table(rows=1, cols=len(items))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (lbl, val) in enumerate(items):
        cell = tbl.rows[0].cells[i]
        set_cell_bg(cell, LIGHT_BG)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after  = Pt(6)
        r1 = p.add_run(str(val) + "\n")
        r1.bold = True
        r1.font.name = FONT_NAME
        r1.font.size = Pt(14)
        r1.font.color.rgb = BRAND_BLUE
        r2 = p.add_run(lbl)
        r2.font.name  = FONT_NAME
        r2.font.size  = Pt(8)
        r2.font.color.rgb = MED_GRAY
    doc.add_paragraph()


def gap_color(gap):
    if gap is None:
        return MED_GRAY
    if gap == 0:
        return GREEN
    if gap <= 20:
        return RGBColor(0xF5, 0x9E, 0x0B)   # amber
    return WARN_RED


def write_docx(rows, path):
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin   = Cm(2.5)
    sec.right_margin  = Cm(2.5)
    sec.top_margin    = Cm(2.0)
    sec.bottom_margin = Cm(2.0)

    # ── Cover block ──────────────────────────────────────────────────────────
    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=2)
    add_run(p, "OPEN LOYALTY", bold=True, color=BRAND_BLUE, size=10)

    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=6)
    add_run(p, "Backlink Gap Analysis — Top 10 Priority Keywords", bold=True, size=22, color=DARK_GRAY)

    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=2)
    add_run(p, "Data source: Ahrefs SERP Overview & Site Explorer  |  Market: US  |  Date: June 2026",
            italic=True, size=9, color=MED_GRAY)

    p = doc.add_paragraph()
    style_para(p, space_before=0, space_after=16)
    add_run(p, "Domain: openloyalty.io  |  DR ~69  |  ~1,806 total referring domains",
            size=9, color=MED_GRAY)

    # ── Domain KPI strip ─────────────────────────────────────────────────────
    add_heading(doc, "Domain Overview", level=1)
    add_kpi_row(doc, [
        ("Domain Rating (DR)", "69"),
        ("Total Referring Domains", "1,806"),
        ("Live Backlinks", "5,408"),
        ("Organic Keywords", "1,553"),
    ])

    # ── Summary table ─────────────────────────────────────────────────────────
    add_heading(doc, "Summary: Backlink Gap by Keyword", level=1)

    col_headers = [
        "#", "Keyword", "Focus Page", "Pos\n(Ahrefs)", "Pos\n(GSC May)",
        "Our\nRDs", "Median\nRDs\n(top5)", "Gap",
        "Our\nRDs\nDR50+", "Median\nRDs\nDR50+", "Gap\nDR50+",
        "Target\nRDs", "New BLs\nNeeded",
    ]
    col_widths = [Cm(0.5), Cm(3.0), Cm(2.8), Cm(1.3), Cm(1.3), Cm(1.2), Cm(1.5), Cm(1.0), Cm(1.2), Cm(1.5), Cm(1.0), Cm(1.2), Cm(1.2)]

    tbl = doc.add_table(rows=1, cols=len(col_headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row
    hrow = tbl.rows[0]
    for i, (hdr, w) in enumerate(zip(col_headers, col_widths)):
        cell = hrow.cells[i]
        cell.width = w
        set_cell_bg(cell, BRAND_BLUE)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(hdr)
        r.bold = True
        r.font.name = FONT_NAME
        r.font.size = Pt(8)
        r.font.color.rgb = WHITE

    # Data rows
    for idx, row in enumerate(rows):
        tr = tbl.add_row()
        bg = LIGHT_BG if idx % 2 == 0 else WHITE

        gsc_pos = row["our_pos_gsc"]
        vals = [
            str(row["id"]),
            row["keyword"],
            row["focus_page"],
            str(row["our_pos"]),
            f"{gsc_pos:.1f}" if gsc_pos else "—",
            str(row["our_rd"]),
            str(row["median_rd"])   if row["median_rd"]   is not None else "n/a",
            str(row["gap"])         if row["gap"]         is not None else "n/a",
            str(row["our_rd50"])    if row["our_rd50"]    is not None else "n/a",
            str(row["median_rd50"]) if row["median_rd50"] is not None else "n/a",
            str(row["gap50"])       if row["gap50"]       is not None else "n/a",
            str(row["target_rd"])   if row["target_rd"]   is not None else "n/a",
            str(row["new_bl"])      if row["gap"]         is not None else "n/a",
        ]
        aligns = [
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ]
        for i, (val, align, w) in enumerate(zip(vals, aligns, col_widths)):
            cell = tr.cells[i]
            cell.width = w
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            p.alignment = align
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after  = Pt(2)
            color = DARK_GRAY
            if i == 7:   # Gap (all RDs)
                color = gap_color(row["gap"])
            elif i == 10:  # Gap DR50+
                color = gap_color(row["gap50"])
            r = p.add_run(val)
            r.font.name  = FONT_NAME
            r.font.size  = Pt(8)
            r.font.color.rgb = color
            if i in (7, 10) and val not in ("0", "n/a"):
                r.bold = True

    doc.add_paragraph()

    # ── Per-keyword detail sections ───────────────────────────────────────────
    add_heading(doc, "Per-Keyword Detail", level=1)

    for row in rows:
        add_heading(doc, f"#{row['id']} — {row['keyword'].title()}", level=2)

        gsc_pos_str = f"{row['our_pos_gsc']:.1f}" if row["our_pos_gsc"] else "—"
        add_kpi_row(doc, [
            ("Focus Page", row["focus_page"]),
            ("Pos (Ahrefs)", str(row["our_pos"])),
            ("Pos (GSC May '26)", gsc_pos_str),
            ("Gap", f"+{row['gap']} RDs" if row["gap"] else "No gap"),
        ])

        # SERP table for this keyword
        serp_rows = sorted(SERP[row["keyword"]], key=lambda r: r[0])
        our_url_frag = ""
        for kw in KEYWORDS:
            if kw["keyword"] == row["keyword"]:
                our_url_frag = kw.get("our_url_in_serp") or ""

        stbl = doc.add_table(rows=1, cols=6)
        stbl.alignment = WD_TABLE_ALIGNMENT.LEFT
        sh_headers = ["Pos", "URL", "DR", "UR", "Ref. Domains", "Traffic"]
        sh_widths  = [Cm(0.8), Cm(7.5), Cm(0.9), Cm(0.9), Cm(1.6), Cm(1.5)]
        shr = stbl.rows[0]
        for i, (h, w) in enumerate(zip(sh_headers, sh_widths)):
            c = shr.cells[i]
            c.width = w
            set_cell_bg(c, DARK_GRAY)
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r2 = p.add_run(h)
            r2.bold = True
            r2.font.name = FONT_NAME
            r2.font.size = Pt(7.5)
            r2.font.color.rgb = WHITE

        seen_urls = set()
        for pos, url, dr, ur, rd, traffic in serp_rows:
            url_clean = url.split("?")[0].rstrip("/")
            if url_clean in seen_urls:
                continue
            seen_urls.add(url_clean)

            is_ours = our_url_frag and our_url_frag.rstrip("/") in url_clean
            tr2 = stbl.add_row()
            row_bg = RGBColor(0xEB, 0xF5, 0xFF) if is_ours else WHITE
            cell_vals = [
                str(pos),
                url[:70] + ("…" if len(url) > 70 else ""),
                str(dr)      if dr      is not None else "—",
                str(ur)      if ur      is not None else "—",
                str(rd)      if rd      is not None else "—",
                str(traffic) if traffic is not None else "—",
            ]
            cell_aligns = [
                WD_ALIGN_PARAGRAPH.CENTER,
                WD_ALIGN_PARAGRAPH.LEFT,
                WD_ALIGN_PARAGRAPH.CENTER,
                WD_ALIGN_PARAGRAPH.CENTER,
                WD_ALIGN_PARAGRAPH.CENTER,
                WD_ALIGN_PARAGRAPH.CENTER,
            ]
            for i, (v, al, w) in enumerate(zip(cell_vals, cell_aligns, sh_widths)):
                c = tr2.cells[i]
                c.width = w
                set_cell_bg(c, row_bg)
                p = c.paragraphs[0]
                p.alignment = al
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after  = Pt(1)
                r3 = p.add_run(v)
                r3.font.name  = FONT_NAME
                r3.font.size  = Pt(7.5)
                r3.font.color.rgb = BRAND_BLUE if is_ours else DARK_GRAY
                if is_ours:
                    r3.bold = True

        doc.add_paragraph()

        # SERP character note
        p = doc.add_paragraph()
        style_para(p, space_before=2, space_after=8)
        add_run(p, "SERP Character: ", bold=True, size=9, color=DARK_GRAY)
        add_run(p, SERP_NOTES[row["keyword"]], size=9, color=MED_GRAY)

    # ── Strategic recommendations ─────────────────────────────────────────────
    add_heading(doc, "Strategic Recommendations", level=1)

    recs = [
        ("Quick wins (small gap, we already rank)",
         "• KW2 (best white label loyalty app, pos 2): acquire 5–10 links to /applications/white-label-loyalty "
         "from agency directories, white-label software reviews, and SaaS partner blogs to hold pos 2.\n"
         "• KW8 (loyalty program api, pos 2): get 10–15 links from developer blogs, GitHub READMEs, "
         "API marketplace listings, and developer-tools roundups to /technology/loyalty-program-api."),

        ("High-priority gaps (pages missing backlinks)",
         "• KW3 (best customer loyalty software) + KW1 (customer loyalty software): "
         "The comparison guide (/insider/best-loyalty-software-comparison-guide) needs ~25 external links. "
         "Target: software-review publications, mid-DR loyalty & CRM blogs, and listicle inclusion requests.\n"
         "• KW6 (customer loyalty platform) + KW9 (gamification in loyalty programs): "
         "Both product/resource pages have zero backlinks. Prioritise 20–30 targeted links each via "
         "guest posts, partner citations, and PR outreach."),

        ("Homepage keywords (KW4 & KW7 — content, not backlinks)",
         "The homepage already has 728 referring domains — more than the median of competing pages. "
         "Moving from pos 4 → pos 1–2 on 'loyalty program software' and 'loyalty system' is a "
         "content/on-page problem: strengthen the homepage's topical relevance signal and improve "
         "click-through rate rather than acquiring more links."),

        ("SERP intent mismatch — deprioritise",
         "KW10 (loyalty points): The SERP is dominated by American Airlines AAdvantage pages. "
         "This is a navigational/consumer intent keyword. Redirect effort to 'loyalty points software', "
         "'loyalty points system', or 'points-based loyalty program' where B2B content can rank."),

        ("Review-site strategy (KW1, KW3, KW6)",
         "G2, Gartner, GetApp, and Capterra hold multiple positions in the high-intent software SERPs. "
         "Ensuring Open Loyalty has strong review profiles (volume + recency) on these platforms "
         "indirectly supports rankings by providing high-DR citation links and brand authority signals."),
    ]

    for title, body in recs:
        add_heading(doc, title, level=3)
        add_body(doc, body, size=9)

    doc.save(path)
    print(f"DOCX written → {path}")


if __name__ == "__main__":
    rows = build_rows()
    csv_path  = Path(__file__).parent / "backlink_gap_analysis.csv"
    docx_path = Path(__file__).parent / "backlink_gap_2026.docx"
    write_csv(rows, csv_path)
    write_docx(rows, docx_path)
