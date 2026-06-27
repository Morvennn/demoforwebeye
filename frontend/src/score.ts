// Daniel Design
// Score band helper — same 0-100 anchors as the agent system prompts,
// used to color scores consistently across the UI.

export interface Band {
  key: "red" | "orange" | "green" | "highlight";
  label: string;
  color: string;
}

export function band(score: number): Band {
  if (score <= 50) return { key: "red", label: "不及格", color: "#ef4444" };
  if (score <= 75) return { key: "orange", label: "及格", color: "#f59e0b" };
  if (score <= 90) return { key: "green", label: "优秀", color: "#22c55e" };
  return { key: "highlight", label: "极品", color: "#a855f7" };
}

// Dimension key → Chinese display name.
export const DIM_LABELS: Record<string, string> = {
  structure: "目录结构",
  code_health_and_security: "代码健康与安全",
  engineering: "工程化",
  docs_and_usability: "文档与易用性",
  practical_value: "实用价值",
  oss_activity: "开源活跃度",
};
