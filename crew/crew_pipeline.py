# crew/crew_pipeline.py
"""
Sequential pipeline runner for the 4-agent architecture.

    News_Agent  →  NLP_Agent  →  Market_Agent  →  Analysis_Agent
        ↓              ↓              ↓                ↓
   news_raw.json  news_processed  market_data    analysis_output

WHY no CrewAI here?
    CrewAI's Agent() constructor unconditionally calls create_llm()
    which requires OPENAI_API_KEY — there is no way to pass llm=None
    or skip it.  All four agents here are pure-Python data processors
    with zero LLM calls; a direct sequential runner is the correct,
    reliable, and key-free way to orchestrate them.
"""

import sys
import os
import json
import traceback
from datetime import datetime

# ── project root on path ──────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.news_agent     import NewsAgent
from agents.nlp_agent      import NLPAgent
from agents.market_agent   import MarketAgent
from agents.analysis_agent import AnalysisAgent
from core.config           import RAW_NEWS_FILE


# ═══════════════════════════════════════════════════════════════════════
# PIPELINE STEPS  — each returns True on success, False on failure
# ═══════════════════════════════════════════════════════════════════════

def step_news() -> bool:
    """STEP 1 — Scrape US financial news → data/news_raw.json"""
    try:
        articles = NewsAgent().run()
        print(f"  ✓ News_Agent produced {len(articles)} articles.\n")
        return True
    except Exception as e:
        print(f"\n  ❌ News_Agent failed: {e}")
        traceback.print_exc()
        return False


def step_nlp() -> bool:
    """STEP 2 — spaCy + BART + BERT + KeyBERT → data/news_processed.json"""
    try:
        with open(RAW_NEWS_FILE, "r", encoding="utf-8") as f:
            raw_news = json.load(f)

        if not raw_news:
            print("  ⚠️  news_raw.json is empty — nothing to process.")
            return False

        processed = NLPAgent().process(raw_news)
        print(f"  ✓ NLP_Agent enriched {len(processed)} articles.\n")
        return True
    except Exception as e:
        print(f"\n  ❌ NLP_Agent failed: {e}")
        traceback.print_exc()
        return False


def step_market() -> bool:
    """STEP 3 — Fetch intraday prices → data/market_data.json + trend CSV"""
    try:
        market = MarketAgent().run()
        print(f"  ✓ Market_Agent fetched {len(market)} tickers.\n")
        return True
    except Exception as e:
        print(f"\n  ❌ Market_Agent failed: {e}")
        traceback.print_exc()
        return False


def step_analysis() -> bool:
    """STEP 4 — Join news + market, score, rank → data/analysis_output.json"""
    try:
        output = AnalysisAgent().run()
        bullish = len(output.get("top_10_bullish", []))
        bearish = len(output.get("top_10_bearish", []))
        print(f"  ✓ Analysis_Agent: {bullish} bullish, {bearish} bearish.\n")
        return True
    except Exception as e:
        print(f"\n  ❌ Analysis_Agent failed: {e}")
        traceback.print_exc()
        return False


# ═══════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════

PIPELINE_STEPS = [
    ("News_Agent",     step_news),
    ("NLP_Agent",      step_nlp),
    ("Market_Agent",   step_market),
    ("Analysis_Agent", step_analysis),
]


def run_pipeline():
    print("\n" + "=" * 62)
    print("  🚀  US INTRADAY NEWS-IMPACT PIPELINE")
    print(f"      Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 62 + "\n")

    for idx, (label, fn) in enumerate(PIPELINE_STEPS, start=1):
        print("─" * 62)
        print(f"  [{idx}/{len(PIPELINE_STEPS)}]  {label}")
        print("─" * 62)

        success = fn()
        if not success:
            print(f"\n{'=' * 62}")
            print(f"  ⛔  PIPELINE STOPPED at {label}")
            print(f"{'=' * 62}\n")
            return False

    print("=" * 62)
    print("  ✅  ALL 4 AGENTS COMPLETED SUCCESSFULLY")
    print(f"      Finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 62 + "\n")
    return True


if __name__ == "__main__":
    run_pipeline()
