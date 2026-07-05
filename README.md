# 📚 LangChain RAG 企业级知识库问答系统

基于 LangChain 框架开发的 RAG（检索增强生成）企业级知识库问答系统，面向电商平台商品知识库场景。

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python + FastAPI |
| **AI框架** | LangChain + LangChain Community |
| **LLM** | 阿里云百炼 通义千问 qwen-plus |
| **Embedding** | 阿里云百炼 text-embedding-v2 |
| **向量数据库** | ChromaDB |
| **关系数据库** | SQLite |
| **前端** | React 18 + TypeScript + Ant Design 5 |

## 快速启动

### 环境要求

- Python 3.11+
- Node.js 18+

### 配置 API Key

1. 登录 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 开通模型服务，创建 API Key
3. 将 API Key 填入 `backend\.env` 文件：
   ```
   DASHSCOPE_API_KEY=sk-your-api-key-here
   ```

### 一键启动（Windows）

双击 `start.bat`，脚本会自动：
1. 创建 Python 虚拟环境并安装依赖
2. 启动后端服务（端口 8000）
3. 安装前端依赖
4. 启动前端服务（端口 5173）
5. 自动打开浏览器

### 手动启动

**后端：**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

然后访问 `http://localhost:5173`

## 默认账号

- **管理员**：admin / 123456
- **普通用户**：自行注册

## 功能说明

### 知识库问答（所有用户）
- 多轮对话，支持上下文理解
- 流式输出，打字机效果
- 回答中标注引用来源
- 会话管理（创建、切换、重命名、删除）

### 知识库管理（仅管理员）
- 上传文档（支持 PDF、TXT、CSV、DOCX、MD）
- 查看文档列表和处理状态
- 删除文档（同时清除向量数据）
- 查看文档分块详情

### 用户系统
- 用户注册/登录
- JWT 认证
- 修改密码
- 角色权限控制

## API 文档

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 自动生成的 API 文档。
