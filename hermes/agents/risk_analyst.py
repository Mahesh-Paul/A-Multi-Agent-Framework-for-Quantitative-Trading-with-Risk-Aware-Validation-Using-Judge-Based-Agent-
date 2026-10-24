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
    input_variables=["ticker", "signal", "confidence", "total_return", "sharpe_ratio", "max_drawdown"],
    template="""
You are a professional risk control analyst.

Evaluate the following trading signal for {ticker} and assess its risk.

Trading Signal: {signal}
Confidence: {confidence}

Backtest Performance:
- Total Return: {total_return}
- Sharpe Ratio: {sharpe_ratio}
- Max Drawdown: {max_drawdown}

Risk Rules:
- REJECT if Max Drawdown is worse than -30%
- REJECT if Sharpe Ratio is below 0
- REDUCE position if Sharpe Ratio is below 1.0
- APPROVE if Sharpe Ratio is above 1.0 and Max Drawdown is better than -20%

Based on these rules provide:
1. Decision: APPROVED, REJECTED, or REDUCED
2. Position Size: % of portfolio to allocate (0-20%)
3. Reason: one sentence

Respond in this exact format:
Decision: <APPROVED/REJECTED/REDUCED>
Position Size: <%>
Reason: <one sentence>
"""
)

def assess_risk(ticker, signal, backtest):
    prompt = prompt_template.format(
        ticker=ticker,
        signal=signal,
        confidence=signal,
        total_return=f"{backtest['total_return']:.2%}",
        sharpe_ratio=f"{backtest['sharpe_ratio']:.2f}",
        max_drawdown=f"{backtest['max_drawdown']:.2%}"
    )

    response = llm.invoke(prompt)

    print(f"\n--- Risk Analyst: {ticker} ---")
    print(response.content)

    return {
        "ticker": ticker,
        "risk_assessment": response.content
    }

if __name__ == "__main__":
    signals_df = pd.read_csv("data/storage/trading_signals.csv")
    backtest_df = pd.read_csv("data/storage/backtest_results.csv")

    assessments = []

    for _, row in backtest_df.iterrows():
        ticker = row["ticker"]

        signal_row = signals_df[signals_df["ticker"] == ticker]
        if signal_row.empty:
            continue

        signal = signal_row.iloc[0]["signal"]

        backtest = {
            "total_return": row["total_return"],
            "sharpe_ratio": row["sharpe_ratio"],
            "max_drawdown": row["max_drawdown"]
        }

        assessment = assess_risk(ticker, signal, backtest)
        assessments.append(assessment)

    df = pd.DataFrame(assessments)
    df.to_csv("data/storage/risk_assessments.csv", index=False)
    print("\nAll risk assessments saved.")