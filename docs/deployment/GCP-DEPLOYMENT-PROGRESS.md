# GCP 部署进度报告

**报告日期**: 2025-11-03
**部署状态**: 进行中

---

## 完成的步骤

### ✅ 第1步: 初始化GCP项目
- [x] 创建GCP项目 (deepdive-engine)
- [x] 设置默认项目和区域 (asia-east1)
- [x] 启用必要的 API:
  - appengine
  - sqladmin
  - redis
  - secretmanager
  - cloudbuild

### ✅ 第2步: 创建云资源

#### Cloud SQL (PostgreSQL 15)
- [x] 实例名: deepdive-db
- [x] IP: 35.189.186.161
- [x] 端口: 5432
- [x] 数据库: deepdive_db
- [x] 用户: deepdive_user
- [x] 状态: RUNNABLE

#### Cloud Memorystore (Redis)
- [x] 实例名: deepdive-redis
- [x] IP: 10.240.18.115
- [x] 端口: 6379
- [x] 版本: Redis 7.2
- [x] 大小: 1GB
- [x] 状态: RUNNING

### ✅ 第3步: 配置 Secret Manager
创建了 8 个秘密用于安全存储凭证:

| 秘密名称 | 用途 | 状态 |
|---------|------|------|
| gmail-user | Gmail邮箱地址 | ✅ 已创建 |
| gmail-app-password | Gmail应用密码 | ⚠️ 需更新为实际值 |
| github-token | GitHub Token | ⚠️ 需更新为实际值 |
| github-repo | GitHub仓库 | ✅ 已创建 |
| github-username | GitHub用户名 | ✅ 已创建 |
| openai-api-key | OpenAI API密钥 | ⚠️ 需更新为实际值 |
| wechat-app-id | WeChat应用ID | ⚠️ 需更新为实际值 |
| wechat-app-secret | WeChat应用密钥 | ⚠️ 需更新为实际值 |
| email-list | 邮件列表 | ✅ 已创建 |

### ✅ 第4步: 更新部署配置

#### app.yaml 修复历史
1. ✅ 移除了不支持的 `memory_utilization` 属性
2. ✅ 移除了不支持的 `automatic_scaling` 配置
3. ✅ 更新了 Python 运行时版本:
   - ❌ python39 (已停止支持)
   - ❌ python312 (不可用)
   - ❌ python311 (已停止支持)
   - 🔄 python310 (当前)

#### 环境变量
配置了所有必要的环境变量:
- 数据库连接: DATABASE_URL
- Redis 连接: REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND
- OpenAI: OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS
- Email: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL, EMAIL_LIST
- GitHub: GITHUB_TOKEN, GITHUB_REPO, GITHUB_USERNAME, GITHUB_LOCAL_PATH
- WeChat: WECHAT_API_URL, WECHAT_APP_ID, WECHAT_APP_SECRET
- 功能开关: ENABLE_AI_SCORING, ENABLE_DUPLICATE_DETECTION, ENABLE_AUTO_PUBLISHING, ENABLE_ANALYTICS

### ✅ 第5步: 创建 App Engine 应用
- [x] 执行 `gcloud app create --region=asia-east1`
- [x] 应用创建成功
- [x] 应用URL: https://deepdive-engine.de.r.appspot.com

---

## 进行中的步骤

### 🔄 第6步: 部署应用 (已切换到 Cloud Run)
**状态**: 进行中 (背景任务 bbbd26)

#### 为什么切换到 Cloud Run？
- App Engine 对 Python 版本有限制 (所有版本都过期)
- Cloud Run 使用 Docker，更灵活
- 我们已有 Python 3.11 的 Dockerfile
- Cloud Run 更适合现代应用部署

部署命令:
```bash
gcloud run deploy deepdive-tracking \
  --source . \
  --platform managed \
  --region asia-east1 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 900 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL="..." \
  --set-env-vars REDIS_URL="..." \
  --set-env-vars CELERY_BROKER_URL="..." \
  --set-env-vars CELERY_RESULT_BACKEND="..."
```

配置:
- Docker 镜像 (Python 3.11-slim)
- Uvicorn ASGI 服务器
- 内存: 1GB
- CPU: 1 vCPU
- 超时: 900秒
- 绑定到 0.0.0.0:8000

预期输出:
```
Building and deploying new service...
✓ Deploying...
  ✓ Creating Revision...
  ✓ Routing traffic...

Service [deepdive-tracking] revision [deepdive-tracking-xxxxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://deepdive-tracking-xxxxx.asia-east1.run.app
```

---

## 待完成的步骤

### ⏳ 第7步: 初始化数据库

完成 App Engine 部署后:

```bash
# 登录到 Cloud Shell
gcloud shell

# 初始化数据库表
python -c "
from src.config import get_settings
from sqlalchemy import create_engine
from src.models import Base

settings = get_settings()
engine = create_engine(settings.database_url)
Base.metadata.create_all(engine)
print('✓ Database tables created')
"

# 初始化优先级配置
python scripts/init_publish_priorities.py

# 验证配置
python scripts/show_publish_priorities.py
```

### ⏳ 第8步: 验证功能

```bash
# Dry-run 测试（不发送邮件）
python scripts/run_priority_publishing_test.py 3 --dry-run

# 实际发送测试
python scripts/run_priority_publishing_test.py 3

# 查看发送结果
python scripts/show_publish_priorities.py
```

### ⏳ 第9步: 验证邮件发送
- 检查 hello.junjie.duan@gmail.com 邮箱
- 应该收到测试邮件

### ⏳ 第10步: 验证 GitHub 发布（如配置）
- 检查 GitHub 仓库
- 应该看到新的提交或 Pull Request

---

## 关键信息

### GCP 资源列表

**数据库**:
```bash
gcloud sql instances list
# 输出: deepdive-db  POSTGRES_15  asia-east1-c  db-f1-micro  35.189.186.161  RUNNABLE
```

**缓存**:
```bash
gcloud redis instances list --region=asia-east1
# 输出: deepdive-redis  RUNNING  10.240.18.115  6379
```

**秘密**:
```bash
gcloud secrets list
# 输出: 9个秘密 (gmail-user, gmail-app-password, github-token, 等)
```

**应用**:
```bash
gcloud app versions list
# 输出: 应用版本和部署时间
```

### 访问应用

部署完成后，应用将在以下 URL 可访问:
- **生产环境**: https://deepdive-engine.de.r.appspot.com
- **App Engine 控制面板**: https://console.cloud.google.com/appengine

### 查看日志

```bash
# 实时日志
gcloud app logs read --tail

# 错误日志
gcloud logging read "severity=ERROR" --limit=20

# 特定模块的日志
gcloud logging read "textPayload:priority_publishing" --limit=10
```

### 数据库连接

从本地连接到 Cloud SQL:

```bash
# 1. 安装 Cloud SQL Proxy
# https://cloud.google.com/sql/docs/postgres/sql-proxy

# 2. 启动 Proxy
cloud_sql_proxy -instances=deepdive-engine:asia-east1:deepdive-db=tcp:5432

# 3. 在另一个终端连接
psql -h localhost -U deepdive_user -d deepdive_db
```

---

## 故障排查

### 常见问题

**Q: 部署失败，显示 "runtime version past End of Support"**
A: 更新 app.yaml 中的 Python 版本。当前使用 Python 3.10，这是最新支持的版本。

**Q: 无法连接到 Cloud SQL**
A:
1. 确认 Cloud SQL 实例正在运行
2. 使用 Cloud SQL Proxy 从本地连接
3. 从 App Engine 应该能自动连接

**Q: 邮件不能发送**
A:
1. 检查 Secret Manager 中的 Gmail 凭证是否正确
2. 查看应用日志: `gcloud app logs read --tail`
3. 确保 Gmail 帐户启用了应用密码（不是账户密码）

**Q: GitHub 推送失败**
A:
1. 检查 GitHub Token 权限
2. 确保 Token 有 `repo` 权限
3. 验证仓库路径和用户名是否正确

---

## 下一步

1. ✅ 等待 App Engine 部署完成
2. ⏳ 登录 Cloud Shell 初始化数据库
3. ⏳ 运行优先级发布初始化脚本
4. ⏳ 测试邮件和 GitHub 发布功能
5. ⏳ 验证邮件是否成功发送

---

## 相关文档

- [GCP 部署指南](./GCP-DEPLOYMENT.md)
- [优先级发布文档](../guides/priority-publishing.md)
- [配置指南](../guides/configure-publishing-channels.md)
- [实现状态](../development/priority-publishing-status.md)

---

**最后更新**: 2025-11-03 00:23 UTC
**部署 ID**: e3ea2d (App Engine deployment)
