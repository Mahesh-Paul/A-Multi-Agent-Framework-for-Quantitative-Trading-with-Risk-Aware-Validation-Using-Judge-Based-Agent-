import yfinance as yf
import pandas as pd
import os

def fetch_fundamentals(ticker):
    print(f"Fetching fundamentals for {ticker}...")
    stock = yf.Ticker(ticker)
    info = stock.info

    data = {
        "ticker": ticker,
        "current_price": info.get("currentPrice", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
        "pb_ratio": info.get("priceToBook", "N/A"),
        "debt_to_equity": info.get("debtToEquity", "N/A"),
        "current_ratio": info.get("currentRatio", "N/A"),
        "revenue_growth": info.get("revenueGrowth", "N/A"),
        "net_income": info.get("netIncomeToCommon", "N/A"),
        "free_cash_flow": info.get("freeCashflow", "N/A"),
        "total_assets": info.get("totalAssets", "N/A"),
        "total_debt": info.get("totalDebt", "N/A"),
        "return_on_equity": info.get("returnOnEquity", "N/A"),
        "profit_margins": info.get("profitMargins", "N/A"),
    }

    print(f"Done {ticker} — P/E: {data['pe_ratio']}, P/B: {data['pb_ratio']}")
    return data

if __name__ == "__main__":
    TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
    results = []

    for ticker in TICKERS:
        data = fetch_fundamentals(ticker)
        results.append(data)

    df = pd.DataFrame(results)
    os.makedirs("data/storage", exist_ok=True)
    df.to_csv("data/storage/fundamentals.csv", index=False)
    print("\nAll fundamentals saved.")