"""Agent A — code audit (technical side, incl. shallow security scan)."""
# Daniel Design

from typing import Any

from .base import ANCHORS, JSON_ONLY, BaseAgent

_MAX_TREE_LINES = 200


class CodeAuditAgent(BaseAgent):
    name = "code_audit"
    label = "代码审计"

    def system_prompt(self) -> str:
        return f"""你是【代码审计 Agent】（Agent A），负责从技术侧评估一个 GitHub 仓库的工程质量。

你将收到：仓库文件树、若干关键文件内容、语言分布。

请从以下三个维度评分（0-100，严格遵循评分锚点），每项给出具体、有依据的点评：
1. structure —— 目录结构与约定清晰度（分层是否合理、命名规范、模块边界是否清晰、是否遵循该语言的社区惯例）。
2. code_health_and_security —— 代码健康与安全性。除可读性、复杂度、重复度外，务必顺带扫描明显的【浅层安全风险】并写入 findings（severity 用 high/med/low）：
   - 硬编码的密钥 / Token / 密码 / 连接串
   - SQL 拼接、命令注入、不安全的反序列化、SSRF 风险
   - 常见反模式：吞掉异常、裸 except、全局可变状态、未校验的外部输入、明文存储敏感信息
3. engineering —— 工程化程度（是否有测试目录 / CI 配置 / lint / format / 依赖锁定文件 / 清晰的依赖声明）。

{ANCHORS}

{JSON_ONLY}，结构如下：
{{
  "agent": "code_audit",
  "dimensions": {{
    "structure": {{"score": <0-100 整数>, "comment": "<具体点评>"}},
    "code_health_and_security": {{"score": <0-100 整数>, "comment": "<具体点评，含安全发现>"}},
    "engineering": {{"score": <0-100 整数>, "comment": "<具体点评>"}}
  }},
  "findings": [{{"severity": "high|med|low", "point": "<问题点>"}}],
  "summary": "<技术侧一句话总结>"
}}"""

    def user_prompt(self, context: dict[str, Any]) -> str:
        tree: list[str] = context.get("tree", [])
        key_files: dict[str, str] = context.get("key_files", {})
        languages: dict[str, int] = context.get("languages", {})

        tree_display = "\n".join(tree[:_MAX_TREE_LINES])
        if len(tree) > _MAX_TREE_LINES:
            tree_display += f"\n...（共 {len(tree)} 个文件，已截断展示）"

        lang_display = ", ".join(f"{k}: {v}" for k, v in languages.items()) or "（无语言统计）"

        files_block = "\n\n".join(
            f"### 文件：{path}\n```\n{content}\n```" for path, content in key_files.items()
        ) or "（未抓取到关键文件）"

        return f"""仓库：{context.get("repo_full", "(unknown)")}

【语言分布】
{lang_display}

【文件树】
{tree_display}

【关键文件内容（已抽样/截断）】
{files_block}

请按 system 中的 JSON 结构输出你的代码审计结论。"""
