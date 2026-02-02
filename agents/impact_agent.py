# agents/impact_agent.py

import json
import os

import pandas as pd

from core.config import SENTIMENT_SCORE_MAP


class ImpactAgent:
    """
    Reads correlation output, computes a numeric impact score per stock,
    classifies trend strength, and produces the final ranked lists that
    the dashboard consumes.
    """

    def __init__(self):
        self.correlation_file = "data/correlation_output.json"
        self.output_file      = "data/impact_output.json"

    # ------------------------------------------------------------------
    def _load_correlation(self) -> list:
        try:
            with open(self.correlation_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"  ⚠️  Could not load {self.correlation_file}: {e}")
            return []

    # ------------------------------------------------------------------
    @staticmethod
    def sentiment_to_number(label: str) -> float:
        """
        Convert the text label produced by the sentiment model
        (e.g. '4 stars', 'neutral') into a float in [-1, 1].
        """
        return SENTIMENT_SCORE_MAP.get(label.strip().lower(), 0.0)

    # ------------------------------------------------------------------
    @staticmethod
    def compute_impact_score(sentiment_num: float, movement_score: float) -> float:
        """
        Weighted impact:
            sentiment  → 60 %
            movement   → 40 %
        Both inputs should already be numeric.
        """
        return round((sentiment_num * 0.6) + (movement_score * 0.4), 4)

    # ------------------------------------------------------------------
    @staticmethod
    def trend_strength(score: float) -> str:
        if score > 0.25:
            return "Strong Bullish"
        elif 0.05 < score <= 0.25:
            return "Moderate Bullish"
        elif -0.05 <= score <= 0.05:
            return "Neutral"
        elif -0.25 <= score < -0.05:
            return "Moderate Bearish"
        else:
            return "Strong Bearish"

    # ------------------------------------------------------------------
    def run(self):
        correlation_data = self._load_correlation()

        print("\n📊 ImpactAgent: computing impact scores …")

        rows = []

        for news_item in correlation_data:
            sentiment_label = news_item.get("sentiment", "neutral")
            sentiment_num   = self.sentiment_to_number(sentiment_label)
            title           = news_item.get("title", "")
            summary         = news_item.get("summary", "")

            for stock in news_item.get("related_stocks_ranked", []):
                movement = stock.get("movement_score", 0.0)
                impact   = self.compute_impact_score(sentiment_num, movement)

                rows.append({
                    "symbol":         stock["symbol"],
                    "company_name":   stock["symbol"],   # ticker is the best we have
                    "sentiment":      sentiment_label,
                    "sentiment_num":  sentiment_num,
                    "movement_score": movement,
                    "impact_score":   impact,
                    "trend":          self.trend_strength(impact),
                    "news_headline":  title,
                    "matched_news":   title,            # dashboard alerts use this key
                    "summary":        summary,
                    "open":           stock.get("open",   0),
                    "close":          stock.get("close",  0),
                    "volume":         stock.get("volume", 0),
                })

        # Build output even if rows is empty (dashboard handles that gracefully)
        if rows:
            df = pd.DataFrame(rows)
            top_pos  = df.sort_values("impact_score", ascending=False).head(10)
            top_neg  = df.sort_values("impact_score", ascending=True).head(10)
            full     = df.to_dict(orient="records")
        else:
            top_pos  = pd.DataFrame()
            top_neg  = pd.DataFrame()
            full     = []

        output = {
            "top_10_positive_news_driven_stocks": top_pos.to_dict(orient="records") if not top_pos.empty else [],
            "top_10_negative_news_driven_stocks": top_neg.to_dict(orient="records") if not top_neg.empty else [],
            "full_list": full
        }

        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print(f"✅ ImpactAgent done → {self.output_file}")
        print(f"   Positive: {len(output['top_10_positive_news_driven_stocks'])} | "
              f"Negative: {len(output['top_10_negative_news_driven_stocks'])} | "
              f"Total: {len(full)}\n")
        return output


# -----------------------------------------------------------------------
if __name__ == "__main__":
    ImpactAgent().run()
