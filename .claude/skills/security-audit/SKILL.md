---
name: security-audit
description: 安全审计——检查代码中的敏感信息泄露、API密钥暴露、JWT安全隐患、XSS风险、SQL注入等Web应用安全问题。支持 Python 后端和 TypeScript 前端。
allowed-tools: Read, Grep, Glob
user-invocable: true
---

# 安全审计

对项目代码进行安全审查，查找潜在的安全隐患，并输出审计报告。

本项目是 **FastAPI + React Web 应用**，需从后端和前端两个维度进行审计。

## 审计范围

### 一、敏感信息泄露

检查代码中是否硬编码（写死）了敏感信息：

```python
# ❌ 危险：硬编码密码
password = "admin123"
db_password = "mypassword"

# ❌ 危险：硬编码 API 密钥 / Token
api_key = "sk-xxxxxxxxxxxx"
dashscope_api_key = "sk-ws-..."
jwt_secret = "my-secret-key"

# ❌ 危险：硬编码数据库连接信息
db_url = "mysql://root:password@localhost/db"
```

检查项：
- 变量名含 `password`、`secret`、`key`、`token`、`api_key` 且赋值为字符串字面量
- `.env` 文件中包含真实密钥但未加入 `.gitignore`
- 前端代码（`.ts`、`.tsx`）中是否直接硬编码了 API 密钥（前端代码会被浏览器下载，密钥必须只在后端）
- 配置文件（`settings.local.json` 等）中是否写了密钥明文
- 邮箱地址、手机号等个人信息直接写在代码中

通俗解释：就像不要把家门钥匙贴在门口一样，密码、密钥这些"钥匙"不能直接写在代码里被人看到。尤其是前端代码，任何人打开浏览器开发者工具就能看到。

### 二、JWT 认证安全

检查 JWT（JSON Web Token，用户登录凭证）相关的安全问题：

```python
# ❌ 危险：JWT 密钥太弱
SECRET_KEY = "123456"  # 太短，容易被暴力破解

# ❌ 危险：Token 不过期
access_token_expire_minutes = 999999999

# ❌ 危险：不验证 Token 签名
payload = jwt.decode(token, options={"verify_signature": False})
```

检查项：
- JWT 密钥强度是否足够（建议至少 32 字符随机字符串）
- Token 过期时间是否合理
- 前端 localStorage 存储 Token 是否存在 XSS 风险（localStorage 可被 JS 读取）
- 是否在每次请求时验证 Token 有效性
- 退出登录时前端是否清除 Token

### 三、API 安全（Web 特有）

```python
# ❌ 危险：CORS 全开（允许任意网站请求）
allow_origins=["*"]

# ❌ 危险：管理员接口没有权限校验
@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):  # 缺少 admin 权限校验！
    ...

# ❌ 危险：不限制请求频率（可被暴力攻击）
# 登录接口没有限流措施
```

检查项：
- CORS 配置是否限制了允许的来源
- 管理员接口是否都有权限校验（`Depends(get_current_admin_user)`）
- 用户接口是否校验了资源归属（用户只能操作自己的会话/消息）
- 登录接口是否有频率限制（防止暴力破解密码）
- API 返回的错误信息是否泄露了内部细节（如数据库错误、堆栈跟踪）
- 文件上传是否校验了文件类型和大小

### 四、前端安全

```typescript
// ❌ 危险：直接渲染用户输入（XSS 风险）
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ❌ 危险：在前端代码中写 API Key
const API_KEY = "sk-ws-xxxxx"

// ❌ 危险：直接使用 URL 参数而不校验
const redirectUrl = new URLSearchParams(location.search).get('redirect')
window.location.href = redirectUrl  // 开放重定向
```

检查项：
- 是否使用了 `dangerouslySetInnerHTML`（React 的 XSS 风险 API）
- 前端代码中是否有 API Key / Token 硬编码
- 用户输入在显示前是否转义
- 路由跳转是否校验了目标地址
- 敏感操作（删除等）是否有确认弹窗

### 五、其他安全隐患

#### 5.1 危险函数使用

```python
# ❌ 危险：eval/exec 可执行任意代码
eval(user_input)
exec(user_input)

# ❌ 危险：pickle 反序列化不可信数据
pickle.loads(untrusted_data)

# ❌ 危险：使用 os.system 拼接用户输入
os.system("rm -rf " + user_path)
```

检查项：
- `eval()`、`exec()`、`compile()` 的使用
- `pickle.loads()` / `pickle.load()` 加载不可信数据
- `os.system()`、`subprocess.call(shell=True)` 拼接用户输入
- `__import__()` 动态导入不可信模块名

#### 5.2 SQL 注入风险

```python
# ❌ 危险：字符串拼接 SQL（可被注入）
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# ✅ 安全：SQLAlchemy ORM 参数化查询（自动防注入）
result = await db.execute(select(User).where(User.name == user_input))
```

检查项：
- 是否使用了原始 SQL 字符串拼接（f-string、`+`、`%` 拼接 SQL）
- 注意：SQLAlchemy ORM 的 `where()` 是参数化的，本身安全。但如果用了 `text()` 函数拼接字符串则需要检查

#### 5.3 依赖安全

```python
# ❌ 危险：固定旧版本且有已知漏洞
fastapi==0.68.0  # 太旧

# ✅ 安全：使用较新版本
fastapi>=0.100.0
```

检查项：
- `requirements.txt` 中是否有已知漏洞的旧版本依赖
- `package.json` 中是否有不再维护的废弃包
- fastapi、uvicorn、sqlalchemy、chromadb 等核心包版本是否合理

#### 5.4 文件路径安全

```python
# ❌ 危险：路径遍历攻击
file_path = "../etc/passwd"
open("/data/" + user_input)  # 用户可输入 ../../etc/passwd
```

检查项：
- 文件上传路径是否由用户输入拼接
- 文件删除是否校验了路径（防止删除系统文件）
- `.env` 文件是否在 `.gitignore` 中

#### 5.5 异常处理不当

```python
# ❌ 危险：空 except 吞掉所有错误（ChromaDB 操作中常见）
try:
    vectorstore.delete(ids=ids_to_delete)
except Exception:
    pass  # 删失败了也不知道

# ❌ 危险：异常信息暴露内部细节
except Exception as e:
    return {"error": str(e)}  # 可能泄露数据库结构、文件路径等
```

---

## 执行步骤

1. **扫描项目文件** — 找出所有需要检查的文件（`.py`、`.ts`、`.tsx`、`.env`、配置文件等）
2. **逐项检查** — 按上述五个维度逐一审计
3. **分级标记** — 每个问题标注严重程度
4. **生成报告** — 输出结构化审计报告

---

## 严重程度定义

| 等级 | 标记 | 定义 | 示例 |
|------|------|------|------|
| 🔴 严重 | Critical | 可直接导致数据泄露或系统被控制 | 硬编码 API Key、JWT 密钥太弱 |
| 🟠 高危 | High | 存在明确的安全风险 | eval 执行用户输入、CORS 全开 |
| 🟡 中危 | Medium | 有安全隐患但利用条件较苛刻 | 异常信息暴露内部细节 |
| 🔵 低危 | Low | 不规范的写法，建议改进 | 依赖版本过旧 |

---

## 输出格式

```markdown
## 🔒 安全审计报告

**审计时间**：YYYY-MM-DD HH:MM
**审计范围**：N 个文件
- 后端：X 个 .py 文件
- 前端：Y 个 .ts/.tsx 文件
- 配置：Z 个配置文件

### 总览

| 严重程度 | 数量 |
|---------|------|
| 🔴 严重 | X |
| 🟠 高危 | X |
| 🟡 中危 | X |
| 🔵 低危 | X |

### 问题清单

| # | 位置 | 等级 | 类别 | 问题描述 | 修复建议 |
|---|------|------|------|---------|---------|
| 1 | .env:3 | 🔴 | 敏感信息 | API Key 未加入 .gitignore | 将 .env 加入 .gitignore |
| 2 | knowledge.py:73 | 🟡 | 异常处理 | except: pass 吞掉异常 | 至少记录日志 |

### 总体建议

（针对发现的问题给出整体安全改进建议）
```

---

## 注意事项

- 只检查安全问题，不修改代码
- 区分"真问题"和"看起来像问题"——例如变量名 `password_label`（密码标签控件）不是硬编码密码
- 对每个问题给出具体的、可操作的修复建议，用通俗语言解释为什么是问题
- 如果项目没有发现任何安全问题，也要输出报告明确说明
- 前后端代码分开检查，分别标注
