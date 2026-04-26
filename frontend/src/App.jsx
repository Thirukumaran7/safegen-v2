import { useState, useEffect, useRef } from "react";
import Header      from "./components/Header";
import StatBar     from "./components/StatBar";
import InputPanel  from "./components/InputPanel";
import ResultPanel from "./components/ResultPanel";
import Dashboard   from "./components/Dashboard";
import Compare     from "./components/Compare";
import { analyzeText, sendFeedback, fetchHealth } from "./utils/api";

export default function App() {
  const [view,    setView]    = useState("analyze");
  const [text,    setText]    = useState("");
  const [policy,  setPolicy]  = useState("moderate");
  const [role,    setRole]    = useState("general");
  const [useRag,  setUseRag]  = useState(true);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");
  const [history, setHistory] = useState([]);
  const [live,    setLive]    = useState(false);
  const [dark,    setDark]    = useState(true);
  const resultRef = useRef(null);

  // Theme toggle
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, [dark]);

  // Startup health check only
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", "dark");
    fetchHealth().then(() => setLive(true)).catch(() => setLive(false));
  }, []);

  const analyze = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await analyzeText(text, policy, role, useRag);
      setResult(res.data);
      setHistory(prev => [res.data, ...prev].slice(0, 15));
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (e) {
      setError("Backend error: " + (e.response?.data?.detail || e.message));
    } finally {
      setLoading(false);
    }
  };

  const handleResult = (r) => {
    if (r) {
      setResult(r);
      setHistory(prev => [r, ...prev].slice(0, 15));
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } else {
      setResult(null);
    }
  };

  return (
    <div style={{ minHeight:"100vh", background:"var(--bg)", color:"var(--text)", transition:"background 0.3s, color 0.3s" }}>
      <Header view={view} setView={setView} live={live} dark={dark} setDark={setDark} />

      {view === "analyze" && (
        <div style={{ padding:16, maxWidth:1400, margin:"0 auto" }}>
          <StatBar sessionCount={history.length} />
          <div className="main-grid" style={{ display:"grid", gridTemplateColumns:"360px 1fr", gap:16 }}>
            <InputPanel
              text={text} setText={setText}
              policy={policy} setPolicy={setPolicy}
              role={role} setRole={setRole}
              useRag={useRag} setUseRag={setUseRag}
              onAnalyze={analyze} loading={loading}
              history={history}
              onResult={handleResult}
              onError={setError}
            />
            <div ref={resultRef}>
              {error && (
                <div style={{ padding:12, background:"#ef444422", border:"1px solid #ef444440", borderRadius:8, fontSize:13, color:"#ef4444", marginBottom:14 }}>
                  {error}
                </div>
              )}
              <ResultPanel
                result={result}
                loading={loading}
                onFeedback={async(id, a) => { await sendFeedback(id, a); }}
              />
            </div>
          </div>
        </div>
      )}

      {view === "compare"   && <Compare />}
      {view === "dashboard" && <Dashboard />}
    </div>
  );
}