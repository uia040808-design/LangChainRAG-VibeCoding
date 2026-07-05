---
name: start
description: 一键启动 LangChain RAG 知识库问答系统（后端 + 前端）
allowed-tools: Bash(pip *), Bash(npm *), Bash(node *), Bash(python *), Bash(cd *), Bash(call *), Bash(start *), Bash(cmd *), Bash(venv/*)
user-invocable: true
---

# 启动系统

启动「LangChain RAG 知识库问答系统」的完整开发环境。

## 系统架构

本系统由两个服务组成：
- **后端**：FastAPI（Python），运行在 http://localhost:8000
- **前端**：React + Vite（Node.js），运行在 http://localhost:5173

## 执行步骤

### 方式一：使用一键启动脚本（推荐）

直接运行项目根目录的 `start.bat`：

```bash
cd "D:\桌面\LangChainRAG项目"
start start.bat
```

脚本会自动完成：
1. 检查 Python 和 Node.js 环境
2. 检查/配置 .env 文件（API Key）
3. 创建虚拟环境并安装后端依赖
4. 启动后端服务（uvicorn，带热重载）
5. 安装前端依赖（如需要）
6. 启动前端开发服务器（Vite，带热更新）
7. 自动打开浏览器访问 http://localhost:5173

### 方式二：手动分步启动

如果只需要重启某个服务或调试：

**只启动后端：**
```bash
cd "D:\桌面\LangChainRAG项目\backend"
venv\Scripts\activate.bat
uvicorn app.main:app --reload --port 8000
```

**只启动前端：**
```bash
cd "D:\桌面\LangChainRAG项目\frontend"
npm run dev
```

## 启动后的访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost:5173 | 用户界面 |
| 后端 API | http://localhost:8000 | REST API |
| API 文档 | http://localhost:8000/docs | Swagger 自动生成的接口文档 |

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |
| 普通用户 | 自行注册 | — |

## 停止服务

关闭后端和前端的命令行窗口即可停止服务。

## 注意事项

- 首次启动会创建虚拟环境和安装依赖，需要联网，耗时 3-5 分钟
- 之后的启动只需启动服务，几秒钟即可
- 后端代码修改后会自动重载（`--reload`），前端代码修改会自动热更新
- 如果端口被占用，修改 backend 的 `--port` 参数或 frontend 的 `vite.config.ts` 配置
- API Key 需要在 backend/.env 文件中配置
