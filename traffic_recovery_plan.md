# Traffic Recovery Action Plan — March → May 2026
**Generated:** 2026-06-16  
**Scope:** Pages that lost clicks or organic visibility between March 2026 (peak: 7,038 clicks) and May 2026 (5,054 clicks, −28%)  
**Data sources:** Google Search Console (March 1–31 vs May 1–22) · Ahrefs Site Explorer (March → June delta)

---

## Executive Summary

Total click loss (GSC): **~2,000 clicks/month** from peak  
Total Ahrefs traffic delta (top losers): **~4,900 estimated monthly visits lost**  
Pages affected: **25+** with measurable decline  

Root causes break into **5 distinct buckets**. Each requires a different intervention:

| # | Root Cause | Pages | Recommended Action |
|---|-----------|-------|-------------------|
| 1 | Brand SERP displacement | Sephora, Starbucks, Nike | Reframe as brand commentary → owned SERP angle |
| 2 | Keyword cannibalization | Mobile apps (2 URLs) | Merge into one canonical page |
| 3 | Freshness/algorithm drop | Phil Hussey, Referral Software, Implementation | Full content refresh + authority signals |
| 4 | Deleted/moved pages with no replacement | ~6 null-URL entries | Audit redirects; create or restore content |
| 5 | Product page keyword erosion | CRM, Points, Coupon, SaaS | On-page refresh + internal link reinforcement |

---

## Group 1 — Brand SERP Displacement

**Diagnosis:** These pages ranked by borrowing authority from famous brand names (Sephora, Starbucks, Nike). In Q2 2026, the official brands improved their own SERP presence, pushing our "analysis" pages down 2–4 positions into the click-cliff below position 7.

### Affected Pages

| Page | GSC Click Loss | Position March | Position May | Ahrefs Δ |
|------|---------------|----------------|--------------|----------|
| /insider/sephora-beauty-insider | −249 | 3.9 | 7.9 | n/a |
| /insider/starbucks-rewards-program | −242 | 5.6 | 8.9 | −195 |
| /insider/how-the-nike-customer-loyalty-program-works | −137 | 5.2 | 6.2 | n/a |

### Root Cause
Official brand pages (sephora.com/loyalty, starbucks.com/rewards) pushed into positions 1–3 for their own brand + loyalty terms. Our editorial pages now sit below them with no differentiation signal.

### Action Plan

**1a. Sephora Beauty Insider — Priority: HIGH**
- Current angle: program description (replicates what Sephora already says)
- New angle: **"Is Sephora Beauty Insider Worth It? An Independent Analysis (2026)"** — add reviewer verdict, comparison table vs. Ulta/NARS, updated earn/burn rates
- Add: Schema `Review` markup with `ratingValue` and `reviewBody`
- Add: "Last updated" timestamp in H1 area + changelog section at bottom
- Target: reclaim position 4–5 for "sephora loyalty program" and own "sephora beauty insider worth it" (informational sub-query)
- **Estimated effort:** 3–4 hours content work

**1b. Starbucks Rewards — Priority: HIGH**
- Same pattern: add independent value analysis, 2026 point redemption rates, comparison vs. Dunkin, Panera
- Add: FAQ schema block (Google is showing FAQs for this SERP)
- Target position: 6–8 is acceptable if impressions stay high; push for 5
- **Estimated effort:** 2–3 hours

**1c. Nike Customer Loyalty Program — Priority: MEDIUM**
- Smaller absolute loss but still −137 clicks
- Add Nike vs. Adidas vs. Puma comparison table; add "NikePlus exclusive benefits" section to capture long-tail
- **Estimated effort:** 2 hours

**Accept/Monitor:** Do not attempt to outrank Sephora or Starbucks for exact brand head terms — that battle cannot be won. Focus on sub-queries where official brand pages don't rank: "worth it?", "how to maximize", "compared to", "explained".

---

## Group 2 — Keyword Cannibalization (MERGE REQUIRED)

**Diagnosis:** Two pages cover identical user intent ("best mobile loyalty apps"). Both are losing traffic simultaneously — a textbook cannibalization signal. Google cannot determine which to rank and has split authority between them, causing both to underperform.

### Affected Pages

| Page | Ahrefs Mar | Ahrefs Jun | Δ Traffic | GSC Mar Clicks | GSC May Clicks | Δ Clicks |
|------|-----------|-----------|-----------|----------------|----------------|---------|
| /resources/10-best-mobile-loyalty-program-apps | 1,322 | 446 | **−876** | ~120 est | ~42 est | **−78** |
| /insider/10-best-mobile-loyalty-program-apps-full-report | n/a | n/a | −42 | n/a | n/a | **−28** |

### Action Plan — MERGE INTO ONE URL

**Step 1:** Decide canonical URL (recommended: keep `/resources/10-best-mobile-loyalty-program-apps` — shorter, cleaner, stronger backlink profile)

**Step 2:** Merge content from `/insider/10-best-mobile-loyalty-program-apps-full-report` into the `/resources/` page:
- Preserve any unique sections from the "full report" (depth, data, screenshots)
- Update the combined page to reflect 2026 app store rankings, download counts, feature changes
- Rename H1 to: **"10 Best Mobile Loyalty Program Apps (2026): Full Analysis"** — combines both the list and the report angle

**Step 3:** 301 redirect `/insider/10-best-mobile-loyalty-program-apps-full-report` → `/resources/10-best-mobile-loyalty-program-apps`

**Step 4:** Internal links — update any pages linking to the old `/insider/` URL to point to canonical

**Step 5:** Re-submit canonical URL in GSC for re-crawling

**Expected outcome:** Consolidated page recovers ~60–70% of combined lost traffic within 60–90 days post-merge. Target: reclaim position 10–12 → push to 8–10 for "best mobile loyalty program apps".

**Estimated effort:** 4–5 hours (content merge + redirect + internal link audit)

---

## Group 3 — Freshness / Algorithm Visibility Loss

**Diagnosis:** Pages that held strong positions historically but have not been updated recently. Google's freshness signals, combined with potential algorithm adjustments in Q1 2026 (multiple minor core updates detected in this period), have pushed these pages down disproportionately — more than competitors improved.

### 3a. Best Loyalty Software Comparison Guide
`/insider/best-loyalty-software-comparison-guide`

| Metric | March | May/June |
|--------|-------|---------|
| GSC Clicks | est. 150 | est. 35 | 
| GSC Position | 6.7 | 10.0 |
| Ahrefs Traffic | 872 | 107 |
| Ahrefs Keywords | −66 keywords lost |

**Action: FULL REFRESH — Priority: VERY HIGH (this is a conversion-relevant page)**
- Audit all listed vendors — verify current pricing, features (tools change fast)
- Add/update 2026 scoring criteria: AI features, mobile-first, headless API, composable architecture
- Add comparison table with live pricing columns
- Target query expansion: "loyalty software comparison 2026", "best loyalty platform for enterprise", "open source loyalty software"
- Add: `ItemList` + `SoftwareApplication` schema
- Internal links FROM this page TO /product/* pages — reinforce conversion path
- **Estimated effort:** 6–8 hours (research + rewrite)

### 3b. Best Retail Loyalty Programs
`/insider/best-retail-loyalty-programs`

| Metric | March | May/June |
|--------|-------|---------|
| Ahrefs Traffic | 1,039 | 416 |
| Ahrefs Keywords | −29 keywords lost |
| Position change | 2 → 3 |

**Action: CONTENT UPDATE — Priority: HIGH**
- Replace or update any programs that changed/ended their loyalty scheme since 2024
- Add 2026 data points: NPS scores, redemption rates, member growth where public
- Expand "key takeaway for brands" section — this is what B2B readers (our ICPs) actually want
- New section: "What makes a great retail loyalty program in 2026?" — captures emerging query cluster
- **Estimated effort:** 4–5 hours

### 3c. Restaurant Loyalty Programs
`/insider/restaurant-loyalty-programs`

| Metric | March | May/June |
|--------|-------|---------|
| GSC Clicks | est. 190 | est. 49 |
| GSC Position | 5.3 | 6.0 |
| Ahrefs Traffic | 2,065 | 1,692 |
| Ahrefs Keywords | −28 keywords lost |

**Action: CONTENT UPDATE — Priority: HIGH**
- Update all listed programs (Chick-fil-A, McDonald's MyMcDonald's Rewards, etc.) with 2026 offer structures
- Starbucks section needs separate treatment given its own page — link there instead of duplicating
- Add: mobile ordering tie-in section (big growth area for restaurant loyalty in 2026)
- **Estimated effort:** 3–4 hours

### 3d. Phil Hussey Interview
`/insider/designing-a-loyalty-program-strategy-phil-hussey`

| Metric | March | May/June |
|--------|-------|---------|
| Ahrefs Traffic | 368 | 60 |
| Ahrefs Keywords | −16 keywords lost |
| Position change | 2 → 1 (but traffic collapsed) |

**Diagnosis:** This is a dated interview — position improved but estimated traffic collapsed, suggesting Google is ranking it for very niche/long-tail queries that get almost no search volume. The page was likely carried by a few high-volume terms it no longer ranks for.

**Action: REPURPOSE — Priority: LOW-MEDIUM**
- Keep the URL and interview content (historical backlinks may exist)
- Add a "2026 Editor's Note" section at top synthesizing current best practices from the interview's themes
- Re-target: "loyalty program strategy framework" rather than Phil's name as primary keyword
- Alternative: Convert to evergreen "Loyalty Program Strategy: Expert Guide" with the interview as one cited source
- **Estimated effort:** 3–4 hours (repurpose/reframe)

### 3e. Best Referral Software
`/insider/best-referral-software`

| Metric | March | May/June |
|--------|-------|---------|
| Ahrefs Traffic | 247 | 13 |
| Ahrefs Keywords | −21 keywords lost |
| Position change | 4 → 8 |

**Diagnosis:** Catastrophic drop. Position 4→8 explains the click collapse (positions 5–8 get dramatically fewer clicks). This topic area (referral software) has high commercial intent and is heavily contested by dedicated SaaS review sites (G2, Capterra, GetApp).

**Action: EVALUATE RELEVANCE FIRST — Priority: MEDIUM**
- Is referral software core to Open Loyalty's ICP? If not, deprioritize.
- If yes: full competitive content audit — check what pages now rank 1–4 and what they offer that ours doesn't
- Key gap likely: lack of 2025–2026 product data, pricing tables, verified user quotes
- If deprioritizing: add a redirect to /product/ or /applications/ page that covers referral within loyalty context
- **Estimated effort:** 2 hours audit + decision; 5–6 hours full refresh if proceeding

### 3f. Loyalty Program Implementation Guide
`/resources/loyalty-program-implementation`

| Metric | March | May/June |
|--------|-------|---------|
| GSC Clicks | est. 100 | est. 14 |
| GSC Position | 10.2 | 16.8 |
| Ahrefs Traffic | 199 | 38 |
| Ahrefs Keywords | −27 keywords lost |

**Diagnosis:** Dramatic position drop (10→17) across many keywords. This is a high-value page for our ICP (someone researching how to implement a loyalty program = late-funnel). The drop suggests content quality/depth issue vs. competitors.

**Action: PRIORITY REFRESH — Priority: VERY HIGH (high conversion potential)**
- This page likely converts — see it as bottom-of-funnel content
- Add: phased implementation timeline with milestones
- Add: integration checklist (POS, CRM, mobile app, API)
- Add: cost estimation guide section
- Add: "Download implementation checklist" CTA (lead magnet opportunity)
- Target queries: "loyalty program implementation checklist", "how to implement a loyalty program", "loyalty platform implementation cost"
- **Estimated effort:** 5–6 hours

---

## Group 4 — Deleted / Moved Pages Without Proper Handling

**Diagnosis:** Ahrefs identified 6+ null-URL entries (pages that existed in March but returned no URL in June). These are likely: deleted pages, URL structure changes without 301 redirects, or pages taken behind login. Combined lost traffic from these: ~200 estimated monthly visits.

### Action Plan

**Step 1: Identify all null-URL pages**
Run an Ahrefs crawl comparison or check the "Lost pages" report in Ahrefs → Site Explorer → Pages → Best by Links filter (lost).

**Step 2: For each deleted/moved page:**

| Scenario | Action |
|----------|--------|
| Page deleted, content still valuable | Restore the page at its original URL |
| Page merged into another URL | Ensure 301 redirect exists from old → new |
| Page deleted, content obsolete | Ensure 301 to most relevant live alternative |
| URL structure changed (e.g. /blog/ → /insider/) | Audit redirect chain — ensure no 302s or redirect loops |

**Step 3: Audit all 301 redirects**
- Use Screaming Frog or Ahrefs broken backlinks report
- Identify any redirect chains longer than 1 hop — flatten to direct 301
- Check redirect destination relevance — generic homepage redirects waste link equity

**Step 4: Submit updated sitemap in GSC after restoring/redirecting**

**Estimated effort:** 3–4 hours audit + 1–2 hours implementation

---

## Group 5 — Product Page Keyword Erosion

**Diagnosis:** Core product pages are losing keyword rankings gradually. These pages don't have the dramatic drops of content pages, but the losses are significant because these pages are closest to conversion.

### Affected Pages

| Page | Ahrefs Mar | Ahrefs Jun | Δ | Keywords Lost | Position |
|------|-----------|-----------|---|---------------|---------|
| /product/loyalty-program-crm-software | 219 | 59 | −160 | −11 | 2→2 |
| /applications/saas-enrichment | 289 | 168 | −121 | −9 | 1→1 |
| /product/loyalty-points-system | 268 | 161 | −107 | −15 | 1→2 |
| /product/coupon-software | 208 | 110 | −98 | −7 | 1→1 |

### Action Plan

**5a. /product/loyalty-program-crm-software — Priority: HIGH**
- Most clicks lost among product pages
- Audit: does the page clearly explain CRM + loyalty integration? Specifically: member segmentation, lifecycle campaigns, behavioral triggers
- Add: feature comparison table vs. generic CRM (Salesforce, HubSpot) — show why a loyalty-native CRM wins
- Add: "How it works" technical section targeting "loyalty CRM API" queries
- Ensure: prominent CTA (demo/contact) above fold

**5b. /product/loyalty-points-system — Priority: HIGH**
- Lost 15 keywords despite holding position 1→2
- The keywords lost are likely long-tail variants — add FAQ section covering: "how do loyalty points work", "types of loyalty points", "points expiration rules", "loyalty points vs. cashback"
- Add: Schema `FAQPage` markup

**5c. /applications/saas-enrichment — Priority: MEDIUM**
- Lost 9 keywords; position held at 1
- Likely losing long-tail around use-case queries
- Add: industry-specific use case sections (fintech, retail, airline) — these generate long-tail keyword clusters
- Ensure page is internally linked from blog/insider content about enrichment

**5d. /product/coupon-software — Priority: MEDIUM**
- Lost 7 keywords
- Same play: add FAQ, use case sections, integration examples
- Cross-link with /insider/loyalty-vs-promotions type content if it exists

**General product page improvements (all 4 pages):**
- Ensure each page has a clear `H2` structure covering: what it is, who it's for, key features, integrations, ROI/outcomes
- Add customer quotes or mini case studies scoped to the product feature
- Internal linking: ensure every major blog/insider page that mentions these features links back to the product page

---

## Group 6 — Homepage Traffic Loss

`/` (homepage)

| Metric | March | May |
|--------|-------|-----|
| GSC Clicks | ~1,200 est | ~779 est |
| GSC Click Loss | **−421** |
| GSC Impressions | 105,000 | 65,000 |
| GSC Position | 11.8 | 11.1 |
| Ahrefs Traffic | 2,102 | 1,714 |
| Ahrefs Traffic Δ | **−388** |

**Diagnosis:** Impressions dropped from 105k to 65k — this is the critical signal. It means Google is showing our homepage in fewer SERPs, not just clicking through less. The position actually improved (11.8 → 11.1), which rules out a ranking penalty. The issue is **keyword footprint reduction** — the homepage lost ~11 keyword rankings entirely.

### Action Plan — Priority: HIGH

**6a. Technical / Crawl Check**
- Verify no accidental `noindex` or crawl issues were introduced between March and May
- Check Core Web Vitals in GSC — any LCP/CLS regressions after site updates?
- Confirm hreflang tags are correct (homepage ranks for multiple markets)

**6b. Content / Brand Query Coverage**
- Impressions loss of 40k+ suggests branded + navigational queries may be affected
- Check GSC Queries report for homepage specifically: which queries drove impressions in March that disappeared in May?
- If brand query volume itself dropped: investigate brand awareness (PR, social, news)

**6c. Internal Link Audit**
- The homepage receives PageRank from all internal pages — ensure no pages were mistakenly removed or noindexed that previously flowed authority to homepage
- Sitemap: ensure homepage is listed correctly with correct `<lastmod>`

**6d. Structured Data**
- Add `Organization` schema with `sameAs` links (LinkedIn, Twitter, G2, Capterra profiles)
- Add `WebSite` schema with `SearchAction` for sitelinks search box

---

## Group 7 — Additional Visibility Losses (Monitor + Quick Fixes)

### 7a. /insider/how-to-build-customer-loyalty
- GSC position: 11.5 → **31.5** (fell off page 1 entirely)
- **Action:** Immediate content audit — this is a dramatic drop. Check if any site changes affected this URL. Consider: was the URL path changed? Any duplicate content created? 
- If content is intact: update with 2026 examples, add structured FAQ, submit for recrawl

### 7b. /insider/building-brand-loyalty
- GSC position: 7.2 → **16.2** (lost page 2 entirely)
- **Action:** Full content refresh — update examples, add statistics from 2025–2026, ensure E-E-A-T signals (author byline with credentials, cited sources)

### 7c. /resources/the-top-40-best-rewards-programs
- GSC Click Loss: **−77**, position 9.9 → 15.6
- **Action:** Verify all 40 programs are current and accurate; remove/replace defunct programs; add 2026 new entrants (particularly in B2B loyalty and fintech)

### 7d. /insider/bank-loyalty-programs
- GSC Click Loss: **−76**, position 6.5 → 7.3 (small position drop but noticeable click loss)
- Ahrefs: −86 traffic, −10 keywords
- **Action:** Update with 2026 banking loyalty trends (embedded finance, crypto rewards, sustainability rewards); this is lower priority than others

---

## Prioritized Action Queue

### Sprint 1 — Immediate (Week 1–2): Fix what's bleeding most

| Priority | Page | Action | Owner | Hours |
|----------|------|--------|-------|-------|
| P0 | /resources/10-best-mobile-loyalty-program-apps + /insider/10-best-mobile-loyalty-program-apps-full-report | MERGE + 301 redirect | SEO + Dev | 5h |
| P0 | /resources/loyalty-program-implementation | Full content refresh | Content | 6h |
| P1 | /insider/best-loyalty-software-comparison-guide | Full content refresh | Content | 8h |
| P1 | Deleted pages (null URLs) | Redirect audit + restore | Dev | 4h |
| P1 | / (homepage) | Technical audit + schema | SEO + Dev | 3h |

### Sprint 2 — High Impact (Week 3–4): Brand pages + freshness

| Priority | Page | Action | Owner | Hours |
|----------|------|--------|-------|-------|
| P1 | /insider/sephora-beauty-insider | Reframe + update + Review schema | Content | 4h |
| P1 | /insider/starbucks-rewards-program | Reframe + update + FAQ schema | Content | 3h |
| P2 | /insider/best-retail-loyalty-programs | Content update | Content | 5h |
| P2 | /insider/restaurant-loyalty-programs | Content update | Content | 4h |
| P2 | /product/loyalty-program-crm-software | Feature/CTA refresh | Content + Dev | 3h |
| P2 | /product/loyalty-points-system | FAQ section + schema | Content | 2h |

### Sprint 3 — Maintenance (Week 5–6): Long tail and monitoring

| Priority | Page | Action | Owner | Hours |
|----------|------|--------|-------|-------|
| P2 | /insider/how-to-build-customer-loyalty | Content refresh | Content | 3h |
| P2 | /insider/building-brand-loyalty | Content refresh + E-E-A-T | Content | 3h |
| P3 | /resources/the-top-40-best-rewards-programs | Update list | Content | 2h |
| P3 | /insider/bank-loyalty-programs | 2026 update | Content | 2h |
| P3 | /insider/how-the-nike-customer-loyalty-program-works | Update + comparison table | Content | 2h |
| P3 | /insider/best-referral-software | Decision: refresh or deprioritize | SEO | 2h |
| P3 | /insider/designing-a-loyalty-program-strategy-phil-hussey | Repurpose | Content | 4h |

---

## Cannibalization Watchlist

Pages to monitor for future cannibalization signals (overlapping topics):

| Cluster | URLs | Risk |
|---------|------|------|
| Mobile loyalty apps | /resources/10-best-mobile-loyalty-program-apps (canonical after merge) | Resolved after merge |
| Loyalty software reviews | /insider/best-loyalty-software-comparison-guide + any future "loyalty platform reviews" page | Monitor |
| Restaurant loyalty | /insider/restaurant-loyalty-programs + /insider/starbucks-rewards-program | Low (different scope) |
| Brand loyalty | /insider/building-brand-loyalty + /insider/how-to-build-customer-loyalty | Medium — check keyword overlap |

**Recommended:** Before creating any new content pages, run a keyword overlap check against existing URLs. Use Ahrefs Content Gap or GSC to confirm no existing page already targets the same primary keyword.

---

## Measurement — How to Know It's Working

Track these metrics monthly after each sprint:

| Metric | Tool | Baseline (May 2026) | Target (Sep 2026) |
|--------|------|--------------------|--------------------|
| Total organic clicks | GSC | ~5,054/month | ≥6,500/month |
| Clicks from refreshed pages | GSC | see per-page baselines above | +30% per page avg |
| Organic MQLs | HubSpot | 31/month | 40+/month |
| /resources/loyalty-program-implementation clicks | GSC | ~14/month | 80+/month |
| /insider/best-loyalty-software-comparison-guide clicks | GSC | ~35/month | 120+/month |
| Pages ranking top-10 | Ahrefs | track via rank tracker | +20% |
| Cannibalization: mobile apps page clicks | GSC | ~42/month | 100+/month |

**Review cadence:** GSC data lags 3 days. Review weekly during sprint execution, monthly for trend analysis.
