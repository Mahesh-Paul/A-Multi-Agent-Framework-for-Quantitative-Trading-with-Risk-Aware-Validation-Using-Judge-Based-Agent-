import os
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass
import chromadb
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

client = chromadb.PersistentClient(path="memory/chroma_db")
market_memory = client.get_or_create_collection("market_memory")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

prompt_template = PromptTemplate(
    input_variables=["ticker", "news"],
    template="""
You are a professional financial news analyst.

Analyze the following recent news headlines for {ticker} and provide:
1. Overall sentiment: BULLISH, BEARISH, or NEUTRAL
2. Confidence score: 0-100
3. Key reason in one sentence

News Headlines:
{news}

Respond in this exact format:
Sentiment: <BULLISH/BEARISH/NEUTRAL>
Confidence: <0-100>
Reason: <one sentence>
"""
)

def analyze_news(ticker):
    results = market_memory.query(
        query_texts=[f"{ticker} stock news"],
        n_results=10,
        where={"ticker": ticker}
    )

    if not results["documents"][0]:
        print(f"No news found for {ticker}")
        return None

    news_text = "\n".join(results["documents"][0])
    prompt = prompt_template.format(ticker=ticker, news=news_text)
    response = llm.invoke(prompt)

    print(f"\n--- News Analyst Report: {ticker} ---")
    print(response.content)

    return {
        "ticker": ticker,
        "analysis": response.content
    }

if __name__ == "__main__":
    TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "NVDA"]
    reports = []

    for ticker in TICKERS:
        report = analyze_news(ticker)
        if report:
            reports.append(report)

    df = pd.DataFrame(reports)
    df.to_csv("data/storage/news_analysis.csv", index=False)
    print("\nAll news analysis saved.")