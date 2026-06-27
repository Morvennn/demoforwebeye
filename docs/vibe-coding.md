# Vibe Coding 过程凭证

> 本文件记录使用 AI 编码工具（Claude Code）辅助开发本工具过程中，**塑造项目走向的关键提示词（Prompt）**，作为「过程凭证」提交。每个 Prompt 附带其带来的关键决策与产出。

开发方式：**对话式驱动（Vibe Coding）** —— 先用 `brainstorming` 技能与 AI 协作把需求打磨成设计稿（spec），获批后再分阶段实现。全程不写一行未经设计的代码。

完整设计文档见 [`superpowers/specs/2026-06-27-repo-health-design.md`](superpowers/specs/2026-06-27-repo-health-design.md)。

---

## Prompt 1 — 任务定义（起点）

> **任务：多 Agent 协作的 GitHub 仓库"体检"工具 ⏰ 2 小时**
> 用户输入一个公开的 GitHub 仓库 URL，系统通过多 Agent 协作对该仓库进行分析，并输出一份结构化的"体检报告"。
> 核心：前端输入框、后端 GitHub 数据获取、至少三个 Agent 的协作链路（代码审计 / 产品价值 / 总分裁判），加分项为流式传输。

**产出**：确立项目目标。AI 先按 brainstorming 流程**拒绝立即写代码**，转而逐个提问澄清需求，避免基于错误假设浪费工时。

---

## Prompt 2 — 一连串澄清选择（锁定技术骨架）

通过多轮「单选」问答一次性锁定五个基础决定（以下为关键问答浓缩）：

> Q 技术栈？→ **Python + FastAPI**
> Q LLM 供应商？→ **我有 MiniMax 的 coding plan**（AI 随即联网确认 MiniMax 是 OpenAI 兼容、base_url=`https://api.minimax.io/v1`，决定用 `openai` SDK 接入）
> Q Agent 编排？→ **手写 async 管道**
> Q 数据获取？→ **纯 GitHub API**（不 clone）
> Q Agent 拓扑？→ **并行 A+B → C 汇总**

**产出**：技术骨架定型——FastAPI + 手写 async 编排 + 纯 GitHub API + 并行拓扑。每一步都附带 AI 的推荐与权衡分析，而非默认接受。

---

## Prompt 3 — 重大架构调整

> **要拆前后端。**

**产出**：从「FastAPI 单工程托管静态页」改为**双工程**（`backend/` FastAPI + `frontend/` Vite+React+TS）。AI 由此追加一个澄清问题（前端栈）并修正一个技术细节：浏览器原生 `EventSource` 仅支持 GET，于是把接口从 `POST` 改为 `GET /api/analyze?repo_url=`，并加入 Vite 代理 + CORS 双重跨域方案。

---

## Prompt 4 — Agent 维度精修 + 动态调权 + 评分锚点（最关键的设计深化）

> 1. A 的 code_quality 扩展为 **code_health_and_security**（顺带扫描硬编码秘钥/常见反模式/浅层安全风险）；B 的 readme_clarity 升级为 **docs_and_usability**（重点考察 Quick Start / API 说明 / 示例代码）。
> 2. C 引入**动态调权**：基础 50/50，但若是 Awesome 列表 / 纯文档型仓库，可自主将产品文档权重上调到 80% 甚至 100%，并在 weighting 字段给出理由。
> 3. 统一 0-100 评分锚点写入 System Prompt：0-50 红 / 51-75 橙 / 76-90 绿 / 91-100 高亮。

**产出**：三个 Agent 的角色与评分体系最终定型。动态调权让工具对「非典型代码仓库」也能公平打分；统一锚点既约束了模型打分尺度，又直接驱动前端配色，前后端契约一致。

---

## Prompt 5 — 环境障碍的处理

> **winget 装 Python（推荐）**

**产出**：本机未安装 Python（后端必需）。AI 探测到 `winget` 可用后，经用户确认一键 `winget install Python.Python.3.12` 装好 Python 3.12.10，保持原 FastAPI 设计不动，避免改栈返工。

---

## 实现阶段的关键内部 Prompt（节选）

设计获批后进入实现，AI 对自身下达的关键实现级指令（节选）：

- 「后台启动 venv + 依赖安装，同时继续写后端源码」——并行化等待，缩短耗时。
- 「先做导入冒烟测试，及早发现语法/循环依赖」——在写完一个模块层后立即 `import` 验证。
- 「后端用 respx mock GitHub API、用 FakeLLM mock MiniMax，跑通 25 个单测」——在不消耗真实 API 额度/费用的前提下验证核心逻辑。
- 「启动 uvicorn + Vite，curl 验证 health / 400 / SSE 事件流 / 代理」——端到端联通性验证。

---

## 小结

整个 2 小时作品的形态、架构、Agent 设计、评分体系，几乎全部由上述 5 条用户 Prompt 串联塑造。AI 的角色是：**强制先设计后实现、提供带权衡的选项、联网核验技术事实（MiniMax API）、并在实现阶段持续自我验证**。
