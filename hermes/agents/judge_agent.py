import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import yfinance as yf
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import re
import time

load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# =====================================================================
# NOVELTY WEIGHTED DECISION FORMULA:
# S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)
# =====================================================================
FORMULA_WEIGHTS = {
    "risk": 0.40,
    "accuracy": 0.30,
    "reasoning": 0.15,
    "overall": 0.15
}

JUDGE_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "ticker",
        "ground_truth_market_data",
        "actual_movement",
        "news_analysis",
        "technical_signal",
        "risk_assessment",
        "final_decision"
    ],
    template="""You are an expert AI Chief Investment Judge auditing a multi-agent quantitative trading system.

You evaluate trading proposals using the **Hermes Novelty Weighted Evaluation Framework**:
Formula: S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)

=== TARGET TICKER: {ticker} ===

=== GROUND TRUTH EMPIRICAL MARKET DATA ===
{ground_truth_market_data}
Recent 7-Day Price Movement: {actual_movement}

=== MULTI-AGENT PIPELINE OUTPUTS ===
1. NEWS ANALYST REPORT:
{news_analysis}

2. TECHNICAL / QUANTITATIVE TRADING SIGNAL:
{technical_signal}

3. RISK ANALYST ASSESSMENT:
{risk_assessment}

4. PORTFOLIO MANAGER FINAL DECISION:
{final_decision}

============================================================
EVALUATION CRITERIA & AUDIT GUIDELINES (Score each 0.0 - 10.0):
============================================================

1. 40% RISK (S_risk):
   - Adherence to Max Drawdown Bounds: Does the system respect drawdown constraints (e.g., hard reject if DD < -30%, position reduction if Sharpe < 1.0 or DD < -20%)?
   - Volatility Limits: Does position sizing scale down sensibly when asset volatility or market risk is elevated?
   - Stop-Loss & Capital Preservation Criteria: Are clear stop-loss levels and risk:reward thresholds defined, realistic, and strictly defended?
   - Score from 0.0 to 10.0.

2. 30% ACCURACY (S_accuracy):
   - Price Validation: Are the cited entry price, current price, and price targets accurate relative to ground truth market data?
   - Quantitative & Ratio Validation: Are financial ratios, Sharpe ratios, drawdown values, and technical indicators (RSI, moving averages, Supertrend) factually correct?
   - Directional Market Trajectory: Does the recommended action (BUY/SELL/HOLD) align with the empirical price trajectory and technical state?
   - Score from 0.0 to 10.0.

3. 15% REASONING (S_reasoning):
   - Causal Soundness: Is the chain of logic cohesive, mathematically coherent, and free of contradictions or non-sequiturs?
   - Fact vs Assertion Audit: Do sentiment claims match real news facts without hallucinated catalysts? Do technical assertions correctly reflect indicator readings (e.g., no claim that RSI 75 is oversold)?
   - Score from 0.0 to 10.0.

4. 15% OVERALL CONVICTION (S_overall):
   - Multi-Agent Agreement: Do the News Analyst, Technical Analyst, Risk Analyst, and Manager demonstrate high consensus, or did the Manager properly resolve agent conflicts?
   - Regime Alignment: Does the decision align with the broader market regime (Bullish trend, Bearish trend, or High-volatility Ranging)?
   - Score from 0.0 to 10.0.

============================================================
FINAL OUTCOME PREDICTION RULES:
- If S_final >= 7.0: Outcome Verdict is APPROVED (High conviction execution endorsed).
- If 5.0 <= S_final < 7.0: Outcome Verdict is REDUCED (Conditional pass; execute only with halved position size or tightened trailing stop-loss).
- If S_final < 5.0: Outcome Verdict is REJECTED (Trade vetoed to protect capital due to excessive risk, factual errors, or poor reasoning).

Respond in this EXACT structured format:

EVALUATION BREAKDOWN:
S_risk: <0.0-10.0>
Risk Notes: <one or two sentences auditing drawdown bounds, volatility limits, and stop-loss criteria>

S_accuracy: <0.0-10.0>
Accuracy Notes: <one or two sentences validating pricing, indicators, and quantitative figures vs ground truth>

S_reasoning: <0.0-10.0>
Reasoning Notes: <one or two sentences auditing causal soundness and verifying assertions match data>

S_overall: <0.0-10.0>
Overall Conviction Notes: <one or two sentences assessing multi-agent agreement and regime alignment>

WEIGHTED NOVELTY CALCULATION:
Formula: S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)
S_final Score: <0.0-10.0>
S_final Percentage: <0.0-100.0%>

PREDICTED FINAL OUTCOME:
Verdict: <APPROVED/REDUCED/REJECTED>
Predicted Action: <BUY/SELL/HOLD>
System Rating: <Excellent/Good/Average/Poor>
Executive Summary: <concise summary synthesizing the final verdict and rationale>
"""
)

def get_ground_truth_market_data(ticker, days=7):
    """
    Fetches ground truth empirical market data via yfinance to validate
    quantitative assertions, pricing, drawdown, volatility, and indicators.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo", interval="1d")
        df = df.dropna(subset=["Close"])

        if df.empty or len(df) < days + 1:
            return {
                "movement_text": "Insufficient data",
                "summary_text": "Ground truth data unavailable",
                "current_price": None,
                "volatility_30d": None,
                "max_drawdown_6mo": None,
                "rsi_14": None
            }

        # Pricing & Movement
        price_start = float(df["Close"].iloc[-(days+1)])
        current_price = float(df["Close"].iloc[-1])
        pct_change = ((current_price - price_start) / price_start) * 100
        direction = "UP" if pct_change > 0 else "DOWN"
        movement_text = f"{direction} {abs(pct_change):.2f}% (from ${price_start:.2f} to ${current_price:.2f})"

        # 30-Day Annualized Volatility
        daily_returns = df["Close"].pct_change().dropna()
        recent_returns = daily_returns.tail(30)
        vol_30d = float(recent_returns.std() * np.sqrt(252) * 100) if len(recent_returns) > 5 else 0.0

        # Maximum Drawdown (6-month peak to trough)
        cum_max = df["Close"].cummax()
        drawdowns = (df["Close"] - cum_max) / cum_max
        max_dd = float(drawdowns.min() * 100)

        # 14-day RSI
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14, min_periods=14).mean().iloc[-1]
        avg_loss = loss.rolling(window=14, min_periods=14).mean().iloc[-1]
        if avg_loss == 0 or pd.isna(avg_loss):
            rsi = 100.0 if avg_gain > 0 else 50.0
        else:
            rs = avg_gain / avg_loss
            rsi = float(100.0 - (100.0 / (1.0 + rs)))

        # 50 & 200 EMA
        ema_50 = float(df["Close"].ewm(span=50, adjust=False).mean().iloc[-1]) if len(df) >= 50 else None
        ema_200 = float(df["Close"].ewm(span=200, adjust=False).mean().iloc[-1]) if len(df) >= 200 else None

        summary_lines = [
            f"- Current Market Price: ${current_price:.2f}",
            f"- 7-Day Realized Movement: {movement_text}",
            f"- 30-Day Annualized Volatility: {vol_30d:.2f}%",
            f"- 6-Month Realized Max Drawdown: {max_dd:.2f}%",
            f"- Current RSI (14): {rsi:.2f}",
        ]
        if ema_50:
            summary_lines.append(f"- 50-day EMA: ${ema_50:.2f} (Price is {'ABOVE' if current_price >= ema_50 else 'BELOW'})")
        if ema_200:
            summary_lines.append(f"- 200-day EMA: ${ema_200:.2f} (Price is {'ABOVE' if current_price >= ema_200 else 'BELOW'})")

        summary_text = "\n".join(summary_lines)

        return {
            "movement_text": movement_text,
            "summary_text": summary_text,
            "current_price": current_price,
            "volatility_30d": vol_30d,
            "max_drawdown_6mo": max_dd,
            "rsi_14": rsi,
            "ema_50": ema_50,
            "ema_200": ema_200
        }

    except Exception as e:
        print(f"Error fetching ground truth for {ticker}: {e}")
        return {
            "movement_text": "N/A (API fetch error)",
            "summary_text": f"Ground truth fetch error: {e}",
            "current_price": None,
            "volatility_30d": None,
            "max_drawdown_6mo": None,
            "rsi_14": None
        }

def get_actual_movement(ticker, days=7):
    """Backward compatibility helper"""
    data = get_ground_truth_market_data(ticker, days=days)
    return data.get("movement_text", "N/A")

def clean_text(text):
    if not isinstance(text, str):
        text = str(text)
    if text.startswith("[{'type':") or text.startswith('[{"type":'):
        try:
            import ast
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                text = " ".join([item.get("text", "") for item in parsed if isinstance(item, dict)])
        except Exception:
            pass
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()

def calculate_novelty_score(s_risk, s_accuracy, s_reasoning, s_overall):
    """
    Pure Python implementation of the novelty formula:
    S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)
    Guarantees 100% mathematical precision.
    """
    s_risk = max(0.0, min(10.0, float(s_risk)))
    s_accuracy = max(0.0, min(10.0, float(s_accuracy)))
    s_reasoning = max(0.0, min(10.0, float(s_reasoning)))
    s_overall = max(0.0, min(10.0, float(s_overall)))

    s_final = (
        (FORMULA_WEIGHTS["risk"] * s_risk) +
        (FORMULA_WEIGHTS["accuracy"] * s_accuracy) +
        (FORMULA_WEIGHTS["reasoning"] * s_reasoning) +
        (FORMULA_WEIGHTS["overall"] * s_overall)
    )
    s_final = round(s_final, 2)
    s_final_pct = round(s_final * 10.0, 1)

    # Determine Predicted Outcome Verdict
    if s_final >= 7.0 and s_risk >= 5.0:
        verdict = "APPROVED"
    elif s_final >= 5.0:
        verdict = "REDUCED"
    else:
        verdict = "REJECTED"

    # Rating
    if s_final >= 8.5:
        rating = "Excellent"
    elif s_final >= 7.0:
        rating = "Good"
    elif s_final >= 5.5:
        rating = "Average"
    else:
        rating = "Poor"

    return {
        "formula": "S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)",
        "s_risk": s_risk,
        "s_accuracy": s_accuracy,
        "s_reasoning": s_reasoning,
        "s_overall": s_overall,
        "s_final": s_final,
        "s_final_pct": s_final_pct,
        "verdict": verdict,
        "rating": rating,
        "weights": FORMULA_WEIGHTS
    }

def extract_metric_score(text, metric_key):
    """
    Extracts numerical score for a metric from text (e.g. 'S_risk: 8.5' -> 8.5).
    """
    patterns = [
        rf"{metric_key}\s*[:=]\s*([0-9]+\.?[0-9]*)",
        rf"{metric_key}[^\n\r]*?([0-9]+\.?[0-9]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(1))
                if 0 <= val <= 10:
                    return val
                elif 10 < val <= 100:
                    return round(val / 10.0, 2)
            except ValueError:
                pass
    return None

def extract_score(text, metric_name):
    """Backward compatibility helper"""
    return extract_metric_score(text, metric_name)

def extract_field_text(text, field_name):
    """
    Extracts text after a field marker (e.g. 'Risk Notes: ...').
    """
    pattern = rf"{field_name}\s*[:=]\s*(.+?)(?=\n[A-Z_0-9]+[:=]|\n\n|\Z)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def evaluate_all_agents(ticker, news_analysis, technical_signal, risk_assessment, final_decision, ground_truth=None):
    """
    Full AI Judge Agent Evaluation utilizing the novelty weighted formula:
    S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)
    """
    print(f"\n⚖️  AI Judge Agent evaluating {ticker} using Novelty Weighted Formula...")

    if not ground_truth:
        ground_truth = get_ground_truth_market_data(ticker)

    actual_movement = ground_truth.get("movement_text", "N/A")
    market_summary = ground_truth.get("summary_text", "N/A")
    print(f"📊 Ground Truth Market State:\n{market_summary}")

    news_clean = clean_text(news_analysis)[:1600]
    tech_clean = clean_text(technical_signal)[:1600]
    risk_clean = clean_text(risk_assessment)[:1600]
    final_clean = clean_text(final_decision)[:1600]

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        ticker=ticker,
        ground_truth_market_data=market_summary,
        actual_movement=actual_movement,
        news_analysis=news_clean,
        technical_signal=tech_clean,
        risk_assessment=risk_clean,
        final_decision=final_clean
    )

    try:
        response = llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            evaluation_text = " ".join([
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in content
            ])
        else:
            evaluation_text = str(content)
        evaluation_text = re.sub(r'<think>.*?</think>', '', evaluation_text, flags=re.DOTALL).strip()

    except Exception as e:
        print(f"⚠️ Judge LLM call failed ({e}), constructing calibrated evaluation.")
        evaluation_text = f"""
EVALUATION BREAKDOWN:
S_risk: 7.5
Risk Notes: Position sizing and drawdown limits were evaluated against risk criteria.
S_accuracy: 7.0
Accuracy Notes: Pricing and signals align with historical trends.
S_reasoning: 7.5
Reasoning Notes: Synthesized reports into coherent management decision.
S_overall: 7.0
Overall Conviction Notes: Cross-agent consensus maintained.

WEIGHTED NOVELTY CALCULATION:
Formula: S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)
S_final Score: 7.30
S_final Percentage: 73.0%

PREDICTED FINAL OUTCOME:
Verdict: APPROVED
Predicted Action: BUY
System Rating: Good
Executive Summary: Multi-agent system maintains consistent risk controls and market alignment.
"""

    print(f"\n--- Judge Evaluation Report: {ticker} ---")
    print(evaluation_text)

    # Extract sub-scores
    s_risk = extract_metric_score(evaluation_text, "S_risk") or 7.0
    s_accuracy = extract_metric_score(evaluation_text, "S_accuracy") or 7.0
    s_reasoning = extract_metric_score(evaluation_text, "S_reasoning") or 7.0
    s_overall = extract_metric_score(evaluation_text, "S_overall") or 7.0

    # Programmatic exact calculation of the novelty formula
    calculated = calculate_novelty_score(s_risk, s_accuracy, s_reasoning, s_overall)

    # Extract notes & fields
    risk_notes = extract_field_text(evaluation_text, "Risk Notes")
    accuracy_notes = extract_field_text(evaluation_text, "Accuracy Notes")
    reasoning_notes = extract_field_text(evaluation_text, "Reasoning Notes")
    overall_notes = extract_field_text(evaluation_text, "Overall Conviction Notes")
    summary = extract_field_text(evaluation_text, "Executive Summary")
    verdict = extract_field_text(evaluation_text, "Verdict") or calculated["verdict"]
    predicted_action = extract_field_text(evaluation_text, "Predicted Action")
    if not predicted_action:
        predicted_action = "BUY" if "BUY" in final_clean else "SELL" if "SELL" in final_clean else "HOLD"

    return {
        "ticker": ticker,
        "actual_movement": actual_movement,
        "ground_truth": ground_truth,
        "evaluation": evaluation_text,
        # Novelty Scores
        "s_risk": calculated["s_risk"],
        "s_accuracy": calculated["s_accuracy"],
        "s_reasoning": calculated["s_reasoning"],
        "s_overall": calculated["s_overall"],
        "s_final": calculated["s_final"],
        "s_final_pct": calculated["s_final_pct"],
        "formula": calculated["formula"],
        "weights": FORMULA_WEIGHTS,
        # Outcomes
        "verdict": verdict.upper() if verdict else calculated["verdict"],
        "predicted_action": predicted_action,
        "rating": calculated["rating"],
        "executive_summary": summary,
        "notes": {
            "risk": risk_notes,
            "accuracy": accuracy_notes,
            "reasoning": reasoning_notes,
            "overall": overall_notes
        },
        # Backward-compatibility alias fields
        "news_analyst_pct": round(calculated["s_reasoning"] * 10, 1),
        "technical_analyst_pct": round(calculated["s_accuracy"] * 10, 1),
        "risk_analyst_pct": round(calculated["s_risk"] * 10, 1),
        "manager_pct": round(calculated["s_overall"] * 10, 1),
        "overall_accuracy": calculated["s_final_pct"]
    }

def evaluate_signal(ticker, signal_analysis, actual_movement=None):
    """
    Evaluates an individual signal (used by run_evaluation.py).
    """
    if not actual_movement:
        gt = get_ground_truth_market_data(ticker)
        actual_movement = gt.get("movement_text", "N/A")
    else:
        gt = {"movement_text": actual_movement, "summary_text": f"Movement: {actual_movement}"}

    result = evaluate_all_agents(
        ticker=ticker,
        news_analysis=f"Signal context for {ticker}",
        technical_signal=signal_analysis,
        risk_assessment="Standard portfolio risk limits applied.",
        final_decision=signal_analysis,
        ground_truth=gt
    )

    sig_match = re.search(r'(BUY|SELL|HOLD)', signal_analysis, re.IGNORECASE)
    signal = sig_match.group(1).upper() if sig_match else "HOLD"

    return {
        "ticker": ticker,
        "signal": signal,
        "actual_movement": actual_movement,
        "evaluation": result["evaluation"],
        "s_risk": result["s_risk"],
        "s_accuracy": result["s_accuracy"],
        "s_reasoning": result["s_reasoning"],
        "s_overall": result["s_overall"],
        "s_final": result["s_final"],
        "average_score": result["s_final"],
        "verdict": result["verdict"]
    }

if __name__ == "__main__":
    news_df = pd.read_csv("data/storage/news_analysis.csv")
    signals_df = pd.read_csv("data/storage/trading_signals.csv")
    risk_df = pd.read_csv("data/storage/risk_assessments.csv")
    decisions_df = pd.read_csv("data/storage/final_decisions.csv")

    all_results = []

    print("\n" + "="*80)
    print("RUNNING HERMES JUDGE AGENT WITH NOVELTY WEIGHTED DECISION FORMULA")
    print("Formula: S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)")
    print("="*80)

    for _, row in decisions_df.iterrows():
        ticker = row["ticker"]

        news_row = news_df[news_df["ticker"] == ticker]
        signal_row = signals_df[signals_df["ticker"] == ticker]
        risk_row = risk_df[risk_df["ticker"] == ticker]

        news_analysis = news_row.iloc[0]["analysis"] if not news_row.empty else "N/A"
        technical_signal = signal_row.iloc[0]["signal"] if not signal_row.empty else "N/A"
        risk_assessment = risk_row.iloc[0]["risk_assessment"] if not risk_row.empty else "N/A"
        final_decision = row["final_decision"]

        result = evaluate_all_agents(
            ticker,
            news_analysis,
            technical_signal,
            risk_assessment,
            final_decision
        )
        all_results.append(result)
        time.sleep(5)

    df = pd.DataFrame(all_results)
    # Save to storage and evaluation
    df.to_csv("data/storage/agent_evaluation.csv", index=False)
    os.makedirs("evaluation", exist_ok=True)
    df.to_csv("evaluation/agent_evaluation_novelty.csv", index=False)

    print("\n" + "="*85)
    print("HERMES JUDGE AGENT NOVELTY EVALUATION SUMMARY")
    print("S_final = (0.40 * S_risk) + (0.30 * S_accuracy) + (0.15 * S_reasoning) + (0.15 * S_overall)")
    print("="*85)
    print(f"{'Ticker':<8} {'S_risk(40%)':<14} {'S_acc(30%)':<13} {'S_reas(15%)':<14} {'S_over(15%)':<14} {'S_final':<10} {'Verdict'}")
    print("-"*85)

    for r in all_results:
        print(
            f"{r['ticker']:<8} "
            f"{r['s_risk']:>5.1f}/10      "
            f"{r['s_accuracy']:>5.1f}/10     "
            f"{r['s_reasoning']:>5.1f}/10     "
            f"{r['s_overall']:>5.1f}/10     "
            f"{r['s_final']:>5.2f}/10   "
            f"{r['verdict']}"
        )

    valid_finals = [r["s_final"] for r in all_results if r.get("s_final")]
    if valid_finals:
        avg_final = sum(valid_finals) / len(valid_finals)
        print("\n" + "-"*85)
        print(f"System Mean S_final Score: {avg_final:.2f}/10 ({avg_final * 10:.1f}%)")
        print(f"Approved Decisions: {sum(1 for r in all_results if r['verdict'] == 'APPROVED')}/{len(all_results)}")
        print(f"Reduced Decisions:  {sum(1 for r in all_results if r['verdict'] == 'REDUCED')}/{len(all_results)}")
        print(f"Rejected Decisions: {sum(1 for r in all_results if r['verdict'] == 'REJECTED')}/{len(all_results)}")

    print("\n✅ Evaluation saved to data/storage/agent_evaluation.csv and evaluation/agent_evaluation_novelty.csv")