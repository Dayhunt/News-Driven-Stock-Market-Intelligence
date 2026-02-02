# agents/market_agent.py
"""
AGENT 3 — Market_Agent
Responsibility : Fetch live US intraday price data and map it to the
                 companies that appeared in the processed news.

Primary source : Alpha Vantage TIME_SERIES_INTRADAY  (ALPHA_VANTAGE_API_KEY)
Fallback       : yfinance  (no key required)

Input  : data/news_processed.json  (to know WHICH tickers matter most)
Output : data/market_data.json           →  {ticker: {ohlcv + news_linked flag}}
         data/stock_trend_history.csv    →  8-day daily close for trend chart
"""

import os
import json
import time

import requests
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

from core.config import (
    ALPHA_VANTAGE_API_KEY,
    US_MARKET_SYMBOLS,
    PROCESSED_NEWS_FILE,
    MARKET_FILE,
    TREND_HISTORY_FILE,
)

load_dotenv()

AV_BASE = "https://www.alphavantage.co/query"


class MarketAgent:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self._av_blocked = not bool(ALPHA_VANTAGE_API_KEY)

    # ── Collect tickers that news actually mentions ──────────────────
    @staticmethod
    def _tickers_from_news() -> set:
        try:
            with open(PROCESSED_NEWS_FILE, "r", encoding="utf-8") as f:
                articles = json.load(f)
            tickers = set()
            for a in articles:
                tickers.update(a.get("companies", []))
            return tickers
        except Exception:
            return set()

    # ── Alpha Vantage single-ticker fetch ─────────────────────────────
    def _fetch_av(self, symbol: str) -> dict | None:
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol":   symbol,
            "interval": "5min",
            "apikey":   ALPHA_VANTAGE_API_KEY,
        }
        try:
            resp = requests.get(AV_BASE, params=params, timeout=15)
            data = resp.json()
        except Exception as e:
            print(f"    ⚠️  AV request error ({symbol}): {e}")
            return None

        if "Note" in data or "Information" in data:
            print("    ⏳ Alpha Vantage rate-limited → switching to yfinance.")
            self._av_blocked = True
            return None

        key = "Time Series (5min)"
        if key not in data:
            return None

        ts     = data[key]
        latest = sorted(ts.keys())[-1]
        e      = ts[latest]
        return {
            "symbol":    symbol,
            "timestamp": latest,
            "open":      float(e["1. open"]),
            "high":      float(e["2. high"]),
            "low":       float(e["3. low"]),
            "close":     float(e["4. close"]),
            "volume":    int(e["5. volume"]),
        }

    # ── yfinance single-ticker fetch (fallback) ───────────────────────
    @staticmethod
    def _fetch_yf(symbol: str) -> dict | None:
        try:
            hist = yf.Ticker(symbol).history(period="1d", interval="5m")
            if hist.empty:
                return None
            row = hist.iloc[-1]
            return {
                "symbol":    symbol,
                "timestamp": str(hist.index[-1]),
                "open":      round(float(row["Open"]),  2),
                "high":      round(float(row["High"]),  2),
                "low":       round(float(row["Low"]),   2),
                "close":     round(float(row["Close"]), 2),
                "volume":    int(row["Volume"]),
            }
        except Exception as e:
            print(f"    ⚠️  yfinance error ({symbol}): {e}")
            return None

    # ── 8-day trend history (yfinance only, one batch call) ───────────
    @staticmethod
    def _build_trend_csv(symbols: list):
        print("  📊 Building 8-day trend history …")
        rows = []
        for sym in symbols:
            try:
                hist = yf.download(sym, period="8d", interval="1d", progress=False)
                if hist.empty:
                    continue
                if isinstance(hist.columns, pd.MultiIndex):
                    hist.columns = hist.columns.get_level_values(0)
                base_price = float(hist["Close"].iloc[0])
                if base_price == 0:
                    continue
                for idx, row in hist.iterrows():
                    rows.append({
                        "date":        str(idx.date()),
                        "symbol":      sym,
                        "close":       round(float(row["Close"]), 2),
                        "trend_score": round(float(row["Close"]) / base_price - 1, 4),
                    })
            except Exception as e:
                print(f"    ⚠️  Trend error ({sym}): {e}")

        if rows:
            pd.DataFrame(rows).to_csv(TREND_HISTORY_FILE, index=False)
            print(f"  ✅ Trend history → {TREND_HISTORY_FILE}")
        else:
            print("  ⚠️  No trend data collected.")

    # ── Main ──────────────────────────────────────────────────────────
    def run(self, symbols: list | None = None) -> dict:
        print("\n📈 [Market_Agent] Starting …")

        # Priority: tickers mentioned in news first, then fill with top list
        news_tickers = self._tickers_from_news()
        # remove index-only pseudo-tickers that have no real price feed
        index_only   = {"SPY", "DJI", "QQQ"}
        news_tickers -= index_only

        if symbols is None:
            symbols = list(news_tickers) + [
                s for s in US_MARKET_SYMBOLS if s not in news_tickers
            ]
        # deduplicate while keeping news tickers first
        seen, ordered = set(), []
        for s in symbols:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        symbols = ordered

        print(f"  Fetching {len(symbols)} symbols "
              f"({len(news_tickers)} from news + {len(symbols)-len(news_tickers)} top list) …")

        market_data = {}
        for symbol in symbols:
            print(f"    📈 {symbol} …", end=" ", flush=True)

            entry = None
            if not self._av_blocked:
                entry = self._fetch_av(symbol)
                if entry:
                    print("(AV ✓)")
                time.sleep(12)      # Alpha Vantage free-tier: 5 req/min

            if entry is None:
                entry = self._fetch_yf(symbol)
                if entry:
                    print("(yf ✓)")
                else:
                    print("(no data)")

            if entry:
                entry["news_linked"] = symbol in news_tickers
                market_data[symbol]  = entry

        # Save snapshot
        with open(MARKET_FILE, "w", encoding="utf-8") as f:
            json.dump(market_data, f, indent=4)
        print(f"  ✅ Market snapshot → {MARKET_FILE}")

        # Build trend CSV for dashboard chart
        self._build_trend_csv(list(market_data.keys())[:15])  # cap at 15 for speed
        print()
        return market_data


if __name__ == "__main__":
    MarketAgent().run()
