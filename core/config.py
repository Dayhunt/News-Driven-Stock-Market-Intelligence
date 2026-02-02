# core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# API KEYS  (read from .env)
# ─────────────────────────────────────────────
NEWSAPI_KEY            = os.getenv("NEWSAPI_KEY", "")
ALPHA_VANTAGE_API_KEY  = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# ─────────────────────────────────────────────
# NEWS SCRAPING SETTINGS
# ─────────────────────────────────────────────
# NewsAPI query – only US, English, business category
NEWSAPI_COUNTRY  = "us"
NEWSAPI_LANGUAGE = "en"
NEWSAPI_CATEGORY = "business"
NEWSAPI_PAGE_SIZE = 30   # max articles per fetch

# ─────────────────────────────────────────────
# US MARKET – TOP 30 SYMBOLS (plain NYSE/NASDAQ tickers)
# ─────────────────────────────────────────────
US_MARKET_SYMBOLS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM",   "V",    "UNH",
    "XOM",  "WMT",  "JNJ",   "BAC",  "HD",
    "PG",   "CVX",  "LLY",   "MRK",  "ABBV",
    "COST", "AVGO", "PEP",   "KO",   "ORCL",
    "TMO",  "ACN",  "CRM",   "NFLX", "AMD",
]

# ─────────────────────────────────────────────
# COMPANY NAME  →  TICKER  (used by NLP_Agent to tag articles)
# Keys are all lower-case; matching is case-insensitive substring.
# ─────────────────────────────────────────────
COMPANY_TICKER_MAP = {
    # mega-cap tech
    "apple":            "AAPL",
    "microsoft":        "MSFT",
    "google":           "GOOGL",
    "alphabet":         "GOOGL",
    "amazon":           "AMZN",
    "nvidia":           "NVDA",
    "meta":             "META",
    "facebook":         "META",
    "tesla":            "TSLA",
    # financials
    "jpmorgan":         "JPM",
    "jp morgan":        "JPM",
    "visa":             "V",
    "bank of america":  "BAC",
    "bofa":             "BAC",
    # healthcare / consumer
    "unitedhealthgroup":"UNH",
    "united health":    "UNH",
    "johnson & johnson":"JNJ",
    "j&j":              "JNJ",
    "procter & gamble": "PG",
    "p&g":              "PG",
    "eli lilly":        "LLY",
    "merck":            "MRK",
    "abbvie":           "ABBV",
    # energy / retail / other
    "exxon":            "XOM",
    "exxonmobil":       "XOM",
    "walmart":          "WMT",
    "home depot":       "HD",
    "chevron":          "CVX",
    "costco":           "COST",
    "broadcom":         "AVGO",
    "pepsico":          "PEP",
    "pepsi":            "PEP",
    "coca-cola":        "KO",
    "coca cola":        "KO",
    "oracle":           "ORCL",
    "thermo fisher":    "TMO",
    "accenture":        "ACN",
    "salesforce":       "CRM",
    "netflix":          "NFLX",
    "amd":              "AMD",
    "advanced micro":   "AMD",
    # indices (informational tags only – no price data)
    "s&p 500":          "SPY",
    "s&p500":           "SPY",
    "dow jones":        "DJI",
    "dow":              "DJI",
    "nasdaq":           "QQQ",
    "wall street":      "SPY",
}

# ─────────────────────────────────────────────
# FILE PATHS  (relative to project root)
# ─────────────────────────────────────────────
RAW_NEWS_FILE       = "data/news_raw.json"
PROCESSED_NEWS_FILE = "data/news_processed.json"
MARKET_FILE         = "data/market_data.json"
ANALYSIS_FILE       = "data/analysis_output.json"
TREND_HISTORY_FILE  = "data/stock_trend_history.csv"

# ─────────────────────────────────────────────
# SENTIMENT LABEL  →  NUMERIC SCORE  [-1 … 1]
# The BERT model used by NLP_Agent outputs "1 star" … "5 stars"
# ─────────────────────────────────────────────
SENTIMENT_SCORE_MAP = {
    "1 star":  -1.0,
    "2 stars": -0.5,
    "3 stars":  0.0,
    "4 stars":  0.5,
    "5 stars":  1.0,
    "neutral":  0.0,
    "positive": 0.5,
    "negative":-0.5,
}

# ─────────────────────────────────────────────
# IMPACT SCORING WEIGHTS  (must sum to 1.0)
# ─────────────────────────────────────────────
IMPACT_WEIGHTS = {
    "sentiment": 0.45,   # biggest lever: how positive/negative is the news?
    "movement":  0.35,   # intraday price change confirms or contradicts
    "volume":    0.20,   # high volume = conviction
}
