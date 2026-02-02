# dashboard/app.py
"""
Streamlit dashboard — run from project root:
    streamlit run dashboard/app.py
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ─── helpers ──────────────────────────────────────────────────────────
def load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="US Intraday AI Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for a clean dark financial-terminal feel
st.markdown("""
<style>
    .main { background-color: #0f1923; color: #e2e8f0; }
    .stDataFrame { background: #1a2736 !important; }
    .block-container { padding-top: 1rem; }
    h1 { color: #00d4aa; }
    h2, h3 { color: #c9d6df; }
    .stInfo { background: #1a2e40 !important; border-left: 3px solid #00d4aa !important; }
    .stSuccess { background: #162a1e !important; border-left: 3px solid #00d4aa !important; }
    .stWarning { background: #2e2510 !important; border-left: 3px solid #f59e0b !important; }
    .stError { background: #2e1518 !important; border-left: 3px solid #ef4444 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════════════
st.title("⚡ US Real-Time News-Impact Dashboard")
st.caption("Auto-refreshes every 30 s · powered by News → NLP → Market → Analysis pipeline")

# Auto-refresh
st_autorefresh(interval=30_000, key="refresh")

# ═══════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════
analysis = load_json("data/analysis_output.json")
news     = load_json("data/news_processed.json")
market   = load_json("data/market_data.json")

# news can be a list (normal) or empty dict (file missing)
if isinstance(news, dict):
    news = []

# ═══════════════════════════════════════════════════════════════════════
# ALERT BAR
# ═══════════════════════════════════════════════════════════════════════
def render_alerts(data: dict):
    st.subheader("🔔 Real-Time Alerts")
    full = data.get("full_list", [])
    if not full:
        st.info("No impact data yet — run the pipeline first.")
        return

    df = pd.DataFrame(full)
    strong_bull = df[df["impact_score"] >  0.3]
    strong_bear = df[df["impact_score"] < -0.3]

    if strong_bull.empty and strong_bear.empty:
        st.info("No major signals right now.")
        return

    for _, r in strong_bull.iterrows():
        st.success(
            f"🚀 **{r['symbol']}** — Impact `{r['impact_score']}`  |  "
            f"Trend: {r['trend']}\n"
            f"📰 {r.get('news_headline', '')}"
        )
    for _, r in strong_bear.iterrows():
        st.error(
            f"⚠️  **{r['symbol']}** — Impact `{r['impact_score']}`  |  "
            f"Trend: {r['trend']}\n"
            f"📰 {r.get('news_headline', '')}"
        )


# ═══════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ═══════════════════════════════════════════════════════════════════════
col_news, col_right = st.columns([2, 1])

# ─── LEFT: News feed ──────────────────────────────────────────────────
with col_news:
    st.subheader("📰 Latest US Financial News")
    if not news:
        st.warning("No news data — run the pipeline.")
    else:
        for item in news:
            title     = item.get("title", "")
            summary   = item.get("summary", "")
            sentiment = item.get("sentiment", "—")
            companies = item.get("companies", [])
            keywords  = item.get("keywords", [])

            st.markdown(f"### {title}")
            if summary:
                st.write(summary)

            c1, c2, c3 = st.columns(3)
            c1.write(f"📊 Sentiment: `{sentiment}`")
            if companies:
                c2.write(f"📈 Stocks: {', '.join(companies)}")
            if keywords:
                c3.write(f"🏷️  Keywords: {', '.join(keywords[:4])}")
            st.markdown("---")

# ─── RIGHT: Alerts + top lists ────────────────────────────────────────
with col_right:
    render_alerts(analysis)

    # Top-10 Bullish
    st.subheader("🟢 Top 10 Bullish")
    bullish = analysis.get("top_10_bullish", [])
    if bullish:
        df_b = pd.DataFrame(bullish)
        cols = [c for c in ["symbol","avg_impact","trend","article_count","top_headline"]
                if c in df_b.columns]
        st.dataframe(df_b[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No bullish data yet.")

    # Top-10 Bearish
    st.subheader("🔴 Top 10 Bearish")
    bearish = analysis.get("top_10_bearish", [])
    if bearish:
        df_r = pd.DataFrame(bearish)
        cols = [c for c in ["symbol","avg_impact","trend","article_count","top_headline"]
                if c in df_r.columns]
        st.dataframe(df_r[cols], use_container_width=True, hide_index=True)
    else:
        st.info("No bearish data yet.")

# ═══════════════════════════════════════════════════════════════════════
# LIVE MARKET SNAPSHOT
# ═══════════════════════════════════════════════════════════════════════
st.subheader("📈 Live Market Snapshot")
if market and isinstance(market, dict):
    rows = []
    for sym, e in market.items():
        chg = round(((e.get("close",0) - e.get("open",0)) / e.get("open",1)) * 100, 2) if e.get("open") else 0
        rows.append({
            "Symbol":  sym,
            "Open":    e.get("open",  "—"),
            "High":    e.get("high",  "—"),
            "Low":     e.get("low",   "—"),
            "Close":   e.get("close", "—"),
            "Chg %":   f"{chg:+.2f}%",
            "Volume":  f"{e.get('volume',0):,}",
            "News?":   "✅" if e.get("news_linked") else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No market data yet.")

# ═══════════════════════════════════════════════════════════════════════
# FULL IMPACT TABLE
# ═══════════════════════════════════════════════════════════════════════
st.subheader("📊 Full Impact Table")
full = analysis.get("full_list", [])
if full:
    df_full = pd.DataFrame(full)
    cols = [c for c in ["symbol","impact_score","trend","sentiment_label",
                        "movement_score","volume","news_headline"]
            if c in df_full.columns]
    st.dataframe(
        df_full[cols].sort_values("impact_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Run the pipeline to populate this table.")

# ═══════════════════════════════════════════════════════════════════════
# 8-DAY TREND CHART
# ═══════════════════════════════════════════════════════════════════════
st.subheader("📉 8-Day Stock Trend")
try:
    df_trend = pd.read_csv("data/stock_trend_history.csv")
    if not df_trend.empty:
        fig = px.line(
            df_trend, x="date", y="trend_score", color="symbol",
            title="8-Day Normalised Trend (% change from day 1)",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Trend Score",
            template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Trend CSV is empty.")
except Exception:
    st.info("Trend data not available yet — run the pipeline.")
