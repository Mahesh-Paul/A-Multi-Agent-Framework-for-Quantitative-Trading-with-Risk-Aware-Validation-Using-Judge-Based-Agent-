import finnhub
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))

def fetch_realtime_news():
    os.makedirs("data/storage", exist_ok=True)

    today = datetime.today().strftime("%Y-%m-%d")
    week_ago = (datetime.today() - timedelta(days=7)).strftime("%Y-%m-%d")

    for ticker in TICKERS:
        print(f"Fetching real-time news for {ticker}...")
        news = client.company_news(ticker, _from=week_ago, to=today)

        data = []
        for article in news[:50]:
            data.append({
                "ticker": ticker,
                "title": article.get("headline", ""),
                "description": article.get("summary", ""),
                "published_at": article.get("datetime", ""),
                "source": article.get("source", ""),
                "url": article.get("url", "")
            })

        df = pd.DataFrame(data)
        df.to_csv(f"data/storage/{ticker}_news.csv", index=False)
        print(f"Saved {ticker} — {len(df)} articles")

if __name__ == "__main__":
    fetch_realtime_news()