import os
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

prompt_template = PromptTemplate(
    input_variables=["ticker", "news_analysis", "total_return", "sharpe_ratio", "max_drawdown"],
    template="""
You are a professional simulated trading analyst.

Analyze the following data for {ticker} and generate a trading signal.

News Sentiment Analysis:
{news_analysis}

Backtest Performance:
- Total Return: {total_return}
- Sharpe Ratio: {sharpe_ratio}
- Max Drawdown: {max_drawdown}

Based on this data provide:
1. Signal: BUY, SELL, or HOLD
2. Confidence: 0-100
3. Reason: one sentence

Respond in this exact format:
Signal: <BUY/SELL/HOLD>
Confidence: <0-100>
Reason: <one sentence>
"""
)

def generate_signal(ticker, news_analysis, backtest):
    prompt = prompt_template.format(
        ticker=ticker,
        news_analysis=news_analysis,
        total_return=f"{backtest['total_return']:.2%}",
        sharpe_ratio=f"{backtest['sharpe_ratio']:.2f}",
        max_drawdown=f"{backtest['max_drawdown']:.2%}"
    )

    response = llm.invoke(prompt)

    print(f"\n--- Simulated Trading Analyst: {ticker} ---")
    print(response.content)

    return {
        "ticker": ticker,
        "signal": response.content
    }

if __name__ == "__main__":
    # Load news analysis
    news_df = pd.read_csv("data/storage/news_analysis.csv")

    # Load backtest results
    backtest_df = pd.read_csv("data/storage/backtest_results.csv")

    signals = []

    for _, row in backtest_df.iterrows():
        ticker = row["ticker"]

        # Get news analysis for this ticker
        news_row = news_df[news_df["ticker"] == ticker]
        if news_row.empty:
            continue

        news_analysis = news_row.iloc[0]["analysis"]

        backtest = {
            "total_return": row["total_return"],
            "sharpe_ratio": row["sharpe_ratio"],
            "max_drawdown": row["max_drawdown"]
        }

        signal = generate_signal(ticker, news_analysis, backtest)
        signals.append(signal)

    df = pd.DataFrame(signals)
    df.to_csv("data/storage/trading_signals.csv", index=False)
    print("\nAll trading signals saved.")