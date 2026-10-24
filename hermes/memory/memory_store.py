import chromadb
import pandas as pd
import os

client = chromadb.PersistentClient(path="memory/chroma_db")

market_memory = client.get_or_create_collection("market_memory")
strategy_memory = client.get_or_create_collection("strategy_memory")
report_memory = client.get_or_create_collection("report_memory")

def store_news_in_memory():
    TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
    
    for ticker in TICKERS:
        path = f"data/storage/{ticker}_news.csv"
        df = pd.read_csv(path)
        df = df.dropna(subset=["title"])

        for i, row in df.iterrows():
            doc = f"{row['title']}. {row.get('description', '')}"
            market_memory.add(
                documents=[doc],
                ids=[f"{ticker}_{i}"],
                metadatas=[{"ticker": ticker, "published_at": str(row["published_at"])}]
            )
        print(f"Stored {ticker} news in memory — {len(df)} entries")

if __name__ == "__main__":
    store_news_in_memory()