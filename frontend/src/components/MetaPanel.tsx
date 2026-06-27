// Daniel Design
import type { RepoMeta } from "../types";

function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}

export function MetaPanel({ meta }: { meta: RepoMeta }) {
  const topLangs = Object.entries(meta.languages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  const maxBytes = topLangs[0]?.[1] ?? 1;

  return (
    <div className="meta-panel card">
      <div className="meta-head">
        <a href={meta.url} target="_blank" rel="noreferrer" className="meta-repo">
          {meta.owner}/{meta.repo}
        </a>
        {meta.description && <div className="meta-desc">{meta.description}</div>}
      </div>

      <div className="meta-stats">
        <div className="stat"><span className="stat-num">⭐ {formatNumber(meta.stars)}</span><span className="stat-label">Star</span></div>
        <div className="stat"><span className="stat-num">🍴 {formatNumber(meta.forks)}</span><span className="stat-label">Fork</span></div>
        <div className="stat"><span className="stat-num">⚠️ {formatNumber(meta.open_issues)}</span><span className="stat-label">Open Issues</span></div>
        <div className="stat"><span className="stat-num">{meta.license || "未声明"}</span><span className="stat-label">License</span></div>
        <div className="stat"><span className="stat-num">{meta.has_contributing ? "有" : "无"}</span><span className="stat-label">贡献指南</span></div>
      </div>

      {topLangs.length > 0 && (
        <div className="lang-bars">
          {topLangs.map(([lang, bytes]) => (
            <div className="lang-row" key={lang}>
              <span className="lang-name">{lang}</span>
              <div className="lang-track">
                <div className="lang-fill" style={{ width: `${(bytes / maxBytes) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
