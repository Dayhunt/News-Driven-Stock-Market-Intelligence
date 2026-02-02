# agents/analysis_agent.py
"""
AGENT 4 — Analysis_Agent
Responsibility : Join news + market data, compute per-stock impact scores,
                 classify trends, and produce the final ranked output.

Input  : data/news_processed.json   (sentiment, companies, summary …)
         data/market_data.json       (ohlcv per ticker)
Output : data/analysis_output.json  →  top bullish, top bearish, full list
"""

import json
import os
from datetime import datetime

import pandas as pd

from core.config import (
    SENTIMENT_SCORE_MAP,
    IMPACT_WEIGHTS,
    PROCESSED_NEWS_FILE,
    MARKET_FILE,
    ANALYSIS_FILE,
)


class AnalysisAgent:
    def __init__(self):
        os.makedirs("data", exist_ok=True)

    # ── Loaders ───────────────────────────────────────────────────────
    @staticmethod
    def _load(path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠️  Could not load {path}: {e}")
            return [] if path == PROCESSED_NEWS_FILE else {}

    # ── Sentiment label → float ───────────────────────────────────────
    @staticmethod
    def _sentiment_num(label: str) -> float:
        return SENTIMENT_SCORE_MAP.get(label.strip().lower(), 0.0)

    # ── Intraday movement score  (close - open) / open ───────────────
    @staticmethod
    def _movement_score(entry: dict) -> float:
        o = entry.get("open", 0)
        c = entry.get("close", 0)
        return round((c - o) / o, 4) if o != 0 else 0.0

    # ── Volume normalisation ──────────────────────────────────────────
    @staticmethod
    def _volume_score(volume: int) -> float:
        """
        Map raw volume to a [-1, 1] scale.
        > 50 M  →  1.0   (very high conviction)
        > 10 M  →  0.5
        > 1 M   →  0.2
        else    →  0.0
        """
        if volume > 50_000_000:
            return 1.0
        if volume > 10_000_000:
            return 0.5
        if volume >  1_000_000:
            return 0.2
        return 0.0

    # ── Weighted impact formula ───────────────────────────────────────
    @staticmethod
    def _impact_score(sentiment_num: float,
                      movement: float,
                      volume_score: float) -> float:
        """
        impact = w_sentiment * sentiment
               + w_movement  * movement
               + w_volume    * volume_score * sign(sentiment)

        The volume term is multiplied by sign(sentiment) so that high
        volume amplifies the direction the news points, not just magnitude.
        """
        sign = 1 if sentiment_num >= 0 else -1
        raw = (IMPACT_WEIGHTS["sentiment"] * sentiment_num
             + IMPACT_WEIGHTS["movement"]  * movement
             + IMPACT_WEIGHTS["volume"]    * volume_score * sign)
        return round(raw, 4)

    # ── Trend classification ──────────────────────────────────────────
    @staticmethod
    def _trend(score: float) -> str:
        if   score >  0.25: return "Strong Bullish"
        elif score >  0.05: return "Moderate Bullish"
        elif score >= -0.05: return "Neutral"
        elif score >= -0.25: return "Moderate Bearish"
        else:                return "Strong Bearish"

    # ── Main ──────────────────────────────────────────────────────────
    def run(self) -> dict:
        print("\n📊 [Analysis_Agent] Starting …")

        news_list   = self._load(PROCESSED_NEWS_FILE)   # list
        market_data = self._load(MARKET_FILE)           # dict {ticker: …}

        print(f"  News articles : {len(news_list)}")
        print(f"  Market tickers: {len(market_data)}")

        rows = []

        for article in news_list:
            title      = article.get("title", "")
            summary    = article.get("summary", "")
            sent_label = article.get("sentiment", "neutral")
            sent_num   = self._sentiment_num(sent_label)
            companies  = article.get("companies", [])
            keywords   = article.get("keywords", [])
            timestamp  = article.get("timestamp", str(datetime.now()))

            # For each company the article mentions, look up market data
            for ticker in companies:
                if ticker not in market_data:
                    continue                  # index pseudo-ticker or no data

                mkt = market_data[ticker]
                movement  = self._movement_score(mkt)
                vol_score = self._volume_score(mkt.get("volume", 0))
                impact    = self._impact_score(sent_num, movement, vol_score)

                rows.append({
                    "symbol":         ticker,
                    "sentiment_label": sent_label,
                    "sentiment_num":  sent_num,
                    "movement_score": movement,
                    "volume":         mkt.get("volume", 0),
                    "volume_score":   vol_score,
                    "impact_score":   impact,
                    "trend":          self._trend(impact),
                    "open":           mkt.get("open",  0),
                    "close":          mkt.get("close", 0),
                    "high":           mkt.get("high",  0),
                    "low":            mkt.get("low",   0),
                    "news_headline":  title,
                    "matched_news":   title,
                    "summary":        summary,
                    "keywords":       keywords,
                    "timestamp":      timestamp,
                })

        # ── Aggregate: if a ticker appears in multiple articles,
        #     average the impact scores and keep the strongest headline ──
        if rows:
            df = pd.DataFrame(rows)

            # per-ticker aggregation
            agg = (
                df.groupby("symbol")
                .apply(lambda g: pd.Series({
                    "symbol":         g.name,
                    "avg_impact":     round(g["impact_score"].mean(), 4),
                    "max_impact":     round(g["impact_score"].max(), 4),
                    "min_impact":     round(g["impact_score"].min(), 4),
                    "article_count":  len(g),
                    "trend":          self._trend(g["impact_score"].mean()),
                    "open":           g["open"].iloc[0],
                    "close":          g["close"].iloc[0],
                    "volume":         int(g["volume"].iloc[0]),
                    "top_headline":   g.loc[g["impact_score"].idxmax(), "news_headline"],
                    "top_summary":    g.loc[g["impact_score"].idxmax(), "summary"],
                    "sentiment_label":g.loc[g["impact_score"].idxmax(), "sentiment_label"],
                }), include_groups=False)
                .reset_index(drop=True)
            )

            top_bullish = (agg.sort_values("avg_impact", ascending=False)
                           .head(10).to_dict(orient="records"))
            top_bearish = (agg.sort_values("avg_impact", ascending=True)
                           .head(10).to_dict(orient="records"))
            full_list   = df.to_dict(orient="records")
            aggregated  = agg.to_dict(orient="records")
        else:
            top_bullish = []
            top_bearish = []
            full_list   = []
            aggregated  = []

        output = {
            "generated_at":   str(datetime.now()),
            "top_10_bullish": top_bullish,
            "top_10_bearish": top_bearish,
            "aggregated":     aggregated,
            "full_list":      full_list,
        }

        with open(ANALYSIS_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print(f"  ✅ Bullish: {len(top_bullish)} | Bearish: {len(top_bearish)} "
              f"| Total rows: {len(full_list)}")
        print(f"  📦 Saved → {ANALYSIS_FILE}\n")
        return output


if __name__ == "__main__":
    AnalysisAgent().run()
