# 📚 LangChain RAG 企业级知识库问答系统

基于 LangChain 框架开发的 RAG（检索增强生成）知识库问答系统，面向电商平台商品知识库场景。支持多格式文档上传、自动向量化、多轮对话问答。

> **注**：RAG（Retrieval-Augmented Generation，检索增强生成）是一种让 AI 先"查资料"再回答的技术。它先从知识库中检索与用户问题相关的内容，然后把这些内容作为参考信息交给大模型，让大模型基于真实资料来回答——这样回答更准确，也减少了 AI "胡编乱造"（幻觉）的可能。

---

## 🏗️ 项目结构

```
LangChainRAG项目/
├── backend/                    # 后端（Python + FastAPI）
│   ├── app/
│   │   ├── api/                # API 路由层
│   │   │   ├── auth.py         #   用户认证接口（登录/注册）
│   │   │   ├── chat.py         #   问答接口（SSE 流式输出）
│   │   │   ├── session.py      #   会话管理接口
│   │   │   └── knowledge.py    #   知识库管理接口（管理员专属）
│   │   ├── core/               # 核心配置与基础设施
│   │   │   ├── config.py       #   配置管理（读取 .env 文件）
│   │   │   ├── security.py     #   安全相关（JWT、密码哈希）
│   │   │   └── deps.py         #   依赖注入（数据库连接等）
│   │   ├── models/             # 数据库模型（SQLAlchemy ORM）
│   │   │   ├── user.py         #   用户模型
│   │   │   ├── session.py      #   会话模型
│   │   │   ├── message.py      #   消息模型
│   │   │   └── document.py     #   知识文档模型
│   │   ├── rag/                # RAG 核心模块
│   │   │   ├── loader.py       #   文档加载器（PDF/TXT/CSV/DOCX/MD）
│   │   │   ├── splitter.py     #   文本分块器（中文优化）
│   │   │   ├── embeddings.py   #   文本向量化（Embedding）
│   │   │   ├── vectorstore.py  #   向量数据库操作（ChromaDB）
│   │   │   ├── retriever.py    #   检索器（相似度搜索）
│   │   │   └── chain.py        #   RAG 核心链（检索→提示词→LLM→回答）
│   │   ├── schemas/            # 请求/响应数据模型（Pydantic）
│   │   ├── services/           # 业务逻辑层
│   │   └── main.py             # FastAPI 应用入口
│   ├── stress_test/            # 压力测试脚本
│   │   ├── locustfile.py       #   核心压测脚本（模拟多用户对话）
│   │   ├── test_data.py        #   测试数据（100 用户 + 问题池）
│   │   ├── prepare.py          #   测试前准备（自动注册用户）
│   │   └── sse_verify.py       #   SSE 单请求深度剖析
│   ├── uploads/                # 上传的文档文件
│   ├── chroma_data/            # ChromaDB 向量数据持久化目录
│   ├── .env                    # 环境变量配置（需自行创建）
│   ├── .env.example            # 环境变量配置模板
│   └── requirements.txt        # Python 依赖列表
│
├── frontend/                   # 前端（React + TypeScript + Ant Design）
│   ├── src/
│   │   ├── components/         # 通用组件
│   │   │   ├── Layout.tsx      #   页面布局（侧边栏+顶栏）
│   │   │   ├── ChatBubble.tsx  #   聊天气泡组件
│   │   │   ├── SourceCard.tsx  #   引用来源卡片组件
│   │   │   ├── SessionList.tsx #   会话列表组件
│   │   │   └── ProtectedRoute.tsx  # 路由守卫（权限控制）
│   │   ├── pages/              # 页面组件
│   │   │   ├── Chat.tsx        #   问答对话页
│   │   │   ├── KnowledgeBase.tsx   # 知识库管理页（管理员）
│   │   │   ├── Dashboard.tsx   #   系统仪表盘（管理员）
│   │   │   ├── Login.tsx       #   登录页
│   │   │   ├── Register.tsx    #   注册页
│   │   │   └── Profile.tsx     #   个人中心
│   │   ├── services/           # API 调用层
│   │   │   ├── api.ts          #   Axios 实例（拦截器/Token管理）
│   │   │   ├── auth.ts         #   认证相关 API
│   │   │   ├── chat.ts         #   问答相关 API（SSE 流式读取）
│   │   │   └── knowledge.ts    #   知识库相关 API
│   │   ├── store/              # 状态管理（Zustand）
│   │   │   ├── authStore.ts    #   用户认证状态
│   │   │   └── chatStore.ts    #   聊天状态（会话/消息）
│   │   ├── App.tsx             # 根组件（路由配置）
│   │   └── main.tsx            # 应用入口
│   ├── package.json            # 前端依赖配置
│   └── vite.config.ts          # Vite 构建配置
│
├── start.bat                   # Windows 一键启动脚本
└── README.md                   # 本文件
```

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | Python + FastAPI | 高性能异步 Web 框架，自动生成 API 文档 |
| **AI 框架** | LangChain + LangChain Community | RAG 流程编排（文档加载→分块→向量化→检索→生成） |
| **大语言模型** | 阿里云百炼 · 通义千问 qwen-plus | 性价比最高的模型，也支持 qwen-turbo / qwen-max |
| **文本向量化** | 阿里云百炼 text-embedding-v2 | 将文本转为向量，用于语义相似度搜索 |
| **向量数据库** | ChromaDB | 轻量级向量数据库，存储文档片段的向量表示 |
| **关系数据库** | SQLite + SQLAlchemy (异步) | 存储用户、会话、消息、文档元数据 |
| **前端框架** | React 18 + TypeScript | 类型安全的前端开发 |
| **UI 组件库** | Ant Design 5 | 企业级 UI 组件库 |
| **状态管理** | Zustand | 轻量级状态管理库 |
| **路由** | React Router v6 | 前端路由管理 |

### 技术选型说明

- **为什么用 ChromaDB 而不是其他向量数据库？** ChromaDB 是轻量级的，不需要单独部署服务，数据直接存在本地文件里，适合小规模项目和个人使用。如果数据量大了可以迁移到 Milvus 或 Pinecone 等专业向量数据库。
- **为什么用 SQLite 而不是 MySQL/PostgreSQL？** SQLite 是嵌入式数据库，不需要安装和配置数据库服务，开箱即用。对于毕业设计或小型项目完全够用。如果切换到生产环境，只需修改 `DATABASE_URL` 配置即可换成其他数据库。
- **为什么用 SSE 而不是 WebSocket？** SSE（Server-Sent Events，服务端推送事件）是单向的（服务端→客户端），实现更简单，适合 AI 流式输出的场景。WebSocket 是双向通信，但对于"用户发一条消息→AI 流式回复"这种场景来说过于复杂。

---

## ✨ 功能说明

### 💬 知识库问答（所有用户）

- **多轮对话**：支持上下文理解，AI 会记住之前的对话内容
- **流式输出**：打字机效果，一个字一个字地显示回答，不用等完整回答生成完
- **引用来源标注**：回答中标注 `[来源: 文档名]`，点击可查看原文片段和相关度评分
- **会话管理**：创建、切换、重命名、删除会话，不同会话之间的对话历史互不干扰
- **回答反馈**：对 AI 回答进行点赞/点踩

### 📁 知识库管理（仅管理员）

- **文档上传**：支持 PDF、TXT、CSV、DOCX、Markdown 五种格式
- **自动处理**：上传后自动完成文档解析→文本分块→向量化→存入向量数据库
- **文档列表**：分页查看所有文档及处理状态
- **文档删除**：删除文档同时清除向量数据和物理文件
- **分块查看**：查看文档被切分成了哪些文本块
- **系统统计**：仪表盘展示文档数、用户数、问答次数等统计数据

### 👤 用户系统

- **注册/登录**：用户名 + 密码注册和登录
- **JWT 认证**：登录后获得 Token，后续请求自动携带，无需重复登录
  > **注**：JWT（JSON Web Token）是一种身份验证方式，登录成功后服务端签发一个加密的"令牌"给前端，之后每次请求带上这个令牌就能识别用户身份，避免了反复输入密码。
- **角色权限**：管理员（admin）和普通用户两种角色，知识库管理功能仅管理员可访问
- **修改密码**：在个人中心修改登录密码

---

## 🚀 快速启动

### 环境要求

- **Python** 3.11 或更高版本
- **Node.js** 18 或更高版本
- **阿里云百炼 API Key**（[免费注册](https://bailian.console.aliyun.com/)后可获取）

### 1. 配置 API Key

登录 [阿里云百炼控制台](https://bailian.console.aliyun.com/)，开通模型服务并创建 API Key。

将 `backend\.env.example` 复制为 `backend\.env`，填入你的 API Key：

```
DASHSCOPE_API_KEY=sk-your-api-key-here
```

> **注**：API Key 有两种类型——
> - `sk-` 开头的是**全局 Key**，使用默认 API 地址即可
> - `sk-ws-` 开头的是**工作空间 Key**，需要到百炼控制台 → 模型调用 → SDK 示例中查看工作空间专属的 API 地址，并修改 `.env` 中的 `DASHSCOPE_BASE_URL`

### 2. 一键启动（Windows，推荐）

双击项目根目录下的 `start.bat`，脚本会自动完成：

1. 创建 Python 虚拟环境并安装后端依赖
2. 启动后端服务（端口 8000）
3. 安装前端依赖
4. 启动前端开发服务器（端口 5173）
5. 自动打开浏览器

### 3. 手动启动

**启动后端：**

```bash
cd backend

# 创建虚拟环境（首次运行）
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate     # Windows
# source venv/bin/activate   # macOS / Linux

# 安装依赖（首次运行）
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

**启动前端（另开一个终端）：**

```bash
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

然后访问 **http://localhost:5173**

---

## 🔑 默认账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | admin | 123456 | 系统启动时自动创建，可管理知识库 |
| 普通用户 | 自行注册 | - | 可使用问答功能 |

---

## 📖 API 文档

启动后端后，访问 **http://localhost:8000/docs** 查看 Swagger 自动生成的交互式 API 文档。

所有接口：

| 模块 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 认证 | `/api/auth/register` | POST | 用户注册 |
| 认证 | `/api/auth/login` | POST | 用户登录 |
| 认证 | `/api/auth/me` | GET | 获取当前用户信息 |
| 认证 | `/api/auth/change-password` | POST | 修改密码 |
| 会话 | `/api/sessions` | GET / POST | 获取/创建会话列表 |
| 会话 | `/api/sessions/{id}` | PUT / DELETE | 重命名/删除会话 |
| 问答 | `/api/chat/{session_id}` | POST | 发送消息，SSE 流式返回 |
| 问答 | `/api/messages/{id}/feedback` | POST | 对回答进行反馈 |
| 知识库 | `/api/knowledge/documents` | GET | 文档列表（管理员） |
| 知识库 | `/api/knowledge/upload` | POST | 上传文档（管理员） |
| 知识库 | `/api/knowledge/documents/{id}` | GET / DELETE | 查看/删除文档（管理员） |
| 知识库 | `/api/knowledge/documents/{id}/chunks` | GET | 查看文档分块（管理员） |
| 知识库 | `/api/knowledge/stats` | GET | 系统统计（管理员） |

---

## 🔄 RAG 工作流程

以下是系统处理一个用户问题的完整流程，帮助你理解 RAG 是如何工作的：

```
用户提问："iPhone 15 有什么新功能？"
    │
    ▼
┌─────────────────────┐
│ 1. 向量检索          │  将用户问题转为向量，在 ChromaDB 中搜索最相似的 K 个文档片段
│    (Embedding + 相似度)│
└─────────┬───────────┘
          │ 返回 Top-5 相关片段 + 相关度评分
          ▼
┌─────────────────────┐
│ 2. 构建提示词         │  系统提示词（角色设定）+ 知识库内容 + 对话历史 + 用户问题
│    (Prompt Engineering)│
└─────────┬───────────┘
          │ 完整消息列表
          ▼
┌─────────────────────┐
│ 3. LLM 生成回答      │  调用通义千问 qwen-plus，流式生成回答
│    (ChatOpenAI)      │
└─────────┬───────────┘
          │ 流式返回（SSE）
          ▼
┌─────────────────────┐
│ 4. 前端渲染          │  打字机效果逐字显示 + 引用来源卡片
│    (React + SSE)     │
└─────────────────────┘
```

### 文档处理流程（上传时触发）

```
上传文档（PDF/TXT/CSV/DOCX/MD）
    │
    ▼
┌─────────────────────┐
│ 1. 文档加载          │  根据文件类型选择对应的 LangChain 加载器
│    (Document Loader) │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 2. 文本分块          │  使用递归字符分割器（中文优化），每块约 500 字符，重叠 50 字符
│    (Text Splitter)   │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 3. 向量化            │  将每个文本块通过 Embedding 模型转为向量（一串数字）
│    (Embedding)       │
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│ 4. 存入向量数据库     │  向量 + 原文内容 + 元数据 一起存入 ChromaDB
│    (ChromaDB)        │
└─────────────────────┘
```

> **通俗理解**：向量化就是把一段文字变成一串数字（比如 `[0.23, -0.45, 0.78, ...]`），这段数字代表了文字的"语义"。两段意思相近的文字，它们的向量在数学上也"距离近"；意思不同的文字，向量"距离远"。所以当用户提问时，系统把问题也转成向量，然后在向量数据库里找"距离最近"的文档片段——这就是语义搜索。

---

## ⚙️ 配置说明

所有配置项在 `backend/.env` 文件中，完整配置如下：

```env
# 阿里云百炼 API 配置
DASHSCOPE_API_KEY=sk-your-api-key-here        # 必填，API Key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  # API 地址

# 应用配置
APP_NAME=LangChainRAG                          # 应用名称
APP_VERSION=1.0.0                              # 版本号
DEBUG=true                                     # 调试模式

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./app.db      # SQLite 数据库路径

# JWT 密钥（生产环境请更换为随机字符串）
SECRET_KEY=dev-secret-key-change-in-production

# 服务端口
BACKEND_PORT=8000                              # 后端端口
FRONTEND_PORT=5173                             # 前端端口
```

---

## ⚡ 性能优化

针对 100 人并发场景，系统做了以下优化：

### 优化清单

| 文件 | 优化内容 | 通俗解释 |
|------|----------|----------|
| `chat_service.py` | 事务一拆为二 | 用户消息写入后立即释放数据库锁，不再等 AI 回答完才放开 |
| `chain.py` | `asyncio.to_thread` | 检索操作扔到线程池执行，不阻塞其他用户的请求 |
| `vectorstore.py` | 单例缓存 | ChromaDB 实例只创建一次，之后复用，减少磁盘读写 |
| `embeddings.py` | httpx 连接复用 | Embedding API 的 TCP 连接重复使用，减少建连开销 |
| `deps.py` | 连接池扩容 + WAL 模式 | 数据库连接数从 15 提到 50，开启 WAL 让读写并行 |

### 优化前后对比（100 用户压测）

| 指标 | 优化前 | 优化后 | 提升 |
|------|:--:|:--:|------|
| 总失败率 | 37.9% | **3.6%** | ↓ 90% |
| 聊天失败率 | 61.3% | **9.1%** | ↓ 85% |
| 登录失败率 | 8% | **0%** | ✅ 完全消除 |
| 会话失败率 | 50% | **0%** | ✅ 完全消除 |
| 首 Token 中位数 | 23000ms | **2500ms** | 快 9.2 倍 |
| p95 响应时间 | 41000ms | **2900ms** | ↓ 93% |

> **核心瓶颈分析**：SQLite 属于文件型数据库，同一时刻只允许一个写入操作，天然不适合高并发。优化通过拆分事务 + 连接池扩容 + WAL 模式，大幅减少了"数据库被锁"的等待时间。如需更高并发，可考虑将数据库换为 PostgreSQL。

---

## 🔬 压力测试

使用 [Locust](https://locust.io/) 进行压力测试，模拟 100 个用户同时进行 3 轮对话。

### 快速压测

```bash
cd backend
venv\Scripts\activate

# 1. 准备测试用户（首次运行）
python stress_test/prepare.py

# 2. 确保后端已启动后，运行压测
python -m locust -f stress_test/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --html report.html

# 3. 浏览器打开 report.html 查看报告
```

### Web UI 模式（演示用）

```bash
python -m locust -f stress_test/locustfile.py
# 浏览器打开 http://localhost:8089，手动控制测试参数
```

### 测试场景

每个虚拟用户执行完整的对话流程：登录 → 创建会话 → 发送问题（SSE 流式读取）→ 追问 × 3 轮，轮间随机等待 3-8 秒模拟真人思考。问题从 13 个长短不一的题目池中随机选取，避免缓存效应。

---

## 📝 许可证

本项目仅用于学习和研究目的。
