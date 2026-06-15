# SEO Growth Plan: 2× Organic MQL Leads by December 2026

**Prepared:** 2026-06-15  
**Goal:** Double MQL leads from organic traffic (~31/month → 62+/month)  
**Data sources:** GSC Jan–May 2026, Ahrefs June 2026, HubSpot 157 MQL contacts

---

## Baseline: Where We Are Now

### GSC Traffic Trend (monthly)
| Month | Clicks | Impressions | CTR | Avg Position |
|-------|--------|-------------|-----|--------------|
| Dec 2025 | 5,993 | 1.66M | 0.36% | 10.0 |
| Jan 2026 | 7,021 | 2.23M | 0.31% | 9.8 |
| Feb 2026 | 7,021 | 2.45M | 0.29% | 8.2 |
| Mar 2026 | 7,038 | 2.53M | 0.28% | **6.8** (peak) |
| Apr 2026 | 5,794 | 2.00M | 0.29% | 7.9 |
| May 2026 | 5,054 | 1.88M | 0.27% | 9.8 |

**⚠ Critical alert:** Clicks dropped 28% (March → May). Positions worsened from 6.8 → 9.8. This requires immediate diagnosis before anything else.

### Ahrefs Snapshot (June 2026)
- Organic keywords: **1,552** (619 in positions 1–3)
- Estimated monthly traffic: **16,126**
- Traffic value: **$62,690/month**
- Site health score: **99/100** (very clean technically)

### MQL Funnel (HubSpot, Jan–May 2026)
- Total MQL contacts from organic + direct: **157** (~31/month)
- Organic clicks/month: ~6,600
- **MQL conversion rate: ~0.47%** of organic clicks

### Self-Reported Attribution (157 MQLs)
| Channel | Count | % |
|---------|-------|---|
| Google | 49 | 31% |
| ChatGPT | 22 | 14% |
| Referral/WoM | 5 | 3.2% |
| AI (Gemini, Copilot, Claude, other) | 8 | 5.1% |
| Blog/Content | 2 | 1.3% |
| Other/unclear | 71 | 45% |

**Key insight:** ~19% of MQLs explicitly cite AI search tools (ChatGPT, Gemini, Claude, Copilot) as how they found Open Loyalty. This is a significant and growing channel with no current strategy.

---

## Core Diagnosis: The Conversion Gap

The fundamental problem is a **mismatch between traffic pages and conversion pages**:

### Pages with most organic traffic (Ahrefs):
| Page | Monthly Traffic | Top Keyword | Commercial Intent |
|------|----------------|-------------|-------------------|
| /insider/restaurant-loyalty-programs | 1,692 | restaurant rewards programs | Low |
| / (homepage) | 1,714 | retail loyalty program software | High |
| /insider/sephora-beauty-insider | 514 | sephora tiers | Very Low |
| /insider/bank-loyalty-programs | 469 | bank loyalty programs | Low |
| /resources/10-best-mobile-loyalty-program-apps | 446 | loyalty app | Low |
| /insider/best-retail-loyalty-programs | 416 | loyalty program retail | Medium |
| /resources/10-best-gamification-loyalty-programs | 392 | gamification rewards program | Low |

### Pages where MQLs actually come from (HubSpot):
| Page | MQL Count | Organic Traffic |
|------|-----------|-----------------|
| / (homepage) | ~60+ | 1,714 ✅ |
| /pricing | ~8 | Low ⚠ |
| /applications/white-label-loyalty | ~6 | 119 ⚠ |
| /technology/loyalty-program-api | ~4 | 90 ⚠ |
| /insider/best-loyalty-software-comparison-guide | ~4 | 107 ⚠ |

**The opportunity:** The pages that convert MQLs get very little organic traffic. The pages with lots of organic traffic convert almost nothing. The fastest path to 2× MQLs is routing more commercial-intent traffic to high-converting pages — not just growing overall traffic.

---

## Phase 0: Stop the Bleeding (June, Weeks 1–2)

Before building, fix what's breaking.

### 0.1 Diagnose the March→May Traffic Drop

18 pages dropped from Top 10, 18 pages with organic traffic dropping, avg position fell from 6.8 to 9.8 between March and May. Investigate:

- [ ] Pull the specific 18 pages that dropped from Top 10 in Ahrefs Site Audit
- [ ] Check if this correlates with a Google algorithm update (March 2026 core update?)
- [ ] Compare page content freshness — were any key pages not updated recently?
- [ ] Check if competitors published competing content in February–March
- [ ] Look at page speed / CWV regressions in GSC

### 0.2 Fix the 1 Noindex Page Getting Organic Traffic

Site Audit flagged 1 noindex page receiving organic traffic. This is leaking link equity.
- [ ] Identify the page
- [ ] Either remove the noindex tag (if the page should rank) or add a canonical/redirect

### 0.3 Submit 34 Pages to IndexNow

Site Audit flagged 34 "pages to submit to IndexNow" — this accelerates recrawling of updated content.
- [ ] Submit via IndexNow plugin or API call

### 0.4 Address Referring Domain Drop

3 referring domains were lost recently.
- [ ] Identify which domains and why (expired content? redirected links?)
- [ ] Attempt to recover or replace with equivalent links

---

## Q3 Focus: Convert More, Rank Higher on Commercial Keywords

**Q3 Goal:** 40 MQL/month by September (from 31 baseline)  
**Primary lever:** Improve conversion rate on existing traffic + quick-win rankings

---

### Initiative 1: Commercial Keyword Quick Wins (July)

These keywords are in positions 4–10 with real commercial intent. Small content improvements can push them into the top 3 where click rates jump from ~5% to ~25%+.

| Keyword | Volume | KD | Current Pos | Page | Target |
|---------|--------|----|-------------|------|--------|
| customer loyalty software | 700 | 49 | 5 | homepage | Top 3 |
| loyalty platform | 600 | 62 | 4 | homepage | Top 3 |
| loyalty management software | 350 | 54 | 4 | homepage | Top 3 |
| limited time offer | 2,700 | 15 | 8 | /insider/time-limited-offer | Top 5 |
| loyalty card | 1,400 | 9 | 9 | /product/loyalty-card-system | Top 5 |
| loyalty management platform | 400 | 53 | 6 | homepage | Top 3 |
| reward programs | 450 | 34 | 7 | /resources/top-40-rewards-programs | Top 5 |

**Actions for homepage (highest priority — 1,714 traffic, $18k value):**
- [ ] Add explicit H2/H3 headers targeting "customer loyalty software", "loyalty platform", "loyalty management software" — the page currently ranks for these via general content but lacks explicit targeting
- [ ] Add a comparison table vs Antavo, LoyaltyLion, Smile.io with direct keyword mentions
- [ ] Improve meta title: currently generic; test "Open Loyalty | #1 Customer Loyalty Software & Platform"
- [ ] Add Schema.org SoftwareApplication markup with explicit category tags
- [ ] Internal links from top blog posts to homepage with exact-match anchor text

**Actions for /insider/time-limited-offer:**
- [ ] The article ranks #8 for "limited time offer" (2,700 vol, KD 15) — this is a huge opportunity
- [ ] Expand article depth: add examples, add a framework/checklist section
- [ ] Add internal CTAs linking to product pages (promotions module, gamification software)

**Actions for /product/loyalty-card-system:**
- [ ] Ranks #9 for "loyalty card" (1,400 vol) — expand content, add FAQ schema
- [ ] Add case studies/examples section to increase dwell time

### Initiative 2: High-Traffic → MQL Conversion Rate Optimization (July–August)

The restaurant, Sephora, bank loyalty, and gamification articles get 1,700+ visits/month combined but send very few MQLs. Adding the right conversion elements could change this.

**For all major blog/insider posts:**
- [ ] Add a "See how Open Loyalty powers [topic] programs → Book a Demo" CTA at the 30% scroll mark (not just bottom)
- [ ] Add a sticky sidebar or inline widget: "Building a loyalty program? See our platform →"
- [ ] Create a dedicated "Loyalty Platform for [Restaurant/Retail/Finance]" landing page and link to it from the relevant blog posts (these industry pages will also capture their own SEO traffic)
- [ ] Add exit-intent popup on blog posts: "Download our [industry] loyalty program benchmark report"

**Specifically for /insider/sephora-beauty-insider (514 visits/month, 189 keywords):**
- [ ] This page ranks for "sephora tiers", "sephora points", "sephora beauty insider" — mostly brand-lookup traffic with near-zero commercial intent
- [ ] Instead of trying to convert this traffic, use it for brand awareness: add an inline content upgrade ("See how to build a tier system like Sephora's → Download free guide") to grow email list
- [ ] Do NOT invest further SEO effort here unless building a specific "Beauty & Cosmetics Loyalty" product page

**For /insider/best-loyalty-software-comparison-guide (107 traffic, ~4 MQLs):**
- [ ] This is your highest-converting informational page (estimated ~4% MQL rate)
- [ ] This page should be a priority. Push it from pos 3 → pos 1 for "best customer loyalty program software"
- [ ] Expand: add a "vs" comparison section for top 5 competitors (Antavo, LoyaltyLion, Smile.io, Emarsys, Salesforce Loyalty)
- [ ] Add trust signals: G2/Capterra badges, customer logos, review quotes
- [ ] Target keyword cluster: "loyalty software comparison", "best loyalty software", "loyalty platform comparison guide"

### Initiative 3: Unlock Low-KD Keyword Gaps (August–September)

These keywords have high volume and low difficulty but Open Loyalty ranks poorly — likely because there's no dedicated, optimized page.

| Keyword | Volume | KD | Current Pos | Gap Type |
|---------|--------|----|-------------|----------|
| gamification software | 1,600 | 5 | 37 | Need a focused page |
| customer retention management software | 800 | 3 | 31 | Product page needs expansion |
| customer retention software | 500 | 4 | 28 | Same as above |
| brand loyalty | 5,200 | 43 | 32 | Need a cornerstone article |
| how to build customer loyalty | 800 | 24 | 45 | Existing article needs upgrade |
| customer loyalty strategies | 450 | 12 | 49 | Same article |
| customer referral program | 600 | 37 | 50 | Existing page needs links |

**Actions:**

**Brand loyalty article** (5,200 vol/month, KD 43, pos 32):
- [ ] Create a comprehensive "What is Brand Loyalty?" guide — this is a top-of-funnel magnet that should rank top 5
- [ ] Structure: definition → why it matters → 5 stages → measurement → tactics → how Open Loyalty helps
- [ ] Target length: 3,000+ words with data/stats, examples (Nike, Apple, Amazon)
- [ ] Internally link to all commercial product pages
- [ ] This single article, if it reaches top 5, adds ~650 clicks/month

**Gamification software** (1,600 vol, KD 5, pos 37):
- [ ] /insider/best-gamification-software already exists but ranks #37 — very low KD means weak competitors
- [ ] Audit the existing article: likely too thin or lacks specific feature comparison
- [ ] Expand with: feature comparison table, pricing comparison, use cases, screenshots
- [ ] Add a dedicated product page /product/gamification-software if it doesn't exist

**Customer retention software** (800 vol, KD 3–4, pos 28–31):
- [ ] /product/customer-retention-software page exists but ranks #28–31 for very low KD keywords
- [ ] This is a commercial page that should rank top 5 with minimal effort given KD of 3–4
- [ ] Action: expand page content (2,000+ words), add comparison, add case studies, add FAQ schema
- [ ] This addresses a real product use case and should convert well when it ranks

**Spanish language content** (/es pages):
- [ ] You already have a Spanish homepage /es and blog posts
- [ ] MQLs are coming from Spain, Colombia, Peru, Argentina, Honduras
- [ ] "plataforma de fidelización" keyword is converting (Angel García, pos 1.6 in GSC)
- [ ] [ ] Translate and localize top 5 commercial pages into Spanish: /es/aplicaciones/white-label-loyalty, /es/tecnologia/loyalty-program-api, etc.
- [ ] [ ] Target Spanish B2B loyalty keywords: "software de fidelización", "plataforma de lealtad", "programa de fidelización empresarial"

---

## Q4 Focus: Scale Volume and AI/GEO Strategy

**Q4 Goal:** 62 MQL/month by December (true 2× baseline)  
**Primary levers:** Content volume, link building, AI search optimization, industry pages

---

### Initiative 4: Industry Landing Pages (October)

Your MQL contacts come from many industries. Creating dedicated "loyalty platform for [industry]" pages:
1. Captures industry-specific search intent that blogs cannot
2. Acts as conversion pages linked from informational blog posts
3. Builds topical authority in each vertical

**Pages to create (in priority order based on MQL volume):**

| Page URL | Primary Keyword | Volume | Rationale |
|----------|-----------------|--------|-----------|
| /applications/loyalty-platform-for-retail | loyalty program for retail | 350 | Retail is top industry, /insider/best-retail-loyalty-programs ranks #3 for "loyalty program retail" |
| /applications/loyalty-platform-for-finance | loyalty program for banks | 200 | Bank loyalty article gets 469 traffic/month, no product CTA destination |
| /applications/loyalty-platform-for-restaurants | restaurant loyalty program software | 250 | Restaurant article gets 1,692 traffic/month |
| /applications/loyalty-platform-for-healthcare | loyalty program for healthcare | 150 | "gamification healthcare" keyword converting MQLs |
| /applications/loyalty-platform-for-saas | saas loyalty program | 200 | /applications/saas-enrichment ranks #1 for "loyalty saas" |

**Each page should include:**
- Clear value prop for that specific industry
- Case study or client example from that industry
- Industry-specific features callout
- FAQ schema targeting 5–10 long-tail questions
- Link back to relevant blog posts
- Demo CTA above the fold

### Initiative 5: AI/GEO Search Optimization (October–November)

14% of your MQLs already discover Open Loyalty through ChatGPT, 5% through other AI tools (19% total). This will grow. Being cited by LLMs requires different optimization than traditional Google SEO.

**What to do:**

**Entity optimization:**
- [ ] Create or update an Open Loyalty Wikipedia/Wikidata entry (AI models use structured knowledge graphs)
- [ ] Ensure consistent NAP (name, address, product description) across Crunchbase, G2, Capterra, LinkedIn
- [ ] Create a dedicated "About Open Loyalty" factual page (/about/company or similar) with founding year, HQ, product category, funding, team size — all verifiable facts LLMs cite

**Structured data:**
- [ ] Add SoftwareApplication schema on all product pages with: applicationCategory, operatingSystem, offers, aggregateRating
- [ ] Add FAQPage schema on all blog posts (LLMs pull directly from FAQ structured data)
- [ ] Add Organization schema on homepage with sameAs links to Crunchbase, G2, LinkedIn, Wikipedia

**"AI-friendly" content:**
- [ ] On key pages (/applications/white-label-loyalty, /technology/loyalty-program-api, homepage), add a "Quick Summary" box at the top with 3–5 bullet points — this is what LLMs excerpt when citing
- [ ] Create a dedicated /about/open-loyalty-facts page with clear, citable statistics: what it is, who it's for, key differentiators, pricing model, API-first vs SaaS, deployment options
- [ ] Publish a quarterly "State of Loyalty" data report — LLMs and journalists cite original data heavily

**G2/Capterra presence:**
- [ ] Actively solicit reviews from existing clients (minimum 25 reviews needed to appear in AI recommendation lists)
- [ ] Respond to all reviews professionally
- [ ] Ensure your category tags on G2/Capterra match the keywords you're targeting: "loyalty management software", "customer loyalty software", "reward program software"

### Initiative 6: Competitor Comparison Pages (November)

These pages are proven high-intent converters — people searching "Open Loyalty vs Antavo" are deep in the buying journey.

**Pages to create:**
- [ ] /vs/antavo — "Open Loyalty vs Antavo: API-First vs Managed Service"
- [ ] /vs/loyaltylion — "Open Loyalty vs LoyaltyLion: Enterprise vs SMB"
- [ ] /vs/salesforce-loyalty — "Open Loyalty vs Salesforce Loyalty Management"
- [ ] /best-loyalty-software → upgrade the existing comparison guide to include 10 competitors

**Why Antavo and LoyaltyLion first:** They share the most keywords with you (260 and 236 respectively) and rank for the same commercial terms. Buyers comparing you to them are already qualified.

### Initiative 7: Link Building (October–December, ongoing)

Current competitor backlink profiles (approx, from Ahrefs):
- LoyaltyLion: DR 76
- Smile.io: DR 78
- Antavo: DR 73
- Open Loyalty: needs DR assessment

You're competing for KD 49–62 keywords (customer loyalty software, loyalty platform) against DR 73–78 sites. Closing this gap is essential for Q4 and beyond.

**Link acquisition strategy:**

**Tier 1: Digital PR (highest leverage):**
- [ ] Publish the "2026 Loyalty Program Benchmarks" data report (use HubSpot + GSC data)
- [ ] Pitch to retail/CRM/loyalty publications: Loyalty360, RetailCustomerExperience, CustomerThink
- [ ] Target journalists who cover loyalty marketing (LinkedIn + HARO)

**Tier 2: Guest posts on industry publications:**
- [ ] Target: Smile.io blog (they accept guest posts), CustomerThink, Business2Community
- [ ] Topic angles: "Why loyalty programs fail without an API-first architecture", "The ROI of white-label loyalty in 2026"

**Tier 3: Broken link building:**
- [ ] Find broken links on loyalty industry resource pages using Ahrefs
- [ ] Offer your updated content as a replacement

**Tier 4: Partnership links:**
- [ ] Request links from technology partners, integration partners, and existing enterprise clients
- [ ] Ensure all client case studies on your site are linked from the client's press page

---

## Technical SEO Cleanup (Ongoing, parallel with above)

These won't single-handedly drive 2× growth but prevent rankings from eroding.

### Priority Fixes (July)
| Issue | Pages Affected | Action |
|-------|---------------|--------|
| Missing alt text | 383 pages | Bulk fix — alt text should describe image AND include keyword where natural |
| Meta description too long | 84 pages | Trim to 150–160 characters |
| Meta description too short | 47 pages | Expand to 120–160 characters |
| Title too long | 80 pages | Trim to 55–60 characters |
| SERP title ≠ page title | 79 pages | Google is rewriting your titles — review and align |
| Title too short | 10 pages | Expand with keyword + brand |

### Indexability
- [ ] Review the 5 noindex pages — confirm each is intentionally noindexed
- [ ] Check the 1 noindex page receiving organic traffic (likely accidentally noindexed)
- [ ] Submit updated sitemap after all content changes

---

## Measurement Framework

### Weekly tracking (every Monday)
- GSC clicks by landing page (focus: homepage, /pricing, /applications/*, /technology/*)
- Ranking changes for 20 priority keywords (see list below)
- MQL count from previous week (HubSpot filter: source = organic/direct, lifecycle = MQL)

### Monthly tracking
- Total organic MQL count vs. 31/month baseline
- Organic clicks vs. 7,038/month March peak
- Conversion rate: organic clicks → MQL (baseline: 0.47%)
- AI attribution: % of MQLs citing ChatGPT/AI (baseline: 19%)

### 20 Priority Keywords to Track Weekly
| Keyword | Volume | Current Position | Target |
|---------|--------|-----------------|--------|
| customer loyalty software | 700 | 5 | 1–2 |
| loyalty platform | 600 | 4 | 1–2 |
| loyalty management software | 350 | 4 | 1–3 |
| loyalty platform saas | 150 | 1 | Hold |
| loyalty program software | 500 | 3 | 1–2 |
| loyalty software | 600 | 1 | Hold |
| loyalty program api | 200 | 1 | Hold |
| brand loyalty | 5,200 | 32 | 5–10 |
| gamification software | 1,600 | 37 | 5–10 |
| customer retention software | 500 | 28 | 5–10 |
| customer retention management software | 800 | 31 | 5–10 |
| limited time offer | 2,700 | 8 | 4–6 |
| loyalty card | 1,400 | 9 | 4–6 |
| best loyalty software | 300 | 3 | 1–2 |
| white label loyalty | vol n/a | 2 | 1 |
| loyalty program management | 500 | 2 | 1 |
| referral program software | 800 | 20 | 5–10 |
| b2b loyalty platform | vol n/a | converting | Monitor |
| loyalty platform for retail | 350 | not ranking | 5–10 |
| plataforma de fidelización | — | 1 | Hold |

---

## 12-Week Sprint Plan

### Weeks 1–2 (June 16–30): Triage
- Diagnose traffic drop — identify the 18 pages that fell from Top 10
- Fix noindex page, submit IndexNow
- Audit homepage meta title/description for commercial keywords

### Weeks 3–6 (July 1–31): Quick Wins
- Homepage H2/H3 optimization for commercial keywords + Schema markup
- Expand /insider/time-limited-offer (2,700 vol, pos 8)
- Expand /product/customer-retention-software (800 vol, KD 3–4, pos 28–31)
- Bulk fix: alt text (383 pages), meta descriptions (131 pages), titles (90 pages)
- Add mid-funnel CTAs to top 10 traffic pages
- Brief the "brand loyalty" cornerstone article for writing

### Weeks 7–10 (August 4–31): Content Push
- Publish "brand loyalty" cornerstone article (5,200 vol, KD 43)
- Expand /insider/best-gamification-software for "gamification software" keyword
- Expand /insider/best-loyalty-software-comparison-guide (add competitor comparisons)
- Launch /applications/loyalty-platform-for-retail
- Launch /applications/loyalty-platform-for-finance
- Start Spanish commercial page translations

### Weeks 11–12 (September 1–15): CRO Review
- Review which pages gained/lost traffic from previous 8 weeks
- A/B test homepage hero CTA text (try "Book a Demo" vs "See the Platform")
- Review MQL count — are we at 40/month? Adjust priorities

### Q4 Sprint (October–December)
- Launch /applications/loyalty-platform-for-restaurants, /healthcare
- Launch AI/GEO optimization (structured data, factual pages, G2 reviews)
- Launch /vs/antavo, /vs/loyaltylion competitor comparison pages
- Link building outreach campaign
- Publish 2026 Loyalty Program Benchmarks data report
- Review and iterate monthly

---

## Expected Outcome

| Metric | Baseline (May 2026) | Q3 Target (Sep) | Q4 Target (Dec) |
|--------|--------------------|-----------------|-----------------| 
| Organic MQLs/month | 31 | 40 | 62 |
| Organic clicks/month (GSC) | 5,054 | 7,500 | 10,000+ |
| Homepage commercial keyword rankings | pos 3–5 avg | pos 1–3 avg | pos 1–2 avg |
| Keywords in top 3 | 619 | 750+ | 900+ |
| AI/GEO MQL attribution | 19% | 22% | 28% |

The 2× MQL target is achievable by combining three levers:
1. **Recover lost rankings** (March→May drop = ~2,000 clicks/month lost)
2. **Improve conversion rate** on existing traffic (0.47% → 0.70% by optimizing high-traffic pages with commercial CTAs)
3. **Grow commercial keyword rankings** (homepage, product pages, comparison pages)

Lever 2 alone — if the top 5 traffic pages each yield 1 additional MQL/month via better CTAs — adds 5 MQLs immediately with zero new content.
