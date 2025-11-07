# 🚀 DeepDive Tracking - Deployment Checklist (Updated)

快速部署检查清单 - 更新版（8:00发布 + 第一个月每6小时 + 24小时内TOP新闻）

**更新日期:** 2025-11-07
**新需求:**
1. ✅ 早上8点发布（从9点改为8点）
2. ✅ 第一个月每6小时发布一次（0:00, 6:00, 12:00, 18:00）
3. ✅ 只发送过去24小时内的TOP新闻
4. ✅ 支持手动触发

---

## ✅ 前置条件

- [ ] GCP Project: `deepdive-tracking` 已配置
- [ ] Cloud Run 服务运行中: https://deepdive-tracking-orp2dcdqua-de.a.run.app
- [ ] Cloud SQL 实例运行中
- [ ] Secret Manager 中所有密钥已配置
  - [ ] gmail-username
  - [ ] gmail-password
  - [ ] openai-api-key
  - [ ] github-token
  - [ ] database-url

---

## 📝 部署步骤 (30分钟)

### Step 1: 提交代码 (5分钟)

```bash
# 检查更改
git status

# 应该看到:
# - scripts/publish/send_top_news_email.py (修改 - 24小时过滤)
# - infra/gcp/setup_cloud_scheduler.sh (修改 - 8:00 + 每6小时)
# - infra/gcp/trigger_workflow_manually.sh (新增)
# - infra/gcp/delete_intensive_schedule.sh (新增)

# 提交更改
git add .
git commit -m "feat(automation): update scheduling requirements

- Change daily workflow to 8:00 AM Beijing Time
- Add intensive schedule for first month (every 6 hours)
- Filter news to last 24 hours only
- Add manual trigger and cleanup scripts

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### Step 2: 部署到 Cloud Run (5分钟)

```bash
# 部署
bash infra/gcp/deploy.sh

# 或手动部署
gcloud run deploy deepdive-tracking \
    --source . \
    --region=asia-east1 \
    --platform=managed \
    --allow-unauthenticated \
    --project=deepdive-tracking
```

**等待部署完成** ⏳ (约3-5分钟)

### Step 3: 验证 API (2分钟)

```bash
# 测试健康检查
curl https://deepdive-tracking-orp2dcdqua-de.a.run.app/health

# 测试 workflow status
curl https://deepdive-tracking-orp2dcdqua-de.a.run.app/api/v1/workflows/status
```

**期望:** 两个请求都返回 JSON 响应

### Step 4: 配置 Cloud Scheduler (3分钟)

```bash
cd infra/gcp
bash setup_cloud_scheduler.sh
```

**期望:** 看到 "Cloud Scheduler Setup Complete!" 消息

### Step 5: 验证 Scheduler (2分钟)

```bash
# 查看定时任务
gcloud scheduler jobs list \
    --location=asia-east1 \
    --project=deepdive-tracking
```

**期望:** 看到三个任务 (ENABLED 状态):
- deepdive-daily-workflow (每天 8:00 AM)
- deepdive-weekly-report (周日 10:00 AM)
- deepdive-intensive-workflow (每6小时 - 临时30天)

### Step 6: 手动触发测试 (10分钟)

**方法1: 使用交互式脚本（推荐）**
```bash
bash infra/gcp/trigger_workflow_manually.sh

# 选择: 1 (Via Cloud Scheduler)
# 选择: 1 (deepdive-daily-workflow)
```

**方法2: 直接命令**
```bash
gcloud scheduler jobs run deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking
```

**等待执行完成** ⏳ (约5-10分钟)

```bash
# 查看日志
gcloud scheduler jobs logs deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking \
    --limit=10
```

### Step 7: 验证结果 (3分钟)

**检查邮箱:**
- [ ] 打开 hello.junjie.duan@gmail.com
- [ ] 查找邮件: "DeepDive Tracking - 今日AI动态精选"
- [ ] 确认邮件格式正确 (卡片布局)
- [ ] 确认有 10-15 条新闻
- [ ] **重要:** 确认所有新闻都是过去24小时内的

**检查 GitHub:**
- [ ] 访问: https://github.com/jjdudu/ai-news-digest
- [ ] 确认有新的提交
- [ ] 访问: https://jjdudu.github.io/ai-news-digest/
- [ ] 确认页面已更新

**检查日志:**
```bash
# 查看 Cloud Run 日志
gcloud run services logs read deepdive-tracking \
    --region=asia-east1 \
    --project=deepdive-tracking \
    --limit=50
```

- [ ] 日志中无 ERROR
- [ ] 看到 "✅ Email sent successfully"
- [ ] 看到 "✅ GitHub publishing completed"

---

## 🎉 部署成功标准

✅ 所有步骤无错误完成
✅ 手动触发测试成功
✅ 收到测试邮件
✅ GitHub 有新提交
✅ 日志无错误

---

## ⏰ 自动化验证

**第一个月 - 每6小时自动执行:**

| 时间 | 检查项 |
|------|--------|
| 00:00 | 验证自动触发、收到邮件 |
| 06:00 | 验证自动触发、收到邮件 |
| 08:00 | **主要发布时间**、验证邮件 |
| 12:00 | 验证自动触发、收到邮件 |
| 18:00 | 验证自动触发、收到邮件 |

**每次验证:**
- [ ] 自动触发成功
- [ ] 收到邮件
- [ ] 邮件内容为过去24小时的TOP新闻
- [ ] GitHub 更新

**30天后:** 运行清理脚本
```bash
bash infra/gcp/delete_intensive_schedule.sh
```

**如果失败:** 查看故障排查部分

---

## 🔧 快速故障排查

### 问题: 邮件未收到

```bash
# 检查密钥
gcloud secrets versions access latest --secret=gmail-username --project=deepdive-tracking
gcloud secrets versions access latest --secret=gmail-password --project=deepdive-tracking

# 检查垃圾邮件文件夹
# 检查 Gmail App Password 是否有效
```

### 问题: Scheduler 触发失败

```bash
# 查看错误日志
gcloud scheduler jobs logs deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking

# 重新创建任务
gcloud scheduler jobs delete deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking \
    --quiet

bash setup_cloud_scheduler.sh
```

### 问题: 数据采集失败

```bash
# 检查数据源
# 连接 Cloud SQL 并查询:
SELECT name, type, is_enabled FROM data_sources WHERE is_enabled = true;

# 确保至少有 3-5 个启用的数据源
```

---

## 📚 详细文档

完整文档: [docs/GCP_AUTOMATION_DEPLOYMENT.md](docs/GCP_AUTOMATION_DEPLOYMENT.md)

---

## ✨ 完成！

部署完成后，系统将:
- 每天 9:00 AM 自动采集、评分、发送邮件
- 每周日 10:00 AM 发送周报
- 邮件自动发送到: **hello.junjie.duan@gmail.com**

**无需任何手动操作！** 🎊
