# GCP Automation Deployment Guide - 自动化部署指南

**版本：** 1.0
**更新时间：** 2025-11-07
**目标：** 实现每日自动采集、评分、发送邮件到 hello.junjie.duan@gmail.com

---

## 📋 系统架构

```
Cloud Scheduler (每天 9:00 AM)
    ↓
    POST /api/v1/workflows/daily
    ↓
Cloud Run (deepdive-tracking)
    ↓
执行 daily_complete_workflow.py
    ↓
Step 1: 数据采集 (scripts/collection/collect_news.py)
    ↓
Step 2: AI评分 (scripts/evaluation/score_collected_news.py)
    ↓
Step 3: 邮件发送 (scripts/publish/send_top_news_email.py)
    ↓
Step 4: GitHub发布 (scripts/publish/send_top_ai_news_to_github.py)
    ↓
邮件发送到: hello.junjie.duan@gmail.com
```

---

## ✅ 前置条件检查

### 1. GCP 服务状态

```bash
# 验证 Cloud Run 服务运行中
gcloud run services describe deepdive-tracking \
    --region=asia-east1 \
    --project=deepdive-tracking

# 应该看到:
# Service URL: https://deepdive-tracking-orp2dcdqua-de.a.run.app
# Status: Ready
```

### 2. 密钥配置检查

```bash
# 列出所有密钥
gcloud secrets list --project=deepdive-tracking

# 需要确保以下密钥存在:
# - gmail-username        (用于发送邮件)
# - gmail-password        (Gmail App Password)
# - openai-api-key        (用于AI评分)
# - github-token          (用于GitHub发布)
# - database-url          (Cloud SQL连接)
```

### 3. 数据库连接检查

```bash
# 验证 Cloud SQL 实例运行中
gcloud sql instances describe deepdive-tracking-db \
    --project=deepdive-tracking

# Status 应该是 RUNNABLE
```

---

## 🚀 部署步骤

### Step 1: 更新代码并提交

```bash
# 查看更改
git status

# 应该看到以下新文件/修改:
# - src/api/v1/endpoints/workflows.py (新增)
# - src/main.py (修改 - 添加 workflows router)
# - infra/gcp/setup_cloud_scheduler.sh (新增)
# - scripts/workflows/daily_workflow.py (新增)

# 提交更改
git add .
git commit -m "feat(automation): add Cloud Scheduler integration for daily workflows

- Add workflows API endpoints (/api/v1/workflows/daily, /api/v1/workflows/weekly)
- Add Cloud Scheduler setup script
- Add daily workflow orchestration
- Enable automated collection → scoring → email → GitHub publishing

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 推送到远程
git push origin main
```

### Step 2: 部署到 Cloud Run

```bash
# 方法1: 使用现有部署脚本
bash infra/gcp/deploy.sh

# 方法2: 手动部署
gcloud run deploy deepdive-tracking \
    --source . \
    --region=asia-east1 \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=production" \
    --project=deepdive-tracking

# 等待部署完成 (约3-5分钟)
# 记录服务 URL: https://deepdive-tracking-orp2dcdqua-de.a.run.app
```

### Step 3: 验证 API 端点

```bash
# 测试健康检查
curl https://deepdive-tracking-orp2dcdqua-de.a.run.app/health

# 应该返回: {"status":"ok","version":"0.1.0"}

# 测试新的 workflows 端点 (不实际触发工作流)
curl -X GET https://deepdive-tracking-orp2dcdqua-de.a.run.app/api/v1/workflows/status

# 应该返回工作流状态或 "no_logs"
```

### Step 4: 配置 Cloud Scheduler

```bash
# 运行 Cloud Scheduler 设置脚本
cd infra/gcp
bash setup_cloud_scheduler.sh

# 脚本会:
# 1. 启用必要的 GCP APIs
# 2. 创建服务账号 (deepdive-scheduler)
# 3. 授予 Cloud Run Invoker 权限
# 4. 创建两个定时任务:
#    - deepdive-daily-workflow: 每天 9:00 AM (Beijing)
#    - deepdive-weekly-report: 每周日 10:00 AM (Beijing)
```

### Step 5: 验证 Cloud Scheduler 配置

```bash
# 查看已创建的定时任务
gcloud scheduler jobs list \
    --location=asia-east1 \
    --project=deepdive-tracking

# 应该看到:
# ID                          LOCATION    SCHEDULE    TARGET_TYPE  STATE
# deepdive-daily-workflow     asia-east1  0 9 * * *   HTTP         ENABLED
# deepdive-weekly-report      asia-east1  0 10 * * 0  HTTP         ENABLED

# 查看任务详情
gcloud scheduler jobs describe deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking
```

---

## 🧪 测试

### 1. 手动触发测试 (推荐先测试)

```bash
# 手动触发每日工作流
gcloud scheduler jobs run deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking

# 查看执行日志
gcloud scheduler jobs logs deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking \
    --limit=10
```

### 2. 通过 API 直接测试

```bash
# 直接调用 workflow endpoint
curl -X POST https://deepdive-tracking-orp2dcdqua-de.a.run.app/api/v1/workflows/daily

# 应该返回工作流执行结果:
# {
#   "status": "success",
#   "workflow_type": "daily",
#   "message": "Daily workflow completed successfully",
#   "timestamp": "2025-11-07T...",
#   "result": { ... }
# }
```

### 3. 查看 Cloud Run 日志

```bash
# 查看实时日志
gcloud run services logs read deepdive-tracking \
    --region=asia-east1 \
    --project=deepdive-tracking \
    --limit=100

# 或者在 GCP Console:
# https://console.cloud.google.com/run/detail/asia-east1/deepdive-tracking/logs
```

### 4. 验证邮件发送

检查邮箱: **hello.junjie.duan@gmail.com**

应该收到邮件:
- **主题:** DeepDive Tracking - 今日AI动态精选 (YYYY-MM-DD)
- **发件人:** Gmail账号 (来自 Secret Manager)
- **内容:** TOP 10-15条高分AI新闻，卡片布局

### 5. 验证 GitHub 发布

检查 GitHub 仓库:
- 应该有新的提交推送到 `ai-news-digest` 仓库
- Pages 应该更新: https://jjdudu.github.io/ai-news-digest/

---

## 🔧 故障排查

### 问题1: Cloud Scheduler 触发失败

```bash
# 查看错误日志
gcloud scheduler jobs logs deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking

# 常见原因:
# 1. Service URL 错误 - 检查 setup_cloud_scheduler.sh 中的 SERVICE_URL
# 2. 权限不足 - 检查 deepdive-scheduler 服务账号权限
# 3. Cloud Run 服务未运行 - 检查服务状态

# 解决方法:
# 删除并重新创建任务
gcloud scheduler jobs delete deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking \
    --quiet

bash setup_cloud_scheduler.sh
```

### 问题2: 邮件未收到

```bash
# 1. 检查 Gmail 密钥是否正确
gcloud secrets versions access latest \
    --secret=gmail-username \
    --project=deepdive-tracking

gcloud secrets versions access latest \
    --secret=gmail-password \
    --project=deepdive-tracking

# 2. 检查邮件发送脚本日志
# 在 Cloud Run logs 中搜索: "send_top_news_email"

# 3. 检查垃圾邮件文件夹

# 4. 验证 Gmail App Password 是否有效
# https://myaccount.google.com/apppasswords
```

### 问题3: 数据采集失败

```bash
# 检查数据源配置
# 连接到 Cloud SQL (通过 Cloud SQL Proxy)
gcloud sql connect deepdive-tracking-db --user=postgres

# 在 psql 中:
SELECT name, type, is_enabled FROM data_sources;

# 确保至少有几个启用的数据源

# 检查网络连接
# Cloud Run 需要能访问外部 RSS feeds 和网站
```

### 问题4: AI 评分失败

```bash
# 检查 OpenAI API Key
gcloud secrets versions access latest \
    --secret=openai-api-key \
    --project=deepdive-tracking

# 检查 API 配额和余额
# https://platform.openai.com/usage

# 查看评分日志
# 在 Cloud Run logs 中搜索: "score_collected_news"
```

### 问题5: Workflow 超时

```bash
# Cloud Scheduler 默认超时: 30分钟
# Workflow 脚本超时: 15分钟

# 如果需要增加超时:
gcloud scheduler jobs update http deepdive-daily-workflow \
    --location=asia-east1 \
    --attempt-deadline=45m \
    --project=deepdive-tracking
```

---

## 📊 监控和维护

### 1. 设置告警

```bash
# 创建告警策略 (在 GCP Console)
# 1. Cloud Run 服务错误率 > 5%
# 2. Cloud Scheduler 任务失败
# 3. Cloud SQL 连接数 > 80%

# 或使用 gcloud:
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="DeepDive Workflow Failed" \
    --condition-name="workflow-failed" \
    --condition-filter='resource.type="cloud_run_revision" AND severity="ERROR"'
```

### 2. 每日检查清单

```
□ 检查邮箱是否收到每日邮件
□ 检查 GitHub 仓库是否有新提交
□ 查看 Cloud Run 日志有无错误
□ 检查 Cloud Scheduler 执行历史
□ 监控 OpenAI API 使用量和余额
```

### 3. 每周维护

```bash
# 查看工作流执行统计
gcloud scheduler jobs describe deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking

# 查看近7天的执行日志
gcloud logging read \
    'resource.type="cloud_scheduler_job" AND
     resource.labels.job_name="deepdive-daily-workflow"' \
    --limit=50 \
    --format=json \
    --project=deepdive-tracking

# 清理旧的 workflow logs (可选)
# logs/workflow_*.json 文件可以定期归档或删除
```

---

## 📝 重要文件位置

### 本地代码

```
src/api/v1/endpoints/workflows.py          # Workflow API endpoints
src/main.py                                 # FastAPI app (includes workflows router)
scripts/publish/daily_complete_workflow.py # 完整工作流脚本
infra/gcp/setup_cloud_scheduler.sh         # Cloud Scheduler 设置脚本
docs/GCP_AUTOMATION_DEPLOYMENT.md          # 本文档
```

### GCP 资源

```
Project: deepdive-tracking
Region: asia-east1

Cloud Run Service:
  Name: deepdive-tracking
  URL: https://deepdive-tracking-orp2dcdqua-de.a.run.app

Cloud SQL Instance:
  Name: deepdive-tracking-db
  Type: PostgreSQL 15

Cloud Scheduler Jobs:
  - deepdive-daily-workflow (每天 9:00 AM Beijing)
  - deepdive-weekly-report (每周日 10:00 AM Beijing)

Service Account:
  Email: deepdive-scheduler@deepdive-tracking.iam.gserviceaccount.com
  Role: roles/run.invoker
```

---

## 🔐 安全注意事项

1. **Service Account 权限最小化**
   - deepdive-scheduler 只有 `roles/run.invoker` 权限
   - 不能访问 Secret Manager 或其他资源

2. **Cloud Run 认证**
   - /trigger-workflow 端点需要 OIDC 认证
   - 只有 deepdive-scheduler 可以调用

3. **密钥管理**
   - 所有敏感信息存储在 Secret Manager
   - 不在代码中硬编码任何密钥

4. **网络安全**
   - Cloud Run 默认启用 HTTPS
   - Cloud SQL 使用私有 IP 和 Cloud SQL Proxy

---

## 📞 支持和反馈

- **问题报告:** 创建 GitHub Issue
- **功能建议:** 提交 Pull Request
- **紧急问题:** 联系项目维护者

---

## 📚 相关文档

- [产品需求文档](../product/requirements.md)
- [系统架构设计](../tech/system-design-summary.md)
- [GCP 实现状态](../IMPLEMENTATION-STATUS.md)
- [数据采集配置](../crawler_collector_config_examples.md)

---

**部署完成后的验证标准:**

✅ Cloud Run 服务运行正常
✅ API endpoints 可访问 (/health, /api/v1/workflows/daily)
✅ Cloud Scheduler 任务已创建并启用
✅ 手动触发测试成功
✅ 收到测试邮件 (hello.junjie.duan@gmail.com)
✅ GitHub 仓库有新提交
✅ 日志无错误

**下一步:** 等待明天 9:00 AM，验证自动执行是否成功！
