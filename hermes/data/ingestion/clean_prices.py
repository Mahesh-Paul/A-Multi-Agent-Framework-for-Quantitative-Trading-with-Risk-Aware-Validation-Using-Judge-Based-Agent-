import pandas as pd
import os

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]

def clean_prices():
    for ticker in TICKERS:
        path = f"data/storage/{ticker}_prices.csv"
        df = pd.read_csv(path)

        # Drop empty rows
        df.dropna(inplace=True)

        # Forward fill any missing values
        df.ffill(inplace=True)

        # Save cleaned version
        df.to_csv(f"data/storage/{ticker}_prices_clean.csv", index=False)
        print(f"Cleaned {ticker} — {len(df)} rows")

if __name__ == "__main__":
    clean_prices()