import vectorbt as vbt
import pandas as pd

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]

def run_backtest(ticker):
    path = f"data/storage/{ticker}_prices_clean.csv"
    df = pd.read_csv(path)

    df = df[df["Price"] != "Ticker"].reset_index(drop=True)
    df.rename(columns={"Price": "Date"}, inplace=True)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df.dropna(subset=["Close"], inplace=True)
    df.set_index("Date", inplace=True)
    df.sort_index(inplace=True)

    close = df["Close"]

    fast_ma = vbt.MA.run(close, 10)
    slow_ma = vbt.MA.run(close, 50)

    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    portfolio = vbt.Portfolio.from_signals(
        close, entries, exits,
        init_cash=10000,
        freq="1D"
    )

    total_return = portfolio.total_return()
    sharpe = portfolio.sharpe_ratio()
    max_dd = portfolio.max_drawdown()

    print(f"\n--- {ticker} Backtest Results ---")
    print(f"Total Return: {total_return:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd:.2%}")

    return {
        "ticker": ticker,
        "total_return": total_return,
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd
    }

if __name__ == "__main__":
    results = []
    for ticker in TICKERS:
        result = run_backtest(ticker)
        results.append(result)

    df_results = pd.DataFrame(results)
    df_results.to_csv("data/storage/backtest_results.csv", index=False)
    print("\nAll backtest results saved.")