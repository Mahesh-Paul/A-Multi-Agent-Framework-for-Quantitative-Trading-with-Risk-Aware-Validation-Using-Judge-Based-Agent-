import React, { useEffect, useState } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const API = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const colors = {
  BUY: "#22c55e",
  HOLD: "#f59e0b",
  SELL: "#ef4444",
  APPROVED: "#22c55e",
  REJECTED: "#ef4444",
  REDUCED: "#f59e0b",
  Excellent: "#22c55e",
  Good: "#38bdf8",
  Average: "#f59e0b",
  Poor: "#ef4444"
};

function App() {
  const [signals, setSignals] = useState([]);
  const [backtest, setBacktest] = useState([]);
  const [risk, setRisk] = useState([]);
  const [judgeEvals, setJudgeEvals] = useState([]);
  const [mode, setMode] = useState(null);
  const [ticker, setTicker] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`${API}/signals`).then(res => setSignals(res.data)).catch(() => {});
    axios.get(`${API}/backtest`).then(res => setBacktest(res.data)).catch(() => {});
    axios.get(`${API}/risk`).then(res => setRisk(res.data)).catch(() => {});
    axios.get(`${API}/judge/evaluations`).then(res => setJudgeEvals(res.data)).catch(() => {});
  }, []);

  const safeText = (text) => {
    if (!text) return "";
    if (typeof text === "object") return JSON.stringify(text);
    return String(text);
  };

  const getAction = (text) => {
    const t = safeText(text);
    if (!t) return "N/A";
    const match = t.match(/Final Action:\s*(BUY|SELL|HOLD)/);
    return match ? match[1] : "N/A";
  };

  const getDecision = (text) => {
    const t = safeText(text);
    if (!t) return "N/A";
    const match = t.match(/Decision:\s*(APPROVED|REJECTED|REDUCED)/);
    return match ? match[1] : "N/A";
  };

  const getSignal = (text) => {
    const t = safeText(text);
    if (!t) return "N/A";
    const match = t.match(/\*{0,2}Signal\*{0,2}[:\s*]+<?\s*(BUY|SELL|HOLD)/i);
    if (match) return match[1].toUpperCase();
    if (/\bBUY\b/i.test(t)) return "BUY";
    if (/\bSELL\b/i.test(t)) return "SELL";
    if (/\bHOLD\b/i.test(t)) return "HOLD";
    return "N/A";
  };

  const getVerdict = (text) => {
    const t = safeText(text);
    if (!t) return "N/A";
    const match = t.match(/\*{0,2}Verdict\*{0,2}[:\s*]+<?\s*(STRONG BUY|BUY|HOLD|AVOID|APPROVED|REDUCED|REJECTED)/i);
    if (match) return match[1].toUpperCase();
    if (/STRONG BUY/i.test(t)) return "STRONG BUY";
    if (/\bBUY\b/i.test(t)) return "BUY";
    if (/\bAVOID\b/i.test(t)) return "AVOID";
    if (/\bHOLD\b/i.test(t)) return "HOLD";
    return "N/A";
  };

  const analyze = async () => {
    if (!ticker || !mode) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await axios.get(`${API}/analyze/${mode}/${ticker.toUpperCase()}`);
      setResult(res.data);
    } catch (e) {
      setError("Error fetching analysis. Check ticker and try again.");
    }
    setLoading(false);
  };

  const parseAnalysis = (text) => {
    const t = safeText(text);
    if (!t) return [];
    return t.split("\n").filter(line => line.trim() !== "");
  };

  return (
    <div style={{ backgroundColor: "#0f172a", minHeight: "100vh", color: "white", padding: "30px", fontFamily: "system-ui, -apple-system, sans-serif" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", marginBottom: "30px" }}>
        <div>
          <h1 style={{ color: "#38bdf8", marginBottom: "5px", fontSize: "28px", fontWeight: "800" }}>🚀 Hermes Trading Dashboard</h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "15px" }}>
            Adaptive Quant Signal Generation Engine & Multi-Agent Consensus System
          </p>
        </div>
      </div>

      {/* Interactive Stock Analysis Section */}
      <h2 style={{ color: "#38bdf8", marginBottom: "15px" }}>🔍 Analyze Any Stock</h2>
      <div style={{ display: "flex", gap: "12px", marginBottom: "20px", flexWrap: "wrap" }}>
        <button onClick={() => setMode("investing")} style={{ padding: "12px 24px", borderRadius: "10px", border: `2px solid ${mode === "investing" ? "#22c55e" : "#334155"}`, backgroundColor: mode === "investing" ? "#14532d" : "#1e293b", color: mode === "investing" ? "#22c55e" : "#94a3b8", cursor: "pointer", fontSize: "15px", fontWeight: "bold" }}>
          📈 Investing Mode
        </button>
        <button onClick={() => setMode("trading")} style={{ padding: "12px 24px", borderRadius: "10px", border: `2px solid ${mode === "trading" ? "#38bdf8" : "#334155"}`, backgroundColor: mode === "trading" ? "#0c2a3d" : "#1e293b", color: mode === "trading" ? "#38bdf8" : "#94a3b8", cursor: "pointer", fontSize: "15px", fontWeight: "bold" }}>
          ⚡ Trading Mode
        </button>
      </div>

      {mode && (
        <div style={{ display: "flex", gap: "10px", marginBottom: "30px", flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="Enter ticker (e.g. AAPL, TSLA, NVDA, GOOGL)"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === "Enter" && analyze()}
            style={{ padding: "12px 20px", borderRadius: "10px", border: "1px solid #334155", backgroundColor: "#1e293b", color: "white", fontSize: "16px", width: "350px" }}
          />
          <button onClick={analyze} style={{ padding: "12px 30px", borderRadius: "10px", border: "none", backgroundColor: "#38bdf8", color: "#0f172a", cursor: "pointer", fontSize: "16px", fontWeight: "bold" }}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      )}

      {error && <p style={{ color: "#ef4444", marginBottom: "20px" }}>{error}</p>}

      {/* Analysis Result Display */}
      {result && (
        <div style={{ backgroundColor: "#1e293b", borderRadius: "14px", padding: "25px", marginBottom: "40px", border: "1px solid #334155", boxShadow: "0 8px 20px rgba(0,0,0,0.3)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
            <h2 style={{ color: "#38bdf8", margin: 0 }}>
              {result.mode === "trading" ? "⚡" : "📈"} {result.ticker} — {result.mode === "trading" ? "Trading" : "Investing"} Analysis
            </h2>
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              {result.judge && (
                <div style={{
                  padding: "8px 16px", borderRadius: "8px",
                  backgroundColor: (colors[result.judge.verdict] || "#94a3b8") + "22",
                  border: `2px solid ${colors[result.judge.verdict] || "#94a3b8"}`,
                  color: colors[result.judge.verdict] || "#94a3b8",
                  fontWeight: "bold", fontSize: "15px"
                }}>
                  ⚖️ Judge: {result.judge.verdict} ({result.judge.s_final}/10)
                </div>
              )}
              <div style={{
                padding: "8px 20px", borderRadius: "8px",
                backgroundColor: result.mode === "trading" ? (colors[getSignal(result.analysis)] || "#94a3b8") + "22" : (colors[getVerdict(result.analysis)?.includes("BUY") ? "BUY" : getVerdict(result.analysis) === "AVOID" ? "SELL" : "HOLD"] || "#94a3b8") + "22",
                border: `2px solid ${result.mode === "trading" ? (colors[getSignal(result.analysis)] || "#94a3b8") : (colors[getVerdict(result.analysis)?.includes("BUY") ? "BUY" : getVerdict(result.analysis) === "AVOID" ? "SELL" : "HOLD"] || "#94a3b8")}`,
                color: result.mode === "trading" ? (colors[getSignal(result.analysis)] || "#94a3b8") : (colors[getVerdict(result.analysis)?.includes("BUY") ? "BUY" : getVerdict(result.analysis) === "AVOID" ? "SELL" : "HOLD"] || "#94a3b8"),
                fontWeight: "bold", fontSize: "16px"
              }}>
                Signal: {result.mode === "trading" ? getSignal(result.analysis) : getVerdict(result.analysis)}
              </div>
            </div>
          </div>

          {/* Embedded AI Judge Novelty Audit within the Analysis */}
          {result.judge && (
            <div style={{
              backgroundColor: "#0b1329",
              border: "1px solid rgba(168, 85, 247, 0.4)",
              borderRadius: "10px",
              padding: "16px 20px",
              marginBottom: "20px"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "18px" }}>⚖️</span>
                  <span style={{ color: "#c084fc", fontWeight: "bold", fontSize: "15px" }}>AI Judge Audit</span>
                  <span style={{ color: "#94a3b8", fontSize: "12px", fontFamily: "monospace" }}>[S_final = 0.40·Risk + 0.30·Acc + 0.15·Reas + 0.15·Over]</span>
                </div>
                <div style={{ color: "#38bdf8", fontWeight: "bold", fontSize: "16px", fontFamily: "monospace" }}>
                  S_final: {result.judge.s_final}/10 ({result.judge.s_final_pct}%) • {result.judge.rating}
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", marginBottom: "12px" }}>
                <div style={{ backgroundColor: "#0f172a", borderRadius: "6px", padding: "8px 12px", borderLeft: "3px solid #22c55e" }}>
                  <div style={{ color: "#94a3b8", fontSize: "11px" }}>🛡️ Risk (40%)</div>
                  <div style={{ color: "#22c55e", fontSize: "15px", fontWeight: "bold" }}>{result.judge.s_risk}/10</div>
                </div>
                <div style={{ backgroundColor: "#0f172a", borderRadius: "6px", padding: "8px 12px", borderLeft: "3px solid #38bdf8" }}>
                  <div style={{ color: "#94a3b8", fontSize: "11px" }}>🎯 Accuracy (30%)</div>
                  <div style={{ color: "#38bdf8", fontSize: "15px", fontWeight: "bold" }}>{result.judge.s_accuracy}/10</div>
                </div>
                <div style={{ backgroundColor: "#0f172a", borderRadius: "6px", padding: "8px 12px", borderLeft: "3px solid #f59e0b" }}>
                  <div style={{ color: "#94a3b8", fontSize: "11px" }}>🧠 Reasoning (15%)</div>
                  <div style={{ color: "#f59e0b", fontSize: "15px", fontWeight: "bold" }}>{result.judge.s_reasoning}/10</div>
                </div>
                <div style={{ backgroundColor: "#0f172a", borderRadius: "6px", padding: "8px 12px", borderLeft: "3px solid #a855f7" }}>
                  <div style={{ color: "#94a3b8", fontSize: "11px" }}>🌐 Conviction (15%)</div>
                  <div style={{ color: "#a855f7", fontSize: "15px", fontWeight: "bold" }}>{result.judge.s_overall}/10</div>
                </div>
              </div>

              {result.judge.executive_summary && (
                <div style={{ color: "#cbd5e1", fontSize: "12px", lineHeight: "1.4" }}>
                  <strong>Judge Summary:</strong> {result.judge.executive_summary}
                </div>
              )}
            </div>
          )}



          {result.mode === "trading" && (
            <div style={{ display: "flex", gap: "15px", marginBottom: "20px", flexWrap: "wrap" }}>
              <div style={{ backgroundColor: "#0f172a", borderRadius: "8px", padding: "12px 20px", textAlign: "center" }}>
                <div style={{ color: "#94a3b8", fontSize: "12px" }}>Current Price</div>
                <div style={{ color: "white", fontSize: "20px", fontWeight: "bold" }}>${result.current_price?.toFixed(2)}</div>
              </div>
              <div style={{ backgroundColor: "#0f172a", borderRadius: "8px", padding: "12px 20px", textAlign: "center" }}>
                <div style={{ color: "#94a3b8", fontSize: "12px" }}>RSI (14)</div>
                <div style={{ color: result.rsi > 70 ? "#ef4444" : result.rsi < 30 ? "#22c55e" : "white", fontSize: "20px", fontWeight: "bold" }}>{result.rsi?.toFixed(2)}</div>
              </div>
              <div style={{ backgroundColor: "#0f172a", borderRadius: "8px", padding: "12px 20px", textAlign: "center" }}>
                <div style={{ color: "#94a3b8", fontSize: "12px" }}>MACD</div>
                <div style={{ color: result.macd > 0 ? "#22c55e" : "#ef4444", fontSize: "20px", fontWeight: "bold" }}>{result.macd?.toFixed(4)}</div>
              </div>
              {result.supertrend && (
                <div style={{ backgroundColor: "#0f172a", borderRadius: "8px", padding: "12px 20px", textAlign: "center" }}>
                  <div style={{ color: "#94a3b8", fontSize: "12px" }}>Supertrend</div>
                  <div style={{ color: result.supertrend === "BULLISH" ? "#22c55e" : "#ef4444", fontSize: "20px", fontWeight: "bold" }}>{result.supertrend}</div>
                </div>
              )}
            </div>
          )}

          {result.analysis && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {parseAnalysis(result.analysis).map((line, i) => (
                <div key={i} style={{ padding: "10px 15px", backgroundColor: "#0f172a", borderRadius: "8px", borderLeft: "3px solid #38bdf8", color: "#e2e8f0", fontSize: "14px" }}>
                  {line}
                </div>
              ))}
            </div>
          )}

          {result.mode === "investing" && result.news && (
            <div style={{ marginTop: "20px" }}>
              <h3 style={{ color: "#38bdf8" }}>📰 Recent News</h3>
              {safeText(result.news).split("\n").filter(n => n.trim()).map((n, i) => (
                <div key={i} style={{ padding: "10px 15px", backgroundColor: "#0f172a", borderRadius: "8px", marginBottom: "8px", color: "#94a3b8", fontSize: "13px" }}>{n}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* AI Judge Multi-Stock Evaluation Cards */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px", flexWrap: "wrap", gap: "10px" }}>
        <h2 style={{ color: "#c084fc", margin: 0 }}>
          ⚖️ AI Judge Agent — Weighted Decision Results
        </h2>
        <span style={{ color: "#94a3b8", fontSize: "13px" }}>
          Empirically evaluated against 7-day realized market movement
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px", marginBottom: "40px" }}>
        {judgeEvals.map((j, i) => {
          const sRisk = Number(j.s_risk || 0);
          const sAcc = Number(j.s_accuracy || 0);
          const sReas = Number(j.s_reasoning || 0);
          const sOver = Number(j.s_overall || 0);
          const sFinal = Number(j.s_final || 0);
          const verdict = j.verdict || "APPROVED";
          const rating = j.rating || "Good";
          const action = j.predicted_action || "BUY";

          return (
            <div key={i} style={{
              backgroundColor: "#1e293b",
              borderRadius: "14px",
              padding: "22px",
              border: `2px solid ${verdict === "APPROVED" ? "#22c55e" : verdict === "REDUCED" ? "#f59e0b" : "#ef4444"}`,
              boxShadow: "0 4px 15px rgba(0,0,0,0.3)"
            }}>
              {/* Card Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                <div>
                  <span style={{ fontSize: "24px", fontWeight: "900", color: "white" }}>{j.ticker}</span>
                  <span style={{ marginLeft: "10px", fontSize: "14px", color: colors[action] || "#38bdf8", fontWeight: "bold" }}>
                    Action: {action}
                  </span>
                </div>
                <div style={{ display: "flex", gap: "6px" }}>
                  <span style={{
                    backgroundColor: (colors[verdict] || "#94a3b8") + "22",
                    border: `1px solid ${colors[verdict] || "#94a3b8"}`,
                    color: colors[verdict] || "#94a3b8",
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: "bold"
                  }}>
                    {verdict}
                  </span>
                  <span style={{
                    backgroundColor: (colors[rating] || "#94a3b8") + "22",
                    border: `1px solid ${colors[rating] || "#94a3b8"}`,
                    color: colors[rating] || "#94a3b8",
                    padding: "4px 10px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: "bold"
                  }}>
                    {rating}
                  </span>
                </div>
              </div>

              {/* S_final Outcome Score */}
              <div style={{
                backgroundColor: "#0f172a",
                borderRadius: "10px",
                padding: "12px 16px",
                marginBottom: "16px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center"
              }}>
                <div>
                  <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "bold", textTransform: "uppercase" }}>Predicted Outcome Score</div>
                  <div style={{ color: "#38bdf8", fontSize: "22px", fontWeight: "bold", fontFamily: "monospace" }}>
                    S_final = {sFinal.toFixed(2)} <span style={{ fontSize: "14px", color: "#94a3b8" }}>/ 10</span>
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "bold" }}>CALIBRATED ACCURACY</div>
                  <div style={{ color: colors[verdict] || "white", fontSize: "20px", fontWeight: "bold" }}>
                    {(sFinal * 10).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* 4 Dimensions Breakdown */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "16px" }}>
                {/* S_risk */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "3px" }}>
                    <span style={{ color: "#22c55e", fontWeight: "bold" }}>🛡️ Risk Adherence (40%)</span>
                    <span style={{ color: "#cbd5e1" }}>{sRisk.toFixed(1)}/10 → +{(sRisk * 0.40).toFixed(2)} pts</span>
                  </div>
                  <div style={{ height: "6px", backgroundColor: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${sRisk * 10}%`, height: "100%", backgroundColor: "#22c55e", borderRadius: "3px" }} />
                  </div>
                </div>

                {/* S_accuracy */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "3px" }}>
                    <span style={{ color: "#38bdf8", fontWeight: "bold" }}>🎯 Market Accuracy (30%)</span>
                    <span style={{ color: "#cbd5e1" }}>{sAcc.toFixed(1)}/10 → +{(sAcc * 0.30).toFixed(2)} pts</span>
                  </div>
                  <div style={{ height: "6px", backgroundColor: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${sAcc * 10}%`, height: "100%", backgroundColor: "#38bdf8", borderRadius: "3px" }} />
                  </div>
                </div>

                {/* S_reasoning */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "3px" }}>
                    <span style={{ color: "#f59e0b", fontWeight: "bold" }}>🧠 Causal Reasoning (15%)</span>
                    <span style={{ color: "#cbd5e1" }}>{sReas.toFixed(1)}/10 → +{(sReas * 0.15).toFixed(2)} pts</span>
                  </div>
                  <div style={{ height: "6px", backgroundColor: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${sReas * 10}%`, height: "100%", backgroundColor: "#f59e0b", borderRadius: "3px" }} />
                  </div>
                </div>

                {/* S_overall */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "3px" }}>
                    <span style={{ color: "#a855f7", fontWeight: "bold" }}>🌐 Conviction & Regime (15%)</span>
                    <span style={{ color: "#cbd5e1" }}>{sOver.toFixed(1)}/10 → +{(sOver * 0.15).toFixed(2)} pts</span>
                  </div>
                  <div style={{ height: "6px", backgroundColor: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                    <div style={{ width: `${sOver * 10}%`, height: "100%", backgroundColor: "#a855f7", borderRadius: "3px" }} />
                  </div>
                </div>
              </div>

              {/* Realized Market Context & Executive Summary */}
              {j.actual_movement && (
                <div style={{ color: "#94a3b8", fontSize: "11px", marginBottom: "8px" }}>
                  <strong>Ground Truth Movement:</strong> {j.actual_movement}
                </div>
              )}
              {j.executive_summary && (
                <div style={{
                  fontSize: "12px",
                  color: "#cbd5e1",
                  backgroundColor: "#0f172a",
                  padding: "10px",
                  borderRadius: "6px",
                  lineHeight: "1.4"
                }}>
                  {j.executive_summary}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Final Trading Signals */}
      <h2 style={{ color: "#38bdf8" }}>📊 Final Trading Signals</h2>
      <div style={{ display: "flex", gap: "15px", flexWrap: "wrap", marginBottom: "40px" }}>
        {signals.map((s, i) => {
          const action = getAction(s.final_decision);
          return (
            <div key={i} style={{ backgroundColor: "#1e293b", borderRadius: "12px", padding: "20px", minWidth: "160px", textAlign: "center", border: `2px solid ${colors[action] || "#334155"}` }}>
              <div style={{ fontSize: "22px", fontWeight: "bold" }}>{s.ticker}</div>
              <div style={{ fontSize: "18px", color: colors[action] || "white", marginTop: "8px" }}>{action}</div>
            </div>
          );
        })}
      </div>

      {/* Backtest Performance */}
      <h2 style={{ color: "#38bdf8" }}>📈 Backtest Performance (Total Return %)</h2>
      <div style={{ backgroundColor: "#1e293b", borderRadius: "12px", padding: "20px", marginBottom: "40px" }}>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={backtest}>
            <XAxis dataKey="ticker" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
            <Tooltip formatter={v => `${(v * 100).toFixed(2)}%`} />
            <Bar dataKey="total_return" radius={[6, 6, 0, 0]}>
              {backtest.map((entry, i) => (
                <Cell key={i} fill={entry.total_return > 0 ? "#22c55e" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Assessment */}
      <h2 style={{ color: "#38bdf8" }}>🛡️ Risk Assessment</h2>
      <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
        {risk.map((r, i) => {
          const decision = getDecision(r.risk_assessment);
          return (
            <div key={i} style={{ backgroundColor: "#1e293b", borderRadius: "12px", padding: "20px", minWidth: "160px", textAlign: "center", border: `2px solid ${colors[decision] || "#334155"}` }}>
              <div style={{ fontSize: "22px", fontWeight: "bold" }}>{r.ticker}</div>
              <div style={{ fontSize: "16px", color: colors[decision] || "white", marginTop: "8px" }}>{decision}</div>
            </div>
          );
        })}
      </div>

    </div>
  );
}

export default App;