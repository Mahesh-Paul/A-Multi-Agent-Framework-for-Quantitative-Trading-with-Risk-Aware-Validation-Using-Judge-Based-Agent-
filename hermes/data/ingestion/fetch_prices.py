import yfinance as yf
import pandas as pd
import os

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]

def fetch_prices():
    os.makedirs("data/storage", exist_ok=True)
    
    for ticker in TICKERS:
        print(f"Fetching {ticker}...")
        df = yf.download(ticker, period="2y", interval="1d")
        df.to_csv(f"data/storage/{ticker}_prices.csv")
        print(f"Saved {ticker} — {len(df)} rows")

if __name__ == "__main__":
    fetch_prices()