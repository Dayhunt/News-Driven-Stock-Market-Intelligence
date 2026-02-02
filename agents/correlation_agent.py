# agents/correlation_agent.py

import json
import os
from datetime import datetime


class CorrelationAgent:
    """
    Matches companies mentioned in processed news against live market data
    and scores each match by intraday price movement.
    """

    def __init__(self):
        self.processed_news_file = "data/news_processed.json"
        self.market_data_file   = "data/market_data.json"
        self.output_file        = "data/correlation_output.json"

    # ------------------------------------------------------------------
    def _load(self, path: str) -> list | dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠️  Could not load {path}: {e}")
            return {} if path == self.market_data_file else []

    # ------------------------------------------------------------------
    @staticmethod
    def intraday_movement_score(entry: dict) -> float:
        """
        Simple intraday movement score:
            score = (close - open) / open
        Positive → price went up during the day.
        Negative → price went down.
        """
        open_price  = entry.get("open",  0)
        close_price = entry.get("close", 0)

        if open_price == 0:
            return 0.0

        return round((close_price - open_price) / open_price, 4)

    # ------------------------------------------------------------------
    def run(self):
        news_list   = self._load(self.processed_news_file)   # list of articles
        market_data = self._load(self.market_data_file)      # {symbol: {…}}

        print("\n🔗 CorrelationAgent: running …")
        print(f"   News articles : {len(news_list)}")
        print(f"   Market symbols: {len(market_data)}")

        final_output = []

        for article in news_list:
            title      = article.get("title", "")
            summary    = article.get("summary", "")
            sentiment  = article.get("sentiment", "neutral")
            companies  = article.get("companies", [])  # list of ticker symbols
            keywords   = article.get("keywords", [])
            timestamp  = article.get("timestamp", str(datetime.now()))

            # Match tickers from the article against available market data
            related_stocks = []
            for ticker in companies:
                if ticker in market_data:
                    entry = market_data[ticker]
                    score = self.intraday_movement_score(entry)

                    related_stocks.append({
                        "symbol":         ticker,
                        "movement_score": score,
                        "open":           entry.get("open",   0),
                        "close":          entry.get("close",  0),
                        "high":           entry.get("high",   0),
                        "low":            entry.get("low",    0),
                        "volume":         entry.get("volume", 0),
                    })

            # Sort by absolute movement (most movement first)
            related_stocks.sort(key=lambda x: abs(x["movement_score"]), reverse=True)

            final_output.append({
                "title":                  title,
                "summary":                summary,
                "sentiment":              sentiment,
                "keywords":               keywords,
                "companies_in_news":      companies,
                "timestamp":              timestamp,
                "related_stocks_ranked":  related_stocks
            })

        # Save
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(final_output, f, indent=4, ensure_ascii=False)

        print(f"✅ CorrelationAgent done → {self.output_file}\n")
        return final_output


# -----------------------------------------------------------------------
if __name__ == "__main__":
    CorrelationAgent().run()
