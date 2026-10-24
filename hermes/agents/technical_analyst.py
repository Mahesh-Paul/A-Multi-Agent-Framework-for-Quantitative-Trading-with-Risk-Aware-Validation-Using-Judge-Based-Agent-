import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

prompt_template = PromptTemplate(
    input_variables=["ticker", "technical_data", "news", "patterns", "signal_score", "trend_confirmation", "regime", "confluence"],
    template="""
You are a professional technical analyst with 20 years of experience trading US equities.

Analyze {ticker}:

Technical Data:
{technical_data}

Chart Patterns:
{patterns}

News:
{news}

SYSTEM PRE-ANALYSIS:
Signal Score: {signal_score} (scale -10 to +10)
Trend Confirmation: {trend_confirmation}
Market Regime: {regime}
Indicator Confluence: {confluence}

DECISION RULES — follow in strict order:
1. Signal Score > 3 → BUY
2. Signal Score < -3 → SELL
3. Signal Score 0.5 to 3 + price above EMA200 → BUY
4. Signal Score -0.5 to -3 + price below EMA200 → SELL
5. RSI > 78 → SELL regardless of other signals
6. RSI < 22 → BUY regardless of other signals
7. Supertrend BULLISH + EMA alignment BULLISH (20>50>200) → BUY
8. Supertrend BEARISH + EMA alignment BEARISH (20<50<200) → SELL
9. HOLD only if score between -1 and 1 AND regime is RANGING
10. NEVER HOLD if price clearly above EMA200 with score above 1
11. NEVER HOLD if price clearly below EMA200 with score below -1

Provide DECISIVE signal:
Signal: <BUY/SELL/HOLD>
Trend: <UPTREND/DOWNTREND/SIDEWAYS>
Strength: <STRONG/MODERATE/WEAK>
Confidence: <0-100>
Entry Price: <price>
Stop Loss: <price>
Target: <price>
Key Levels: <support and resistance>
Summary: <2 sentences>
"""
)

def detect_patterns(df):
    patterns = []
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(latest["Close"] - latest["Open"])
    wick = latest["High"] - latest["Low"]

    if (prev["Close"] < prev["Open"] and latest["Close"] > latest["Open"] and
            latest["Close"] > prev["Open"] and latest["Open"] < prev["Close"]):
        patterns.append("Bullish Engulfing")

    if (prev["Close"] > prev["Open"] and latest["Close"] < latest["Open"] and
            latest["Close"] < prev["Open"] and latest["Open"] > prev["Close"]):
        patterns.append("Bearish Engulfing")

    if wick > 0 and body / wick < 0.1:
        patterns.append("Doji")

    lower_wick = min(latest["Open"], latest["Close"]) - latest["Low"]
    upper_wick = latest["High"] - max(latest["Open"], latest["Close"])

    if lower_wick > 2 * body and upper_wick < body:
        patterns.append("Bullish Pin Bar")
    if upper_wick > 2 * body and lower_wick < body:
        patterns.append("Bearish Pin Bar")

    if latest["High"] > prev["High"] and latest["Low"] > prev["Low"]:
        patterns.append("Higher High Higher Low (Bullish)")
    elif latest["High"] < prev["High"] and latest["Low"] < prev["Low"]:
        patterns.append("Lower High Lower Low (Bearish)")

    if latest["Open"] > prev["High"]:
        patterns.append("Gap Up")
    elif latest["Open"] < prev["Low"]:
        patterns.append("Gap Down")

    return patterns if patterns else ["No significant pattern"]

def calculate_signal_score(current_price, ema20, ema50, ema200, rsi, macd, macd_signal, adx, supertrend_dir, volume_spike, stoch_k, stoch_d, bb_upper, bb_lower):
    score = 0

    # Supertrend — weighted 1.5x
    if supertrend_dir == 1:
        score += 1.5
    elif supertrend_dir == -1:
        score -= 1.5

    # EMA alignment
    if ema20 and ema50 and ema200:
        if current_price > ema200:
            score += 1
        else:
            score -= 1
        if current_price > ema50:
            score += 0.5
        else:
            score -= 0.5
        if ema20 > ema50 > ema200:
            score += 1.5
        elif ema20 < ema50 < ema200:
            score -= 1.5

    # RSI
    if rsi:
        if rsi < 30:
            score += 2
        elif rsi < 45:
            score += 0.5
        elif rsi > 70:
            score -= 2
        elif rsi > 55:
            score -= 0.5

    # MACD
    if macd and macd_signal:
        if macd > macd_signal:
            score += 1
        else:
            score -= 1

    # Stochastic
    if stoch_k and stoch_d:
        if stoch_k > stoch_d and stoch_k < 80:
            score += 0.5
        elif stoch_k < stoch_d and stoch_k > 20:
            score -= 0.5

    # Bollinger Bands
    if bb_upper and bb_lower:
        if current_price < bb_lower:
            score += 1
        elif current_price > bb_upper:
            score -= 1

    # Volume confirmation
    if volume_spike == "YES":
        score = score * 1.2

    # ADX amplification
    if adx and adx > 25:
        score = score * 1.1

    return round(score, 1)

def get_trend_confirmation(current_price, ema20, ema50, ema200):
    if not all([ema20, ema50, ema200]):
        return "INSUFFICIENT DATA"
    if ema20 > ema50 > ema200 and current_price > ema20:
        return "STRONG UPTREND"
    elif ema20 < ema50 < ema200 and current_price < ema20:
        return "STRONG DOWNTREND"
    elif current_price > ema200:
        return "WEAK UPTREND"
    elif current_price < ema200:
        return "WEAK DOWNTREND"
    else:
        return "SIDEWAYS"

def get_market_regime(df):
    adx_col = [c for c in df.columns if "ADX_" in c]
    if not adx_col:
        return "UNKNOWN"
    recent_adx = df[adx_col[0]].tail(5).mean()
    if recent_adx > 25:
        return "TRENDING"
    else:
        return "RANGING"

def get_confluence(supertrend_dir, macd, macd_signal, rsi, current_price, ema200):
    bullish_count = 0
    bearish_count = 0

    if supertrend_dir == 1: bullish_count += 1
    elif supertrend_dir == -1: bearish_count += 1

    if macd and macd_signal:
        if macd > macd_signal: bullish_count += 1
        else: bearish_count += 1

    if rsi:
        if rsi < 50: bullish_count += 1
        else: bearish_count += 1

    if ema200 and current_price > ema200: bullish_count += 1
    elif ema200: bearish_count += 1

    if bullish_count >= 3:
        return f"STRONG BULLISH CONFLUENCE ({bullish_count}/4 bullish)"
    elif bearish_count >= 3:
        return f"STRONG BEARISH CONFLUENCE ({bearish_count}/4 bearish)"
    else:
        return f"MIXED ({bullish_count} bullish, {bearish_count} bearish)"

def analyze_technicals(ticker):
    print(f"\nTechnical Analyst analyzing {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y", interval="1d")
        df = df.dropna(subset=["Close"])

        if df.empty or len(df) < 50:
            return None

        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.atr(length=14, append=True)
        df.ta.adx(length=14, append=True)
        df.ta.bbands(length=20, append=True)
        df.ta.supertrend(length=10, multiplier=3, append=True)
        df.ta.stoch(append=True)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        current_price = float(latest["Close"])

        def fmt(v):
            return f"{v:.2f}" if isinstance(v, float) else str(v)

        def safe_float(val):
            try:
                v = float(val)
                return v if v != 0 else None
            except:
                return None

        ema20 = safe_float(latest.get("EMA_20"))
        ema50 = safe_float(latest.get("EMA_50"))
        ema200 = safe_float(latest.get("EMA_200"))
        rsi = safe_float(latest.get("RSI_14"))
        macd = safe_float(latest.get("MACD_12_26_9")) or 0
        macd_signal = safe_float(latest.get("MACDs_12_26_9")) or 0
        atr = safe_float(latest.get("ATRr_14"))
        adx = safe_float(latest.get("ADX_14"))
        bb_upper = safe_float(latest.get("BBU_20_2.0"))
        bb_lower = safe_float(latest.get("BBL_20_2.0"))
        stoch_k = safe_float(latest.get("STOCHk_14_3_3"))
        stoch_d = safe_float(latest.get("STOCHd_14_3_3"))

        supertrend_col = [c for c in df.columns if "SUPERT_" in c and "d" not in c.lower()]
        supertrend_dir_col = [c for c in df.columns if "SUPERTd_" in c]
        supertrend_dir = int(latest.get(supertrend_dir_col[0], 0)) if supertrend_dir_col else None
        supertrend_signal = "BULLISH" if supertrend_dir == 1 else "BEARISH" if supertrend_dir == -1 else "NEUTRAL"

        volume_avg = df["Volume"].tail(20).mean()
        volume_spike = "YES" if latest["Volume"] > volume_avg * 1.5 else "NO"

        signal_score = calculate_signal_score(
            current_price, ema20, ema50, ema200, rsi,
            macd, macd_signal, adx, supertrend_dir,
            volume_spike, stoch_k, stoch_d, bb_upper, bb_lower
        )

        trend_confirmation = get_trend_confirmation(current_price, ema20, ema50, ema200)
        regime = get_market_regime(df)
        confluence = get_confluence(supertrend_dir, macd, macd_signal, rsi, current_price, ema200)
        patterns = detect_patterns(df)

        technical_data = f"""
Current Price: ${fmt(current_price)}
EMA 20: {fmt(ema20)} → Price {'ABOVE ✅' if ema20 and current_price > ema20 else 'BELOW ❌'}
EMA 50: {fmt(ema50)} → Price {'ABOVE ✅' if ema50 and current_price > ema50 else 'BELOW ❌'}
EMA 200: {fmt(ema200)} → Price {'ABOVE ✅' if ema200 and current_price > ema200 else 'BELOW ❌'}
EMA Alignment: {'BULLISH ✅ (20>50>200)' if ema20 and ema50 and ema200 and ema20 > ema50 > ema200 else 'BEARISH ❌ (20<50<200)' if ema20 and ema50 and ema200 and ema20 < ema50 < ema200 else 'MIXED'}
RSI (14): {fmt(rsi)} → {'🔴 OVERBOUGHT' if rsi and rsi > 70 else '🟢 OVERSOLD' if rsi and rsi < 30 else '🟡 NEUTRAL'}
MACD: {fmt(macd)} | Signal: {fmt(macd_signal)} → {'🟢 BULLISH' if macd > macd_signal else '🔴 BEARISH'}
ADX (14): {fmt(adx)} → {'💪 STRONG' if adx and adx > 25 else '😐 WEAK'}
ATR (14): {fmt(atr)}
Bollinger Upper: {fmt(bb_upper)} | Lower: {fmt(bb_lower)}
Stochastic K: {fmt(stoch_k)} | D: {fmt(stoch_d)} → {'🟢 BULLISH' if stoch_k and stoch_d and stoch_k > stoch_d else '🔴 BEARISH'}
Supertrend: {'🟢 BULLISH' if supertrend_signal == 'BULLISH' else '🔴 BEARISH'}
Volume Spike: {'🟢 YES' if volume_spike == 'YES' else '⚪ NO'}
Higher High: {'YES' if latest['High'] > prev['High'] else 'NO'}
Higher Low: {'YES' if latest['Low'] > prev['Low'] else 'NO'}
"""

        news = yf.Ticker(ticker).news
        news_text = "\n".join([
            f"- {n.get('content', {}).get('title', 'N/A')}"
            for n in news[:3]
        ])

        prompt = prompt_template.format(
            ticker=ticker,
            technical_data=technical_data,
            news=news_text,
            patterns="\n".join(patterns),
            signal_score=signal_score,
            trend_confirmation=trend_confirmation,
            regime=regime,
            confluence=confluence
        )

        try:
            response = llm.invoke(prompt)
            content = response.content
            if isinstance(content, list):
                analysis_text = " ".join([
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                ])
            else:
                analysis_text = str(content)
        except Exception as e:
            print(f"Technical LLM call failed (using fallback analysis): {e}")
            # Fallback text based on indicator rules
            act_sig = "BUY" if signal_score > 3 or (0.5 <= signal_score <= 3 and current_price > ema200) else "SELL" if signal_score < -3 or (-3 <= signal_score <= -0.5 and current_price < ema200) else "HOLD"
            analysis_text = f"""
Provide DECISIVE signal:
Signal: {act_sig}
Trend: {trend_confirmation}
Strength: {"STRONG" if adx and adx > 25 else "WEAK"}
Confidence: {int(min(100, max(0, abs(signal_score) * 10)))}
Entry Price: {current_price:.2f}
Stop Loss: {current_price * 0.95:.2f}
Target: {current_price * 1.10:.2f}
            Key Levels: Support {(bb_lower if bb_lower is not None else current_price*0.9):.2f}, Resistance {(bb_upper if bb_upper is not None else current_price*1.1):.2f}
Summary: Technical indicators evaluate to {act_sig} with a signal score of {signal_score}. Regime is {regime}.
"""

        print(f"\n--- Technical Analyst Report: {ticker} ---")
        print(analysis_text)

        return {
            "ticker": ticker,
            "analysis": analysis_text,
            "current_price": current_price,
            "rsi": rsi,
            "macd": macd,
            "supertrend": supertrend_signal,
            "signal_score": signal_score,
            "trend_confirmation": trend_confirmation,
            "regime": regime,
            "confluence": confluence
        }

    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

if __name__ == "__main__":
    result = analyze_technicals("AAPL")