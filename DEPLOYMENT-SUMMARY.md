# GCP 部署总结

**状态**: 🔄 进行中
**日期**: 2025-11-03
**部署策略**: Cloud Run（Docker 容器化）

---

## 📋 已完成的工作

### ✅ 阶段 1: GCP 基础设施 (100%)

#### 云资源创建
- **Cloud SQL PostgreSQL 15**
  - 实例: deepdive-db
  - IP: 35.189.186.161:5432
  - 数据库: deepdive_db
  - 用户: deepdive_user
  - 状态: ✅ RUNNABLE

- **Cloud Memorystore Redis 7.2**
  - 实例: deepdive-redis
  - IP: 10.240.18.115:6379
  - 大小: 1GB
  - 状态: ✅ RUNNING

- **Secret Manager (9个秘密)**
  - ✅ gmail-user
  - ✅ gmail-app-password (需更新实际值)
  - ✅ github-token (需更新实际值)
  - ✅ github-repo
  - ✅ github-username
  - ✅ openai-api-key (需更新实际值)
  - ✅ wechat-app-id (需更新实际值)
  - ✅ wechat-app-secret (需更新实际值)
  - ✅ email-list

### ✅ 阶段 2: 应用配置 (100%)

#### 部署配置文件修复
| 文件 | 问题 | 修复 |
|------|------|------|
| infra/gcp/app.yaml | 不支持memory_utilization | 删除 |
| infra/gcp/app.yaml | 不支持automatic_scaling | 删除 |
| infra/gcp/app.yaml | Python 3.9已停止支持 | 升级到3.11 |
| **决定** | 🔄 **app.yaml 方案有限制** | ✅ **切换到 Cloud Run** |

#### 现在使用 Cloud Run
- ✅ Docker 容器化部署
- ✅ Python 3.11-slim 基础镜像
- ✅ Uvicorn ASGI 服务器
- ✅ 更灵活的运行时配置

### ✅ 阶段 3: 优先级发布系统 (已在之前完成)

完整实现的系统功能:
- ✅ PublishPriority 数据模型
- ✅ PriorityPublishingWorkflow 工作流
- ✅ Email > GitHub > WeChat 优先级
- ✅ 灵活的内容过滤规则
- ✅ 时间和限流控制
- ✅ 完整的文档和脚本

---

## 🔄 进行中的步骤

### 🔄 Cloud Run 部署 (已启动)

**部署命令**:
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

**当前进度**:
1. ✅ 创建了 Artifact Registry 存储库
2. ✅ 上传了源代码
3. 🔄 构建 Docker 镜像 (进行中)
4. ⏳ 部署到 Cloud Run (待进行)

**预期完成时间**: 5-10 分钟

**完成后的 URL**:
```
https://deepdive-tracking-XXXXX.asia-east1.run.app
```

---

## ⏳ 待完成的步骤

### 第1步: 等待 Cloud Run 部署完成
当部署完成时，你将看到:
```
Service [deepdive-tracking] revision [XXX] has been deployed
and is serving 100 percent of traffic.
Service URL: https://deepdive-tracking-XXXXX.asia-east1.run.app
```

### 第2步: 初始化数据库表

```bash
# 使用 gcloud shell 或 Cloud SQL Proxy
python -c "
from src.config import get_settings
from sqlalchemy import create_engine
from src.models import Base

settings = get_settings()
engine = create_engine(settings.database_url)
Base.metadata.create_all(engine)
print('✓ Database tables created successfully')
"
```

### 第3步: 初始化优先级配置

```bash
# 初始化默认优先级配置
python scripts/init_publish_priorities.py

# 验证配置
python scripts/show_publish_priorities.py
```

预期输出:
```
[1] EMAIL - 优先级 10/10
    • 总成功: 0 篇
    • 总失败: 0 篇
    • 最后发布时间: 未发布
    • 成功率: N/A

[2] GITHUB - 优先级 9/10
    • 总成功: 0 篇
    • 总失败: 0 篇
    • 最后发布时间: 未发布
    • 成功率: N/A

[3] WECHAT - 优先级 8/10
    • 总成功: 0 篇
    • 总失败: 0 篇
    • 最后发布时间: 未发布
    • 成功率: N/A
```

### 第4步: 更新 Secret Manager 中的实际凭证

```bash
# 更新 Gmail 应用密码
echo -n "YOUR_REAL_GMAIL_APP_PASSWORD" | \
  gcloud secrets versions add gmail-app-password --data-file=-

# 更新 GitHub Token
echo -n "YOUR_REAL_GITHUB_TOKEN" | \
  gcloud secrets versions add github-token --data-file=-

# 更新 OpenAI API 密钥
echo -n "YOUR_REAL_OPENAI_API_KEY" | \
  gcloud secrets versions add openai-api-key --data-file=-

# 更新 WeChat 凭证（可选）
echo -n "YOUR_WECHAT_APP_ID" | \
  gcloud secrets versions add wechat-app-id --data-file=-

echo -n "YOUR_WECHAT_APP_SECRET" | \
  gcloud secrets versions add wechat-app-secret --data-file=-
```

### 第5步: 测试邮件和 GitHub 发布

```bash
# Dry-run 模式（不实际发送）
python scripts/run_priority_publishing_test.py 3 --dry-run

# 实际发送测试
python scripts/run_priority_publishing_test.py 3
```

### 第6步: 验证功能

**邮件验证**:
- 检查 hello.junjie.duan@gmail.com 邮箱
- 应该收到 3 封测试邮件

**GitHub 验证**:
- 检查 GitHub 仓库
- 应该看到新的提交或 Pull Request

**查看统计**:
```bash
python scripts/show_publish_priorities.py
```

---

## 🎯 GCP 资源概览

### 资源列表命令

```bash
# Cloud SQL
gcloud sql instances list

# Redis
gcloud redis instances list --region=asia-east1

# Secret Manager
gcloud secrets list

# Cloud Run
gcloud run services list --region=asia-east1

# Artifact Registry (Docker 仓库)
gcloud artifacts repositories list --location=asia-east1
```

### 监控和日志

```bash
# 查看 Cloud Run 日志
gcloud run services describe deepdive-tracking --region=asia-east1

# 实时日志
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --tail

# 错误日志
gcloud logging read "severity=ERROR" --limit=20
```

---

## 📊 成本估计

| 服务 | 配置 | 月成本 |
|------|------|--------|
| Cloud Run | 1GB RAM, 1 vCPU, 900s timeout | $10-15 |
| Cloud SQL | PostgreSQL db-f1-micro | $15-20 |
| Cloud Memorystore | Redis 1GB | $10-12 |
| Cloud Logging | 记录存储 | $5-10 |
| Artifact Registry | Docker 镜像存储 | $1-2 |
| **总计** | | **$40-60/月** |

---

## 🔒 安全检查清单

- [ ] 定期更新 Secret Manager 中的凭证
- [ ] 使用最小权限原则配置服务账号
- [ ] 启用 Cloud Audit Logs
- [ ] 监控异常日志活动
- [ ] 定期检查访问控制

---

## 📚 文档导航

| 文档 | 目的 |
|------|------|
| [GCP 部署指南](docs/deployment/GCP-DEPLOYMENT.md) | 完整的部署步骤 |
| [优先级发布文档](docs/guides/priority-publishing.md) | 发布系统文档 |
| [配置指南](docs/guides/configure-publishing-channels.md) | Email/GitHub/WeChat 配置 |
| [实现状态](docs/development/priority-publishing-status.md) | 功能实现细节 |

---

## 🚀 后续步骤

### 当前
1. ⏳ 等待 Cloud Run 部署完成 (~5-10 分钟)
2. 📝 部署完成后更新 Secret Manager 凭证

### 部署完成后
1. 初始化数据库表
2. 初始化优先级配置
3. 测试邮件和 GitHub 发布
4. 监控应用日志和性能

### 长期维护
1. 定期查看日志
2. 更新凭证（Google 推荐每 90 天）
3. 监控成本
4. 制定灾备计划

---

## 💡 提示

- **部署 URL**: 部署完成后检查 `gcloud run services list`
- **调试**: 查看实时日志 `gcloud logging read --tail`
- **重新部署**: 代码更新后运行 `gcloud run deploy deepdive-tracking --source .`
- **成本优化**: Cloud Run 按请求计费，闲置不产生成本

---

**预期状态**: 📋 当前 Cloud Run 部署进行中
**下一步**: 等待部署完成，然后初始化数据库
**估计时间**: 总共 10-15 分钟（包括 Docker 构建）
