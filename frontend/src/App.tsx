// Daniel Design
import { useEffect, useRef } from "react";
import { RepoInput } from "./components/RepoInput";
import { MetaPanel } from "./components/MetaPanel";
import { AgentStream } from "./components/AgentStream";
import { FinalReportView } from "./components/FinalReport";
import { useAnalyze } from "./hooks/useAnalyze";

export default function App() {
  const a = useAnalyze();
  const loading = a.status === "loading";
  const judgeScrollRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (judgeScrollRef.current) judgeScrollRef.current.scrollTop = judgeScrollRef.current.scrollHeight;
  }, [a.judge.text]);

  const showJudge = (a.judge.running || !!a.judge.text) && !a.finalReport;

  return (
    <div className="app">
      <header className="hero">
        <h1>🩺 GitHub 仓库体检</h1>
        <p className="tagline">多 Agent 协作的 GitHub 仓库「体检」报告</p>
        <RepoInput onSubmit={a.run} disabled={loading} />
      </header>

      {a.error && <div className="error-banner">⚠️ {a.error}</div>}

      <main className="content">
        {a.meta && <MetaPanel meta={a.meta} />}

        {(a.meta || loading) && (
          <div className="agents-row">
            <AgentStream title="🧑‍💻 Agent A · 代码审计" accent="#60a5fa" agent={a.codeAudit} />
            <AgentStream title="📦 Agent B · 产品价值" accent="#f472b6" agent={a.productValue} />
          </div>
        )}

        {showJudge && (
          <div className="agent-stream card">
            <div className="agent-head" style={{ borderTopColor: "#a855f7" }}>
              <span className="agent-dot" style={{ background: "#a855f7" }} />
              <h3>🧑‍⚖️ Agent C · 总分裁判</h3>
              <span className={`agent-status ${a.judge.report ? "is-done" : "is-running"}`}>
                {a.judge.report ? "已完成" : "汇总中…"}
              </span>
            </div>
            <pre className="agent-text" ref={judgeScrollRef}>
              {a.judge.text}
              {a.judge.running && <span className="cursor">▋</span>}
            </pre>
          </div>
        )}

        {a.finalReport && <FinalReportView report={a.finalReport} />}
      </main>

      <footer className="footer">
        FastAPI + React + MiniMax 多 Agent 协作 · 仅分析公开仓库
      </footer>
    </div>
  );
}
