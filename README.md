# 🩺 GitHub 仓库体检

> 多 Agent 协作的 GitHub 仓库「体检」工具
> 输入一个公开的 GitHub 仓库 URL，三个 AI Agent 协作分析，实时流式输出一份 0-100 分的结构化体检报告。

## 它做什么

- 🧑‍💻 **Agent A · 代码审计**：评估目录结构、代码健康与安全（含硬编码秘钥/常见反模式的浅层扫描）、工程化程度。
- 📦 **Agent B · 产品价值**：评估文档与易用性（Quick Start / API 说明 / 示例代码）、实用价值、开源活跃度。
- 🧑‍⚖️ **Agent C · 总分裁判**：汇总 A 与 B，按动态权重生成 0-100 总分、亮点、可执行优化建议。
- ⚡ **流式体验**：后端各 Agent 的思考过程通过 SSE 实时推送到前端，边想边显示，无需全量等待。

三个 Agent 由 **MiniMax**（OpenAI 兼容 API）驱动，采用 **并行 A+B → C 汇总** 的拓扑。

## 技术栈

| | 技术 |
|---|---|
| 后端 | Python 3.11+ · FastAPI · httpx · openai SDK（指向 MiniMax）· pydantic |
| 前端 | Vite · React 18 · TypeScript |
| 通信 | SSE（`EventSource`，GET + query 参数）|
| 数据源 | GitHub REST API（纯 API，不 clone）|

## 架构

```
React SPA ──EventSource──► FastAPI ──► RepoFetcher (GitHub API)
                              │
                              ▼
                    AgentPipeline: gather(A, B) ──► C ──► 最终报告
                              │  全程 SSE 事件回流
                              ▼
                          MiniMax LLM
```

完整设计见 [`docs/superpowers/specs/2026-06-27-repo-health-design.md`](docs/superpowers/specs/2026-06-27-repo-health-design.md)。

## 先决条件

- **Python 3.11+**（开发基于 3.12）
- **Node.js 18+**（开发基于 24，自带 npm）
- 一个 **MiniMax API Key**（来自你的 MiniMax coding plan / 开放平台）
- _可选但强烈建议_：一个 **GitHub Personal Access Token**（经典 PAT，勾选 `public_repo`），把未认证的 60 次/小时提升到 5000 次/小时

## 本地运行

### 1) 配置后端

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Git Bash（PowerShell 用 .venv\Scripts\Activate.ps1）
pip install -r requirements.txt

cp .env.example .env                 # Windows cmd 用: copy .env.example .env
# 然后编辑 .env，填入 MINIMAX_API_KEY（必需）和 GITHUB_TOKEN（可选）
```

`.env` 关键项：

```ini
MINIMAX_API_KEY=你的MiniMax密钥
MINIMAX_BASE_URL=https://api.minimax.io/v1
MINIMAX_MODEL=MiniMax-M3
GITHUB_TOKEN=你的GitHub_PAT        # 可选，解除限流
CORS_ORIGIN=*                       # 部署时改成前端域名
```

启动后端：

```bash
uvicorn app.main:app --reload        # 监听 http://localhost:8000
```

### 2) 配置前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev                          # 监听 http://localhost:5173（自动代理 /api → 8000）
```

### 3) 使用

浏览器打开 **http://localhost:5173**，粘贴一个公开 GitHub 仓库 URL（如 `https://github.com/fastapi/fastapi`），点击「开始体检」，即可看到元数据卡片 → A/B 并行实时分析 → C 汇总 → 最终报告（含评分、亮点、建议，可导出 Markdown / JSON）。

> 评分锚点与配色：`0-50` 红·不及格 ｜ `51-75` 橙·及格 ｜ `76-90` 绿·优秀 ｜ `91-100` 高亮·极品。

## 测试

后端单元测试（URL 解析、JSON 修复、GitHub 抓取 mock、Agent 管道 mock LLM）：

```bash
cd backend
pytest -v
```

前端类型检查 / 构建：

```bash
cd frontend
npm run typecheck
npm run build
```

## 项目结构

```
webeye/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI + SSE 端点 + CORS
│   │   ├── config.py          # 环境变量
│   │   ├── models.py          # Pydantic schema
│   │   ├── github.py          # GitHub API 抓取 + URL 解析
│   │   ├── llm.py             # MiniMax 客户端 + JSON 修复
│   │   ├── pipeline.py        # 多 Agent 编排（并行 A+B → C）
│   │   └── agents/            # A / B / C 三个 Agent
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── hooks/useAnalyze.ts   # EventSource 接线
│   │   ├── components/           # 输入 / 元数据 / Agent流 / 最终报告
│   │   └── types.ts
│   └── vite.config.ts            # /api 代理
└── docs/
    ├── superpowers/specs/         # 设计文档
    └── vibe-coding.md             # Vibe Coding 关键 Prompt 凭证
```

## 关于限流

未配置 `GITHUB_TOKEN` 时，GitHub API 限流为 **60 次/小时/IP**（共享出口 IP 很容易耗尽）。若看到 `rate_limit` 错误，配置 token 即可。每次分析约消耗 4 + N 次 API 调用（N 为抓取的关键文件数）。

---

用 AI 辅助开发的 2 小时作品。过程 凭证见 [`docs/vibe-coding.md`](docs/vibe-coding.md)。
