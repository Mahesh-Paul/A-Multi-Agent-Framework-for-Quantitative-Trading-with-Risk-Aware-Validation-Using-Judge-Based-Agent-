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
    input_variables=["ticker", "news_analysis", "trading_signal", "risk_assessment"],
    template="""
You are the Portfolio Manager overseeing a team of analysts.

Review the following reports for {ticker} and make a final decision.

News Analyst Report:
{news_analysis}

Simulated Trading Signal:
{trading_signal}

Risk Assessment:
{risk_assessment}

Based on all three reports provide a final decision:
1. Final Action: BUY, SELL, or HOLD
2. Position Size: % of portfolio (respect risk analyst decision)
3. Summary: two sentences max

Respond in this exact format:
Final Action: <BUY/SELL/HOLD>
Position Size: <%>
Summary: <two sentences>
"""
)

def make_final_decision(ticker, news_analysis, trading_signal, risk_assessment):
    prompt = prompt_template.format(
    ticker=ticker,
    news_analysis=news_analysis,
    trading_signal=trading_signal,
    risk_assessment=risk_assessment
)

    response = llm.invoke(prompt)

    print(f"\n--- Manager Final Decision: {ticker} ---")
    print(response.content)

    return {
        "ticker": ticker,
        "final_decision": response.content
    }

if __name__ == "__main__":
    news_df = pd.read_csv("data/storage/news_analysis.csv")
    signals_df = pd.read_csv("data/storage/trading_signals.csv")
    risk_df = pd.read_csv("data/storage/risk_assessments.csv")

    final_decisions = []

    for ticker in ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]:
        news_row = news_df[news_df["ticker"] == ticker]
        signal_row = signals_df[signals_df["ticker"] == ticker]
        risk_row = risk_df[risk_df["ticker"] == ticker]

        if news_row.empty or signal_row.empty or risk_row.empty:
            print(f"Missing data for {ticker}, skipping...")
            continue

        news_analysis = news_row.iloc[0]["analysis"]
        trading_signal = signal_row.iloc[0]["signal"]
        risk_assessment = risk_row.iloc[0]["risk_assessment"]

        decision = make_final_decision(
            ticker,
            news_analysis,
            trading_signal,
            risk_assessment
        )
        final_decisions.append(decision)

    df = pd.DataFrame(final_decisions)
    df.to_csv("data/storage/final_decisions.csv", index=False)
    print("\n✅ Final decisions saved to data/storage/final_decisions.csv")