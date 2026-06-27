"""Agent C — judge: aggregates A+B with dynamic weighting into a final report."""
# Daniel Design

from typing import Any

from .base import ANCHORS, JSON_ONLY, BaseAgent


class JudgeAgent(BaseAgent):
    name = "judge"
    label = "总分裁判"

    def system_prompt(self) -> str:
        return f"""你是【总分裁判 Agent】（Agent C），负责汇总 Agent A（代码审计）与 Agent B（产品价值）的结论，生成最终体检报告。

【评分与权重规则】
1. 基础权重：代码侧 50% / 产品文档侧 50%。
   - “代码分”= Agent A 三个维度（structure / code_health_and_security / engineering）的算术平均。
   - “产品分”= Agent B 三个维度（docs_and_usability / practical_value / oss_activity）的算术平均。
   - final_score = round(代码分 * code权重 + 产品分 * product权重)。
2. 动态调权（关键能力）：如果你判断这是【纯资源整理型】仓库（如 Awesome 列表、curated resources、几乎不含业务代码逻辑）或【纯文档型】仓库，你可以自主把 product 权重上调到 0.8 甚至 1.0，并相应下调 code 权重。
   - 必须在 weighting 字段用一两句话写明调整理由（不调整也要说明用了基础 50/50）。
   - 必须在 applied_weights 给出实际使用的权重，形如 {{"code": 0.5, "product": 0.5}}，且两者之和为 1.0。
3. final_score 必须是 0-100 的整数，严格遵循评分锚点。
4. dimension_scores：把 A 与 B 共六个维度的分数原样汇总。
5. strengths：3-5 条亮点（简短、具体）。
6. recommendations：3-6 条【可执行】的优化建议，按优先级排序。
7. verdict：一句话总体结论（可含分数定级，如“优秀 / 及格”）。

{ANCHORS}

{JSON_ONLY}，结构如下：
{{
  "agent": "judge",
  "final_score": <0-100 整数>,
  "weighting": "<权重说明与调整理由>",
  "applied_weights": {{"code": <0-1>, "product": <0-1>}},
  "dimension_scores": {{
    "structure": <整数>, "code_health_and_security": <整数>, "engineering": <整数>,
    "docs_and_usability": <整数>, "practical_value": <整数>, "oss_activity": <整数>
  }},
  "strengths": ["<亮点1>", "..."],
  "recommendations": [{{"priority": "high|med|low", "suggestion": "<可执行建议>"}}],
  "verdict": "<一句话结论>"
}}"""

    def user_prompt(self, context: dict[str, Any]) -> str:
        import json as _json

        code_audit = context.get("code_audit", {})
        product_value = context.get("product_value", {})
        meta = context.get("meta_summary", {})

        meta_lines = "\n".join(f"- {k}: {v}" for k, v in meta.items()) or "（无元数据）"

        return f"""仓库：{context.get("repo_full", "(unknown)")}

【仓库元数据】
{meta_lines}

【Agent A 代码审计结论】
{_json.dumps(code_audit, ensure_ascii=False, indent=2)}

【Agent B 产品价值结论】
{_json.dumps(product_value, ensure_ascii=False, indent=2)}

请综合 A 与 B 的结论，按 system 中的规则与 JSON 结构输出最终体检报告。注意判断是否需要动态调权。"""
