# agents/news_agent.py
"""
AGENT 1 — News_Agent
Responsibility : Fetch raw US financial news articles.

Primary source : NewsAPI  (requires NEWSAPI_KEY in .env)
Fallback       : RSS feeds from Reuters, CNBC, Yahoo Finance
Output         : data/news_raw.json   →  list of {title, url, content, timestamp}
"""

import json
import os
import time
from datetime import datetime

import requests
import feedparser

from core.config import (
    NEWSAPI_KEY,
    NEWSAPI_COUNTRY,
    NEWSAPI_LANGUAGE,
    NEWSAPI_CATEGORY,
    NEWSAPI_PAGE_SIZE,
    RAW_NEWS_FILE,
)

# ─── US-finance keyword filter ──────────────────────────────────────────
FINANCE_KEYWORDS = [
    "stock", "market", "share", "price", "nasdaq", "s&p", "dow",
    "equity", "trade", "trading", "invest", "investor", "fed",
    "gdp", "inflation", "revenue", "profit", "loss", "quarter", "earnings",
    "ipo", "bond", "forex", "crude", "oil", "gold", "wall street",
    "bank", "company", "corporate", "economy", "economic", "fiscal",
    "export", "import", "budget", "tax", "growth", "recession",
    "bull", "bear", "dividend", "index", "rally", "crash", "correction",
    "sec", "ceo", "cfo", "merger", "acquisition", "startup", "vc",
    "interest rate", "treasury", "fed rate", "monetary", "stimulus",
    "apple", "microsoft", "google", "amazon", "nvidia", "tesla",
    "jpmorgan", "goldman", "morgan stanley", "blackrock",
]


def _is_financial(title: str, content: str) -> bool:
    text = (title + " " + content).lower()
    return any(kw in text for kw in FINANCE_KEYWORDS)


class NewsAgent:
    # ── RSS feeds used when NewsAPI key is missing ────────────────────
    RSS_FEEDS = [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.cnbc.com/feeds/tv/rss/top_stories/index.xml",
        "https://finance.yahoo.com/rss/",
        "https://www.marketwatch.com/investing/feeds/top48/rss.xml",
    ]

    def __init__(self):
        os.makedirs("data", exist_ok=True)

    # ── Primary: NewsAPI ──────────────────────────────────────────────
    def _fetch_newsapi(self, limit: int = 30) -> list:
        if not NEWSAPI_KEY:
            print("  ⚠️  NEWSAPI_KEY not set — skipping NewsAPI.")
            return []

        print("  📡 Calling NewsAPI …")
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey":   NEWSAPI_KEY,
            "country": NEWSAPI_COUNTRY,
            "language":NEWSAPI_LANGUAGE,
            "category":NEWSAPI_CATEGORY,
            "pageSize": limit,
        }

        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"  ⚠️  NewsAPI request failed: {e}")
            return []

        if data.get("status") != "ok":
            print(f"  ⚠️  NewsAPI error: {data.get('message', 'unknown')}")
            return []

        articles = []
        for item in data.get("articles", []):
            title   = (item.get("title") or "").strip()
            content = (item.get("content") or item.get("description") or "").strip()
            url_art = (item.get("url") or "").strip()

            if not title or not url_art:
                continue
            if not _is_financial(title, content):
                continue

            articles.append({
                "title":     title,
                "url":       url_art,
                "timestamp": str(datetime.now()),
                "content":   content,
            })
            print(f"    ✓ [{len(articles)}] {title[:90]}")

        print(f"  ✅ NewsAPI returned {len(articles)} financial articles.")
        return articles

    # ── Fallback: RSS ─────────────────────────────────────────────────
    def _fetch_rss(self, limit: int = 30) -> list:
        print("  📡 Fetching via RSS feeds …")
        articles   = []
        seen       = set()

        for feed_url in self.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    title   = (entry.get("title") or "").strip()
                    url_art = (entry.get("link") or "").strip()
                    content = (entry.get("summary") or "").strip()

                    if title.lower() in seen:
                        continue
                    seen.add(title.lower())

                    if not _is_financial(title, content):
                        continue

                    articles.append({
                        "title":     title,
                        "url":       url_art,
                        "timestamp": str(datetime.now()),
                        "content":   content,
                    })
                    print(f"    ✓ [{len(articles)}] {title[:90]}")

                    if len(articles) >= limit:
                        break
            except Exception as e:
                print(f"    ⚠️  RSS parse error ({feed_url}): {e}")

            if len(articles) >= limit:
                break

        print(f"  ✅ RSS collected {len(articles)} financial articles.")
        return articles

    # ── Main ──────────────────────────────────────────────────────────
    def run(self) -> list:
        print("\n🔍 [News_Agent] Starting …")

        articles = self._fetch_newsapi(limit=NEWSAPI_PAGE_SIZE)

        if not articles:
            print("  🔄 Falling back to RSS …")
            articles = self._fetch_rss(limit=30)

        with open(RAW_NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4, ensure_ascii=False)

        print(f"  🎉 Saved {len(articles)} articles → {RAW_NEWS_FILE}\n")
        return articles


if __name__ == "__main__":
    NewsAgent().run()
