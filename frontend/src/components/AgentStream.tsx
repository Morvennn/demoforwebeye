// Daniel Design
import { useEffect, useRef } from "react";
import type { AgentState } from "../hooks/useAnalyze";
import { band, DIM_LABELS } from "../score";

interface Props {
  title: string;
  accent: string;
  agent: AgentState;
}

export function AgentStream({ title, accent, agent }: Props) {
  const scrollRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [agent.text]);

  const dims = agent.report ? Object.entries(agent.report.dimensions) : [];

  return (
    <div className="agent-stream card">
      <div className="agent-head" style={{ borderTopColor: accent }}>
        <span className="agent-dot" style={{ background: accent }} />
        <h3>{title}</h3>
        <span className={`agent-status ${agent.report ? "is-done" : agent.running ? "is-running" : "is-pending"}`}>
          {agent.report ? "已完成" : agent.running ? "分析中…" : "等待中"}
        </span>
      </div>

      {(agent.text || agent.running) && !agent.report && (
        <pre className="agent-text" ref={scrollRef}>
          {agent.text}
          {agent.running && !agent.report && <span className="cursor">▋</span>}
        </pre>
      )}

      {agent.report && (
        <div className="agent-result">
          {dims.map(([key, d]) => {
            const b = band(d.score);
            return (
              <div className="dim-row" key={key}>
                <div className="dim-top">
                  <span className="dim-label">{DIM_LABELS[key] ?? key}</span>
                  <span className="dim-score" style={{ color: b.color }}>
                    {d.score} <small>· {b.label}</small>
                  </span>
                </div>
                <div className="dim-bar">
                  <div className="dim-fill" style={{ width: `${d.score}%`, background: b.color }} />
                </div>
                <div className="dim-comment">{d.comment}</div>
              </div>
            );
          })}

          {agent.report.findings.length > 0 && (
            <ul className="findings">
              {agent.report.findings.map((f, i) => (
                <li key={i} className={`finding sev-${f.severity}`}>
                  <span className="sev-tag">{f.severity}</span>
                  {f.point}
                </li>
              ))}
            </ul>
          )}

          <div className="agent-summary">{agent.report.summary}</div>
        </div>
      )}
    </div>
  );
}
