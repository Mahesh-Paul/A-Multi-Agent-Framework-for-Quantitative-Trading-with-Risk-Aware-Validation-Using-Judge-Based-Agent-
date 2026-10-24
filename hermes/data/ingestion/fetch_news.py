from newsapi import NewsApiClient
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_news():
    os.makedirs("data/storage", exist_ok=True)
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)

    for ticker in TICKERS:
        print(f"Fetching news for {ticker}...")
        articles = newsapi.get_everything(
            q=ticker,
            language="en",
            sort_by="publishedAt",
            page_size=100
        )

        data = []
        for article in articles["articles"]:
            data.append({
                "ticker": ticker,
                "title": article["title"],
                "description": article["description"],
                "published_at": article["publishedAt"],
                "source": article["source"]["name"],
                "url": article["url"]
            })

        df = pd.DataFrame(data)
        df.to_csv(f"data/storage/{ticker}_news.csv", index=False)
        print(f"Saved {ticker} news — {len(df)} articles")

if __name__ == "__main__":
    fetch_news()