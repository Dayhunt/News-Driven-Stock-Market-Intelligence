# News Driven Stock Market Intelligence

An AI-powered **multi-agent system** that automatically scrapes financial news, processes it using NLP, identifies company mentions, fetches real‑time stock prices, and predicts the impact of news on market movement.

This project helps **analysts, investors, and developers** quickly understand how current news may influence stock prices — **without manual research**.

---

## Features

### 1. Automated News Scraping
- Scrapes live news from **MoneyControl**
- Extracts full article content
- Handles pagination & dynamic pages

### 2. NLP Processing
- Summarization using **BART**
- Sentiment analysis using **BERT**
- Keyword extraction using **KeyBERT**
- Company/entity extraction

### 3. Market Data Analysis
- Symbol lookup using **Finnhub**
- Real‑time stock price via **yfinance**
- Last 8 days’ closing prices
- Predicts sentiment-based market impact:
  - **Positive**
  - **Neutral**
  - **Negative**

### 4. Multi-Agent Pipeline (CrewAI)
Orchestrates:
- **News Agent**
- **NLP Agent**
- **Market Analysis Agent**

### 5. JSON Storage
Outputs stored in:
- data/news_processed.json
- data/market_news_impact.json


---

## Tech Stack

| Component         | Technology |
|------------------|------------|
| Scraping         | Requests, BeautifulSoup, Selenium |
| NLP              | HuggingFace Transformers (BART, BERT), KeyBERT |
| Financial Data   | Finnhub API, yfinance |
| Orchestration    | CrewAI |
| Storage          | JSON files |

---

##  How It Works

### ** 1️ Run News Agent**
Scrapes full article content and saves raw structured news.

### ** 2️ Run NLP Agent**
- Summarizes using BART  
- Extracts sentiment with BERT  
- Extracts keywords with KeyBERT  
- Identifies company mentions  

### ** 3️ Run Analysis Agent**
- Maps companies → stock symbols  
- Fetches real‑time stock prices  
- Gets last 8‑day trend  
- Predicts sentiment-based impact  

---

##  Installation

```
git clone <your-repo-url>
cd your-project
pip install -r requirements.txt
```
## Run the Project
- **python crew_pipeline.py

## Future Enhancements
- Streamlit dashboard for visualization
- Real‑time alert system
- More news sources (MoneyControl, Bloomberg, Reuters)
- Multi‑language news analysis

