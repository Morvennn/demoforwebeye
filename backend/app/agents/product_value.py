"""Agent B — product value (docs/usability + practical value + OSS activity)."""
# Daniel Design

from typing import Any

from .base import ANCHORS, JSON_ONLY, BaseAgent


class ProductValueAgent(BaseAgent):
    name = "product_value"
    label = "产品价值"

    def system_prompt(self) -> str:
        return f"""你是【产品价值 Agent】（Agent B），负责从用户与开源治理侧评估一个 GitHub 仓库。

你将收到：README 全文、仓库元数据（Star / Fork / Issue 数、最近更新时间、License、是否有贡献指南）。

请从以下三个维度评分（0-100，严格遵循评分锚点），每项给出具体、有依据的点评：
1. docs_and_usability —— 文档与易用性。不仅看 README 写了什么，更要重点考察【能否快速上手】：是否有完整的 Quick Start / 安装步骤、API 或使用说明、可运行的示例代码；一个新人能否在 10 分钟内理解并跑起来。README 缺失则该项低分。
2. practical_value —— 实用价值与定位（是否解决真实问题、定位是否清晰、相对同类项目的差异化）。
3. oss_activity —— 开源活跃度与治理（更新频率、Star/Fork 量级、License 是否规范、是否有 CONTRIBUTING / 行为准则）。

{ANCHORS}

{JSON_ONLY}，结构如下：
{{
  "agent": "product_value",
  "dimensions": {{
    "docs_and_usability": {{"score": <0-100 整数>, "comment": "<具体点评>"}},
    "practical_value": {{"score": <0-100 整数>, "comment": "<具体点评>"}},
    "oss_activity": {{"score": <0-100 整数>, "comment": "<具体点评>"}}
  }},
  "findings": [{{"severity": "high|med|low", "point": "<问题点>"}}],
  "summary": "<产品/文档侧一句话总结>"
}}"""

    def user_prompt(self, context: dict[str, Any]) -> str:
        meta = context.get("meta_summary", {})
        readme: str | None = context.get("readme")

        meta_lines = "\n".join(f"- {k}: {v}" for k, v in meta.items()) or "（无元数据）"
        readme_block = readme[:8000] if readme else "（仓库没有 README）"
        if readme and len(readme) > 8000:
            readme_block += "\n...（README 已截断）"

        return f"""仓库：{context.get("repo_full", "(unknown)")}

【仓库元数据】
{meta_lines}

【README】
{readme_block}

请按 system 中的 JSON 结构输出你的产品价值评估结论。"""
