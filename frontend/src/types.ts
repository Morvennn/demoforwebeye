// Daniel Design
// Types mirroring the backend SSE payloads (see backend/app/models.py).

export type AgentName = "code_audit" | "product_value" | "judge";
export type Severity = "high" | "med" | "low";

export interface DimensionScore {
  score: number;
  comment: string;
}

export interface Finding {
  severity: Severity;
  point: string;
}

export interface RepoMeta {
  owner: string;
  repo: string;
  url: string;
  description?: string | null;
  stars: number;
  forks: number;
  open_issues: number;
  default_branch: string;
  pushed_at?: string | null;
  license?: string | null;
  languages: Record<string, number>;
  has_contributing: boolean;
}

export interface AgentReport {
  agent: AgentName;
  dimensions: Record<string, DimensionScore>;
  findings: Finding[];
  summary: string;
}

export interface Recommendation {
  priority: Severity;
  suggestion: string;
}

export interface JudgeReport {
  agent: "judge";
  final_score: number;
  weighting: string;
  applied_weights: { code: number; product: number };
  dimension_scores: Record<string, number>;
  strengths: string[];
  recommendations: Recommendation[];
  verdict: string;
}

export interface FinalReport {
  meta: RepoMeta;
  code_audit: AgentReport;
  product_value: AgentReport;
  judge: JudgeReport;
}
