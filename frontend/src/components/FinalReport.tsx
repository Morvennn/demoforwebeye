// Daniel Design
import type { FinalReport } from "../types";
import { band, DIM_LABELS } from "../score";

function download(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function toMarkdown(r: FinalReport): string {
  const j = r.judge;
  const lines: string[] = [];
  lines.push(`# ${r.meta.owner}/${r.meta.repo} 体检报告`);
  lines.push("");
  lines.push(`**总分：${j.final_score} / 100**  —  ${j.verdict}`);
  lines.push("");
  lines.push(`> 权重：${j.weighting}（code=${j.applied_weights.code}，product=${j.applied_weights.product}）`);
  lines.push("");
  lines.push("## 分项评分");
  for (const [k, v] of Object.entries(j.dimension_scores)) {
    lines.push(`- ${DIM_LABELS[k] ?? k}：**${v}**`);
  }
  lines.push("");
  lines.push("## 亮点");
  j.strengths.forEach((s) => lines.push(`- ${s}`));
  lines.push("");
  lines.push("## 优化建议");
  j.recommendations.forEach((r2) => lines.push(`- [${r2.priority}] ${r2.suggestion}`));
  lines.push("");
  lines.push("## Agent 结论");
  lines.push(`- 代码审计：${r.code_audit.summary}`);
  lines.push(`- 产品价值：${r.product_value.summary}`);
  return lines.join("\n");
}

export function FinalReportView({ report }: { report: FinalReport }) {
  const j = report.judge;
  const b = band(j.final_score);

  return (
    <div className="final-report card">
      <div className="final-score-wrap" style={{ borderColor: b.color }}>
        <div className="final-score" style={{ color: b.color }}>
          {j.final_score}
          <small>/100</small>
        </div>
        <div className="final-band" style={{ background: b.color }}>{b.label}</div>
        <div className="final-verdict">{j.verdict}</div>
      </div>

      <div className="weighting">⚖️ {j.weighting}</div>

      <div className="dim-grid">
        {Object.entries(j.dimension_scores).map(([k, v]) => {
          const bb = band(v);
          return (
            <div className="dim-card" key={k}>
              <div className="dim-card-score" style={{ color: bb.color }}>{v}</div>
              <div className="dim-card-label">{DIM_LABELS[k] ?? k}</div>
            </div>
          );
        })}
      </div>

      <div className="final-cols">
        <div className="final-col">
          <h4>✨ 亮点</h4>
          <ul>{j.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
        </div>
        <div className="final-col">
          <h4>🛠 优化建议</h4>
          <ul className="recs">
            {j.recommendations.map((r2, i) => (
              <li key={i} className={`sev-${r2.priority}`}>
                <span className="sev-tag">{r2.priority}</span>
                {r2.suggestion}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="export-row">
        <button onClick={() => download(`${report.meta.repo}-report.md`, toMarkdown(report), "text/markdown")}>
          ⬇ 导出 Markdown
        </button>
        <button onClick={() => download(`${report.meta.repo}-report.json`, JSON.stringify(report, null, 2), "application/json")}>
          ⬇ 导出 JSON
        </button>
      </div>
    </div>
  );
}
