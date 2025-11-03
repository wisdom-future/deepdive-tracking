# GCP 部署指南

本指南说明如何将 DeepDive Tracking 部署到 Google Cloud Platform (GCP)。

## 🎯 为什么选择 GCP？

与本地部署相比，GCP 提供：

✅ **邮箱凭证自动管理**
- Secret Manager 安全存储所有凭证
- 自动注入到应用环境变量
- 无需手动复制 App Password
- 自动轮换管理

✅ **GitHub Token 自动处理**
- Secret Manager 加密存储
- 自动从环境变量读取
- 支持自动更新

✅ **其他优势**
- 完全托管的数据库（Cloud SQL）
- 完全托管的缓存（Cloud Memorystore）
- 自动扩展（根据流量自动增加/减少实例）
- 自动备份和灾备
- 完整的监控和日志
- 成本优化（按使用量付费）

## 📋 前置条件

### 1. GCP 账号和项目

```bash
# 安装 Google Cloud SDK
# 访问: https://cloud.google.com/sdk/docs/install

# 初始化 gcloud
gcloud init

# 设置默认项目
gcloud config set project PROJECT_ID

# 验证配置
gcloud config list
```

### 2. 启用必要的 API

```bash
gcloud services enable \
  appengine.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  cloudrun.googleapis.com \
  cloudbuild.googleapis.com
```

## 🚀 部署步骤

### 步骤 1: 创建云资源

#### 1.1 创建 Cloud SQL PostgreSQL 数据库

```bash
# 创建 PostgreSQL 实例
gcloud sql instances create deepdive-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-east1 \
  --availability-type=REGIONAL

# 创建数据库
gcloud sql databases create deepdive_db \
  --instance=deepdive-db

# 创建数据库用户
gcloud sql users create deepdive_user \
  --instance=deepdive-db \
  --password=YOUR_SECURE_DB_PASSWORD
```

#### 1.2 创建 Cloud Memorystore (Redis)

```bash
# 创建 Redis 实例
gcloud redis instances create deepdive-redis \
  --size=1 \
  --region=asia-east1 \
  --tier=basic \
  --redis-version=7.0

# 获取连接信息
gcloud redis instances describe deepdive-redis \
  --region=asia-east1 \
  --format='value(host,port)'
```

### 步骤 2: 配置 Secret Manager

所有敏感信息都存储在 Secret Manager 中：

```bash
# Gmail 凭证
echo -n "hello.junjie.duan@gmail.com" | \
  gcloud secrets create gmail-user --data-file=-

echo -n "YOUR_GMAIL_APP_PASSWORD" | \
  gcloud secrets create gmail-app-password --data-file=-

# GitHub Token
echo -n "YOUR_GITHUB_TOKEN" | \
  gcloud secrets create github-token --data-file=-

# GitHub 仓库信息
echo -n "YOUR_USERNAME/deepdive-tracking" | \
  gcloud secrets create github-repo --data-file=-

echo -n "YOUR_USERNAME" | \
  gcloud secrets create github-username --data-file=-

# OpenAI API Key
echo -n "YOUR_OPENAI_API_KEY" | \
  gcloud secrets create openai-api-key --data-file=-

# WeChat 凭证
echo -n "YOUR_WECHAT_APP_ID" | \
  gcloud secrets create wechat-app-id --data-file=-

echo -n "YOUR_WECHAT_APP_SECRET" | \
  gcloud secrets create wechat-app-secret --data-file=-

# 邮箱列表
echo -n '["recipient@example.com","admin@example.com"]' | \
  gcloud secrets create email-list --data-file=-
```

### 步骤 3: 更新部署配置

编辑 `infra/gcp/app.yaml`，更新以下信息：

```yaml
env_variables:
  # 数据库连接 - 替换为你的实际实例
  DATABASE_URL: "postgresql://deepdive_user:YOUR_DB_PASSWORD@CLOUD_SQL_IP:5432/deepdive_db"

  # Redis 连接 - 替换为你的实际 Redis 地址
  REDIS_URL: "redis://REDIS_HOST:REDIS_PORT/0"

  # 邮箱配置
  GMAIL_USER: "${GMAIL_USER}"
  GMAIL_APP_PASSWORD: "${GMAIL_APP_PASSWORD}"
  EMAIL_LIST: "${EMAIL_LIST}"

  # GitHub 配置
  GITHUB_TOKEN: "${GITHUB_TOKEN}"
  GITHUB_REPO: "${GITHUB_REPO}"
  GITHUB_USERNAME: "${GITHUB_USERNAME}"

  # OpenAI 配置
  OPENAI_API_KEY: "${OPENAI_API_KEY}"

  # WeChat 配置
  WECHAT_APP_ID: "${WECHAT_APP_ID}"
  WECHAT_APP_SECRET: "${WECHAT_APP_SECRET}"

beta_settings:
  # 更新为你的项目 ID 和实例名称
  cloud_sql_instances: "YOUR_PROJECT_ID:asia-east1:deepdive-db"
```

### 步骤 4: 部署应用

#### 选项 A: 部署到 App Engine（推荐用于长期运行任务）

```bash
# 从项目根目录
cd D:\projects\deepdive-tracking

# 部署应用
gcloud app deploy infra/gcp/app.yaml --promote

# 查看部署日志
gcloud app logs read -n 50

# 访问应用
gcloud app browse
```

#### 选项 B: 部署到 Cloud Run（推荐用于 API 服务）

```bash
# 创建 Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:$PORT", "src.main:app"]
EOF

# 部署到 Cloud Run
gcloud run deploy deepdive-tracking \
  --source . \
  --platform managed \
  --region asia-east1 \
  --memory=2Gi \
  --timeout=900 \
  --allow-unauthenticated
```

### 步骤 5: 初始化数据库和优先级配置

```bash
# 方法 1: 通过 Cloud Shell
gcloud shell

# 连接到云数据库
python -c "
from src.config import get_settings
from sqlalchemy import create_engine
from src.models import Base

settings = get_settings()
engine = create_engine(settings.database_url)
Base.metadata.create_all(engine)
print('Database tables created')
"

# 初始化优先级配置
python scripts/init_publish_priorities.py

# 验证配置
python scripts/show_publish_priorities.py

# 方法 2: 通过远程 SSH（如果使用 App Engine）
gcloud app instances list
gcloud app instances describe INSTANCE_ID --format=json
```

## 📧 邮件发送验证

### 在 GCP 上测试邮件发送

```bash
# 在 Cloud Shell 中运行 dry-run 测试
python scripts/run_priority_publishing_test.py 3 --dry-run

# 查看日志
gcloud logging read "resource.type=app_engine_standard" --limit=20

# 实际发送测试（所有凭证自动从 Secret Manager 加载）
python scripts/run_priority_publishing_test.py 3
```

### 验证邮件是否收到

1. **查看发送日志**
```bash
gcloud logging read "textPayload:email AND severity=INFO" --limit=10
```

2. **检查邮箱**
- 检查 `hello.junjie.duan@gmail.com` 的收件箱
- 查看发送成功的统计信息：
```bash
python scripts/show_publish_priorities.py
```

## 📊 监控和日志

### 实时日志查看

```bash
# 查看实时应用日志
gcloud app logs read --tail

# 查看错误日志
gcloud logging read "severity=ERROR" --limit=20

# 按模块查看
gcloud logging read "resource.type=app_engine_standard AND textPayload:priority_publishing" --limit=10
```

### 查看发布统计

```bash
# 在 Cloud Shell 中
python scripts/show_publish_priorities.py

# 示例输出会显示：
# [1] EMAIL - 优先级 10/10
#     • 总成功: 23 篇
#     • 总失败: 2 篇
#     • 最后发布时间: 2025-11-02 15:30:45
#     • 成功率: 92.0%
```

## 💾 数据库管理

### 连接到 Cloud SQL

```bash
# 使用 Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT_ID:asia-east1:deepdive-db=tcp:5432

# 在另一个终端连接
psql -h localhost -U deepdive_user -d deepdive_db
```

### 备份和恢复

```bash
# 创建备份
gcloud sql backups create \
  --instance=deepdive-db \
  --description="Manual backup"

# 列出备份
gcloud sql backups list --instance=deepdive-db

# 恢复备份
gcloud sql backups restore BACKUP_ID \
  --instance=deepdive-db
```

## 🔐 安全最佳实践

### 1. Secret Manager 访问控制

```bash
# 创建 Service Account
gcloud iam service-accounts create deepdive-app \
  --display-name="DeepDive Tracking App"

# 授予 Secret 访问权限
gcloud secrets add-iam-policy-binding gmail-user \
  --member=serviceAccount:deepdive-app@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# （为所有 secrets 重复上述命令）
```

### 2. 定期轮换凭证

```bash
# 更新 Gmail App Password
echo -n "NEW_GMAIL_APP_PASSWORD" | \
  gcloud secrets versions add gmail-app-password --data-file=-

# 更新 GitHub Token
echo -n "NEW_GITHUB_TOKEN" | \
  gcloud secrets versions add github-token --data-file=-
```

### 3. 审计日志

```bash
# 启用 Cloud Audit Logs
gcloud logging sinks create audit-sink \
  logging.googleapis.com/projects/PROJECT_ID/logs/cloudaudit.googleapis.com

# 查看 Audit 日志
gcloud logging read "resource.type=cloudaudit.googleapis.com" --limit=10
```

## 💰 成本优化

### 估算月成本（小规模）

| 服务 | 配置 | 估算成本 |
|------|------|--------|
| App Engine | f1-micro | $10-15 |
| Cloud SQL | db-f1-micro | $15-20 |
| Cloud Memorystore | 1GB | $10-12 |
| Cloud Logging | 10GB logs | $5-10 |
| **总计** | | **$40-60/月** |

### 节省成本的方法

```bash
# 1. 使用 Cloud Run 按需付费（可能更便宜）
gcloud run deploy deepdive-tracking --source .

# 2. 设置预算告警
gcloud billing budgets create \
  --billing-account=ACCOUNT_ID \
  --display-name="Monthly Budget" \
  --budget-amount=100

# 3. 减少日志保留期
gcloud logging sinks update _Default \
  --log-filter='resource.type=app_engine_standard' \
  --log-retention-days=7
```

## 🔧 故障排查

### 常见问题

#### 邮件发送失败

```bash
# 1. 检查 Secret Manager 凭证
gcloud secrets versions access latest --secret="gmail-app-password"

# 2. 查看详细错误日志
gcloud logging read "severity=ERROR AND textPayload:email" --limit=5

# 3. 验证 SMTP 连接
python -c "
import smtplib
from src.config import get_settings

settings = get_settings()
try:
    server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
    server.starttls()
    server.login(settings.smtp_user, settings.smtp_password)
    print('✓ SMTP 连接成功')
    server.quit()
except Exception as e:
    print(f'✗ SMTP 连接失败: {e}')
"
```

#### GitHub 推送失败

```bash
# 1. 检查 GitHub Token 有效性
curl -H "Authorization: token TOKEN" https://api.github.com/user

# 2. 验证仓库权限
git ls-remote https://github.com/YOUR_USERNAME/REPO.git

# 3. 查看 Git 操作日志
gcloud logging read "textPayload:github" --limit=10
```

#### 数据库连接失败

```bash
# 1. 检查 Cloud SQL 实例
gcloud sql instances list

# 2. 查看连接错误
gcloud logging read "resource.type=cloudsql_database" --limit=10

# 3. 使用 Cloud SQL Proxy
cloud_sql_proxy -instances=PROJECT_ID:asia-east1:deepdive-db=tcp:5432
```

## 📖 相关文档

- 📚 **系统文档**: `docs/guides/priority-publishing.md`
- ⚙️ **配置指南**: `docs/guides/configure-publishing-channels.md`
- 📊 **实现状态**: `docs/development/priority-publishing-status.md`

## ✅ 部署检查清单

在部署前请确认：

- [ ] GCP 项目已创建并启用必要的 API
- [ ] Cloud SQL 和 Redis 实例已创建
- [ ] Secret Manager 中已存储所有凭证
- [ ] `infra/gcp/app.yaml` 已更新为实际的资源配置
- [ ] `.env` 文件（本地开发）已配置（如需本地测试）
- [ ] 数据库表已初始化（运行 `init_publish_priorities.py`）
- [ ] Dry-run 测试已验证（`run_priority_publishing_test.py --dry-run`）
- [ ] 邮箱地址已验证（可以接收测试邮件）
- [ ] GitHub 仓库已准备（如使用 GitHub 发布）

## 🚀 后续步骤

1. ✅ 创建 GCP 项目和资源
2. ✅ 配置 Secret Manager
3. ✅ 部署应用
4. ✅ 验证邮件发送功能
5. ✅ 设置监控告警
6. ✅ 定期查看日志和统计

完成这些步骤后，你的 DeepDive Tracking 就可以在 GCP 上自动运行，所有凭证都由 Secret Manager 安全管理！

