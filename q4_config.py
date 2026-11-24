"""Shared Q4 2026 scorecard configuration: tracked keywords, Chatbeat prompts and sheet layout."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(ROOT, "token.json")
HISTORY_FILE = os.path.join(ROOT, "q4_history.json")
SITE = "sc-domain:openloyalty.io"
GSC_ENDPOINT = "https://www.googleapis.com/webmasters/v3"
OL_KEYWORDS = {"open loyalty", "openloyalty"}

Q4_FIRST_MONDAY = "2026-09-21"  # W39
BASELINE_WEEK = ("2026-09-14", "2026-09-20")  # W38, the "Starting position" column

C1_KEYWORDS = [
    "loyalty platform",
    "loyalty program software",
    "customer loyalty software",
    "loyalty software",
    "customer loyalty program software",
    "customer loyalty platform",
    "loyalty system",
    "loyalty card system",
    "voucher management system",
    "coupon management software",
    "loyalty program saas",
    "loyalty rewards management system",
    "best customer loyalty software",
    "loyalty program api",
    "loyalty management software",
]

C2_KEYWORDS = [
    "loyalty points",
    "loyalty program cost",
    "loyalty program app",
    "white label loyalty",
    "b2b loyalty programs",
    "b2b loyalty program software",
    "ecommerce loyalty program",
    "retail loyalty",
    "omnichannel loyalty program",
    "loyalty gamification",
]

C3_KEYWORDS = [
    "yotpo alternatives",
    "smile.io alternatives",
    "voucherify competitors",
    "loyaltylion alternatives",
    "talon.one alternatives",
    "antavo alternatives",
]

LLM_PROMPTS = [
    "Best customer loyalty software",
    "Best loyalty program software for enterprise",
    "Best white label loyalty platform",
    "Best B2B loyalty program software",
    "Best API-first loyalty platform",
    "Best loyalty platform",
    "Best loyalty program software",
    "Best customer loyalty program software",
    "Best loyalty system",
    "Best loyalty software",
    "Best customer loyalty platform",
    "Best loyalty card system",
    "Best coupon management software",
    "Best voucher software",
    "Best loyalty program saas",
]

GPT2_PROMPTS = [
    "Alternatives to Salesforce Loyalty Management",
    "Antavo alternatives",
    "Headless loyalty platform",
    "How much does loyalty program software cost",
    "Is it cheaper to build a loyalty program in-house or buy one",
    "Loyalty program for restaurants",
    "Loyalty program pricing models explained",
    "Loyalty program software for ecommerce",
    "LoyaltyLion alternatives",
    "Omnichannel loyalty platform",
    "Talon.One alternatives",
    "Voucherify alternatives",
    "What are the best alternatives to Smile.io",
    "Yotpo alternatives",
]

# (comment key, sheet label, keywords)
GSC_SECTIONS = [
    ("c1", "Cluster 1 (Google) — High Intent", C1_KEYWORDS),
    ("c2", "Cluster 2 (Google) — MQL generators", C2_KEYWORDS),
    ("c3", "Cluster 3 (Google) — Competitors", C3_KEYWORDS),
]

# (comment key, Chatbeat llm value, export: "q3c1" or "q4", prompts, sheet label)
CB_SECTIONS = [
    ("GPT", "GPT", "q3c1", LLM_PROMPTS, "ChatGPT (C1 prompts)"),
    ("CLAUDE", "CLAUDE", "q3c1", LLM_PROMPTS, "Claude (C1 prompts)"),
    ("AI_OVERVIEW", "AI_OVERVIEW", "q3c1", LLM_PROMPTS, "AI Overview (C1 prompts)"),
    ("PERPLEXITY", "PERPLEXITY", "q3c1", LLM_PROMPTS, "Perplexity (C1 prompts)"),
    ("GPT2", "GPT", "q4", GPT2_PROMPTS, "ChatGPT 2nd cluster"),
]
