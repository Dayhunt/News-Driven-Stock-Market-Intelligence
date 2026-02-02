# agents/nlp_agent.py
"""
AGENT 2 — NLP_Agent
Responsibility : Pre-process raw news with spaCy, summarise with BART,
                 extract keywords with KeyBERT, score sentiment with BERT,
                 and tag which US companies are mentioned.

Input  : data/news_raw.json        (written by News_Agent)
Output : data/news_processed.json  →  list of enriched article dicts
"""

import os
import json
from datetime import datetime

import spacy
import nltk
from transformers import pipeline as hf_pipeline
from keybert import KeyBERT

from core.config import (
    COMPANY_TICKER_MAP,
    RAW_NEWS_FILE,
    PROCESSED_NEWS_FILE,
)

# ─── one-time NLTK data download ────────────────────────────────────────
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)


# ─── Load spaCy model (small English model, fast) ──────────────────────
def _load_spacy():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("  ⏳ Downloading spaCy en_core_web_sm …")
        spacy.cli.download("en_core_web_sm")
        return spacy.load("en_core_web_sm")


# ─── Company extraction helper ─────────────────────────────────────────
def extract_companies(text: str) -> list:
    """
    Scan *text* for every company name in COMPANY_TICKER_MAP.
    Return deduplicated list of ticker symbols.
    """
    lower = text.lower()
    found = {}                                   # ticker → name (dedup)
    for name, ticker in COMPANY_TICKER_MAP.items():
        if name in lower:
            found[ticker] = name
    return list(found.keys())


class NLPAgent:
    def __init__(self):
        print("  ⏳ Loading spaCy …")
        self.nlp = _load_spacy()

        print("  ⏳ Loading BART summariser …")
        self.summariser = hf_pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
        )

        print("  ⏳ Loading BERT sentiment model …")
        self.sentiment_model = hf_pipeline(
            "sentiment-analysis",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
        )

        print("  ⏳ Loading KeyBERT …")
        self.keyword_model = KeyBERT()

        os.makedirs("data", exist_ok=True)
        print("  ✅ NLP_Agent models ready.\n")

    # ── spaCy preprocessing ───────────────────────────────────────────
    def preprocess(self, text: str) -> str:
        """
        spaCy pipeline:
          1. Tokenise
          2. Lemmatise every token
          3. Drop stopwords, punctuation, spaces, numbers
          4. Keep only NOUN, VERB, ADJ, ADV
          5. Return cleaned text (preserves readable words)
        """
        if not text:
            return ""

        doc = self.nlp(text[:5000])          # spaCy has a token limit; be safe

        allowed_pos = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}
        tokens = [
            token.lemma_.strip()
            for token in doc
            if (not token.is_stop
                and not token.is_punct
                and not token.is_space
                and not token.like_num
                and token.pos_ in allowed_pos
                and len(token.lemma_.strip()) > 1)
        ]
        return " ".join(tokens)

    # ── BART summarisation ────────────────────────────────────────────
    def summarise(self, text: str) -> str:
        if not text or len(text) < 60:
            return text or ""
        try:
            result = self.summariser(
                text[:3000],
                max_length=150,
                min_length=30,
                do_sample=False,
            )
            return result[0]["summary_text"]
        except Exception as e:
            print(f"    ⚠️  Summarisation failed: {e}")
            return "Summary unavailable."

    # ── BERT sentiment ────────────────────────────────────────────────
    def sentiment(self, text: str) -> str:
        """Returns raw label e.g. '4 stars'."""
        if not text:
            return "neutral"
        try:
            result = self.sentiment_model(text[:512])[0]
            return result["label"]
        except Exception as e:
            print(f"    ⚠️  Sentiment failed: {e}")
            return "neutral"

    # ── KeyBERT keywords ──────────────────────────────────────────────
    def keywords(self, text: str) -> list:
        if not text:
            return []
        try:
            return [kw[0] for kw in self.keyword_model.extract_keywords(text, top_n=7)]
        except Exception as e:
            print(f"    ⚠️  Keyword extraction failed: {e}")
            return []

    # ── Main processing loop ──────────────────────────────────────────
    def process(self, news_list: list) -> list:
        processed = []

        for item in news_list:
            title     = item.get("title", "")
            content   = item.get("content", "")
            url       = item.get("url", "")
            timestamp = item.get("timestamp", str(datetime.now()))

            print(f"  📝 {title[:80]}")

            # raw combined text for NLP
            raw_text  = f"{title}. {content}" if content else title

            # 1. spaCy clean text (used for keyword extraction)
            cleaned   = self.preprocess(raw_text)

            # 2. BART summary (on the original, not cleaned — readability)
            summary   = self.summarise(content if content else title)

            # 3. BERT sentiment (on original text)
            sent      = self.sentiment(raw_text)

            # 4. KeyBERT on the spaCy-cleaned text (better signal)
            kws       = self.keywords(cleaned if cleaned else raw_text)

            # 5. Company-ticker tagging
            companies = extract_companies(raw_text)

            processed.append({
                "title":     title,
                "url":       url,
                "timestamp": timestamp,
                "cleaned_text": cleaned,
                "summary":   summary,
                "sentiment": sent,
                "keywords":  kws,
                "companies": companies,
            })

        # Save
        with open(PROCESSED_NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=4, ensure_ascii=False)

        print(f"  ✅ Processed {len(processed)} articles → {PROCESSED_NEWS_FILE}\n")
        return processed


if __name__ == "__main__":
    if os.path.exists(RAW_NEWS_FILE):
        with open(RAW_NEWS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        NLPAgent().process(raw)
    else:
        print(f"❌ {RAW_NEWS_FILE} not found — run News_Agent first.")
