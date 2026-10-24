import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict

from agents.news_analysis import analyze_news
from agents.sim_trading_analyst import generate_signal
from agents.risk_analyst import assess_risk
from agents.manager import make_final_decision

load_dotenv()

# Define shared state between agents
class HermesState(TypedDict):
    ticker: str
    news_analysis: str
    trading_signal: str
    risk_assessment: str
    final_decision: str

# Node 1: News Analyst
def news_analyst_node(state: HermesState):
    print(f"\n🔍 News Analyst analyzing {state['ticker']}...")
    result = analyze_news(state["ticker"])
    return {"news_analysis": result["analysis"] if result else "No news found"}

# Node 2: Simulated Trading Analyst
def sim_trading_node(state: HermesState):
    print(f"\n📊 Sim Trading Analyst analyzing {state['ticker']}...")
    backtest_df = pd.read_csv("data/storage/backtest_results.csv")
    row = backtest_df[backtest_df["ticker"] == state["ticker"]].iloc[0]
    backtest = {
        "total_return": row["total_return"],
        "sharpe_ratio": row["sharpe_ratio"],
        "max_drawdown": row["max_drawdown"]
    }
    result = generate_signal(state["ticker"], state["news_analysis"], backtest)
    return {"trading_signal": result["signal"]}

# Node 3: Risk Analyst
def risk_analyst_node(state: HermesState):
    print(f"\n🛡️ Risk Analyst analyzing {state['ticker']}...")
    backtest_df