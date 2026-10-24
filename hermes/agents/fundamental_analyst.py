import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import yfinance as yf
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

prompt_template = PromptTemplate(
    input_variables=["ticker", "fundamentals", "news"],
    template="""
You are a professional fundamental analyst specializing in long-term value investing.

Analyze the following data for {ticker} and provide a comprehensive investment analysis.

Fundamental Data:
{fundamentals}

Recent News:
{news}

Based on this data provide:
1. Verdict: STRONG BUY / BUY / HOLD / AVOID
2. Intrinsic Value Assessment: Is the stock overvalued or undervalued?
3. P/E Analysis: Is the P/E ratio attractive?
4. P/B Analysis: Is the P/B ratio attractive?
5. Debt Assessment: Is the debt level manageable?
6. Growth Assessment: Is the company growing?
7. Key Risks: Top 2 risks
8. Summary: 2 sentences max

Respond in this exact format:
Verdict: <STRONG BUY/BUY/HOLD/AVOID>
Intrinsic Value: <overvalued/undervalued/fairly valued>
P/E Analysis: <your analysis>
P/B Analysis: <your analysis>
Debt Assessment: <your analysis>
Growth Assessment: <your analysis>
Key Risks: <risk 1>, <risk 2>
Summary: <2 sentences>
"""
)

def analyze_fundamentals(ticker):
    print(f"\nFundamental Analyst analyzing {ticker}...")

    stock = yf.Ticker(ticker)
    info = stock.info

    fundamentals = f"""
    Current Price: ${info.get('currentPrice', 'N/A')}
    Market Cap: ${info.get('marketCap', 'N/A')}
    P/E Ratio: {info.get('trailingPE', 'N/A')}
    P/B Ratio: {info.get('priceToBook', 'N/A')}
    Debt to Equity: {info.get('debtToEquity', 'N/A')}
    Current Ratio: {info.get('currentRatio', 'N/A')}
    Revenue Growth: {info.get('revenueGrowth', 'N/A')}
    Net Income: ${info.get('netIncomeToCommon', 'N/A')}
    Free Cash Flow: ${info.get('freeCashflow', 'N/A')}
    Return on Equity: {info.get('returnOnEquity', 'N/A')}
    Profit Margins: {info.get('profitMargins', 'N/A')}
    """

    news = yf.Ticker(ticker).news
    news_text = "\n".join([
        f"- {n.get('content', {}).get('title', 'N/A')} (Source: {n.get('content', {}).get('provider', {}).get('displayName', 'N/A')})"
        for n in news[:5]
    ])

    prompt = prompt_template.format(
        ticker=ticker,
        fundamentals=fundamentals,
        news=news_text
    )

    response = llm.invoke(prompt)

    print(f"\n--- Fundamental Analyst Report: {ticker} ---")
    print(response.content)

    return {
        "ticker": ticker,
        "analysis": response.content,
        "news": news_text
    }

if __name__ == "__main__":
    result = analyze_fundamentals("AAPL")