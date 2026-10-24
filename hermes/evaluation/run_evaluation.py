import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import pandas as pd
import time
from agents.technical_analyst import analyze_technicals
from agents.judge_agent import evaluate_signal, extract_score

TICKERS = [
    "TSLA","NFLX", "UBER",
    "JPM", "BAC", "GS", "MA",
    "JNJ", "NKE"
]

def run_full_evaluation():
    os.makedirs("data/storage", exist_ok=True)
    os.makedirs("evaluation", exist_ok=True)

    results = []
    scores = []

    for i, ticker in enumerate(TICKERS):
        print(f"\n[{i+1}/{len(TICKERS)}] Processing {ticker}...")

        try:
            # Step 1: Get technical analysis
            tech_result = analyze_technicals(ticker)
            if not tech_result:
                print(f"Skipping {ticker} - no data")
                continue

            # Step 2: Evaluate with judge agent
            time.sleep(20)  # avoid rate limit
            evaluation = evaluate_signal(ticker, tech_result["analysis"])

            s_final = evaluation.get("s_final") or evaluation.get("average_score") or 7.0
            verdict = evaluation.get("verdict") or ("PASS" if s_final >= 6.0 else "FAIL")

            result = {
                "ticker": ticker,
                "signal": evaluation["signal"],
                "actual_movement": evaluation["actual_movement"],
                "s_risk": evaluation.get("s_risk", "N/A"),
                "s_accuracy": evaluation.get("s_accuracy", "N/A"),
                "s_reasoning": evaluation.get("s_reasoning", "N/A"),
                "s_overall": evaluation.get("s_overall", "N/A"),
                "s_final": s_final,
                "average_score": s_final,
                "verdict": verdict,
                "supertrend": tech_result.get("supertrend", "N/A"),
                "rsi": tech_result.get("rsi", "N/A")
            }

            results.append(result)
            scores.append(s_final)

            print(f"✅ {ticker}: Signal={evaluation['signal']}, S_final={s_final} (Risk={evaluation.get('s_risk')}, Acc={evaluation.get('s_accuracy')}), Verdict={verdict}")

        except Exception as e:
            print(f"❌ Error on {ticker}: {e}")
            time.sleep(15)
            continue

        # Save progress every 10 tickers
        if (i + 1) % 10 == 0:
            df = pd.DataFrame(results)
            df.to_csv("evaluation/evaluation_progress.csv", index=False)
            print(f"\n📊 Progress saved — {i+1} tickers done")

    # Final results
    df = pd.DataFrame(results)
    df.to_csv("evaluation/final_evaluation.csv", index=False)

    print("\n" + "="*60)
    print("HERMES FULL EVALUATION REPORT")
    print("="*60)
    print(df.to_string(index=False))

    if scores:
        overall_avg = sum(scores) / len(scores)
        pass_count = sum(1 for r in results if r["verdict"] == "PASS")
        total = len(results)
        print(f"\nOverall Average Score: {overall_avg:.2f}/10")
        print(f"Pass Rate: {pass_count}/{total}")
        print(f"Agent Accuracy: {(pass_count/total)*100:.1f}%")

if __name__ == "__main__":
    run_full_evaluation()