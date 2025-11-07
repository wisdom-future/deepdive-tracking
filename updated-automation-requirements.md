# ✅ 更新的自动化需求配置完成

**日期:** 2025-11-07
**状态:** ✅ 代码完成，待部署
**目标:** 按新需求配置自动化发布

---

## 🎯 新需求总结

根据最新要求，已完成以下配置更新：

### 1. **过去24小时内的TOP新闻** ✅
- **修改文件:** `scripts/publish/send_top_news_email.py`
- **实现:**
  - 添加时间过滤：`RawNews.collected_at >= datetime.now() - timedelta(hours=24)`
  - 只查询最近24小时内采集的新闻
  - 从中选择TOP 15条（之前是所有时间的TOP 10）

### 2. **早上8点发布** ✅
- **修改文件:** `infra/gcp/setup_cloud_scheduler.sh`
- **实现:**
  - 从 `0 9 * * *` 改为 `0 8 * * *`
  - 每天早上8:00 AM Beijing Time 发布

### 3. **第一个月每6小时发布** ✅
- **新增调度任务:** `deepdive-intensive-workflow`
- **时间:** 0:00, 6:00, 12:00, 18:00 Beijing Time
- **Cron:** `0 0,6,12,18 * * *`
- **注意:** 这是临时任务，30天后需删除

### 4. **支持手动触发** ✅
- **新增脚本:** `infra/gcp/trigger_workflow_manually.sh`
- **功能:**
  - 交互式菜单选择
  - 支持通过Cloud Scheduler触发（推荐）
  - 支持直接API调用
  - 支持查看工作流状态

---

## 📋 完整调度配置

部署后将创建以下3个调度任务：

### 任务1: 每日工作流
```bash
Job Name: deepdive-daily-workflow
Schedule: 0 8 * * * (每天 8:00 AM Beijing)
Endpoint: POST /api/v1/workflows/daily
Purpose:  日常发布，每天早上8点
Status:   PERMANENT (永久)
```

### 任务2: 每周报告
```bash
Job Name: deepdive-weekly-report
Schedule: 0 10 * * 0 (每周日 10:00 AM Beijing)
Endpoint: POST /api/v1/workflows/weekly
Purpose:  周报发布
Status:   PERMANENT (永久)
```

### 任务3: 密集调度（第一个月）
```bash
Job Name: deepdive-intensive-workflow
Schedule: 0 0,6,12,18 * * * (每6小时)
Endpoint: POST /api/v1/workflows/daily
Purpose:  第一个月密集发布，提高曝光
Status:   TEMPORARY (30天后删除)
Times:    00:00, 06:00, 12:00, 18:00 Beijing Time
```

---

## 🔄 执行流程

### 自动执行（每6小时）

```
触发时间: 00:00, 06:00, 12:00, 18:00
    ↓
Cloud Scheduler → POST /api/v1/workflows/daily
    ↓
Cloud Run 执行 daily_complete_workflow.py
    ↓
Step 1: 采集最新新闻
    ↓
Step 2: AI评分
    ↓
Step 3: 查询过去24小时的TOP 15条
    ↓
Step 4: 发送邮件到 hello.junjie.duan@gmail.com
    ↓
Step 5: 发布到 GitHub Pages
```

### 手动触发

```bash
# 使用交互式脚本（推荐）
bash infra/gcp/trigger_workflow_manually.sh

# 或直接使用 gcloud 命令
gcloud scheduler jobs run deepdive-daily-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking
```

---

## 📂 新增/修改的文件

### 修改的文件
```
scripts/publish/send_top_news_email.py     [修改] 添加24小时过滤
infra/gcp/setup_cloud_scheduler.sh         [修改] 8:00发布 + 每6小时调度
```

### 新增的文件
```
infra/gcp/trigger_workflow_manually.sh     [新增] 手动触发脚本
infra/gcp/delete_intensive_schedule.sh     [新增] 30天后清理脚本
UPDATED_AUTOMATION_REQUIREMENTS.md         [新增] 本文档
```

---

## 🚀 部署步骤

### 1. 提交代码
```bash
git add .
git commit -m "feat(automation): update scheduling requirements

- Change daily workflow to 8:00 AM Beijing Time
- Add intensive schedule for first month (every 6 hours)
- Filter news to last 24 hours only (TOP 15)
- Add manual trigger script with interactive menu
- Add cleanup script for intensive schedule

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin main
```

### 2. 部署到 Cloud Run
```bash
bash infra/gcp/deploy.sh
# 或
gcloud run deploy deepdive-tracking \
    --source . \
    --region=asia-east1 \
    --project=deepdive-tracking
```

### 3. 配置 Cloud Scheduler
```bash
cd infra/gcp
bash setup_cloud_scheduler.sh
```

**预期输出:**
```
✓ Daily job created: deepdive-daily-workflow
  Schedule: Every day at 8:00 AM Beijing Time

✓ Weekly job created: deepdive-weekly-report
  Schedule: Every Sunday at 10:00 AM Beijing Time

✓ Intensive job created: deepdive-intensive-workflow
  Schedule: Every 6 hours (0:00, 6:00, 12:00, 18:00) Beijing Time
  NOTE: This is a TEMPORARY job for first month
```

### 4. 测试手动触发
```bash
bash infra/gcp/trigger_workflow_manually.sh

# 选择选项 1 (Via Cloud Scheduler)
# 选择选项 1 (deepdive-daily-workflow)
```

### 5. 验证邮件
- 检查: hello.junjie.duan@gmail.com
- 主题: "DeepDive Tracking - 今日AI动态精选 (YYYY-MM-DD)"
- 内容: TOP 15 条过去24小时内的新闻

---

## ⏰ 发布时间表

### 第一个月（密集模式）

| 时间 | 任务 | 频率 | 说明 |
|------|------|------|------|
| 00:00 | Intensive | 每天 | 深夜发布 |
| 06:00 | Intensive | 每天 | 清晨发布 |
| 08:00 | Daily | 每天 | **主要发布时间** |
| 12:00 | Intensive | 每天 | 午间发布 |
| 18:00 | Intensive | 每天 | 傍晚发布 |
| 周日 10:00 | Weekly | 每周 | 周报 |

**总计:** 每天5次邮件（工作日），周日6次

### 30天后（正常模式）

删除 intensive schedule 后：

| 时间 | 任务 | 频率 | 说明 |
|------|------|------|------|
| 08:00 | Daily | 每天 | 每日发布 |
| 周日 10:00 | Weekly | 每周 | 周报 |

**总计:** 每天1次邮件（工作日），周日2次

---

## 🛠️ 30天后的清理

### 自动提醒

30天后，执行以下操作：

```bash
# 方法1: 使用清理脚本
bash infra/gcp/delete_intensive_schedule.sh

# 方法2: 直接删除
gcloud scheduler jobs delete deepdive-intensive-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking
```

### 验证清理

```bash
# 查看剩余任务（应该只有2个）
gcloud scheduler jobs list \
    --location=asia-east1 \
    --project=deepdive-tracking

# 应该看到:
# - deepdive-daily-workflow
# - deepdive-weekly-report
```

---

## 🧪 测试清单

### 部署后立即测试

- [ ] Cloud Run 服务运行正常
- [ ] API endpoints 可访问 (`/health`, `/api/v1/workflows/status`)
- [ ] 3个 Cloud Scheduler 任务已创建
- [ ] 手动触发成功

### 功能测试

- [ ] 手动触发脚本可用
- [ ] 查询到过去24小时内的新闻
- [ ] 邮件包含15条新闻（如果有足够数据）
- [ ] 邮件发送到 hello.junjie.duan@gmail.com
- [ ] GitHub Pages 更新

### 时间验证

- [ ] 等待下一个6小时边界（0:00, 6:00, 12:00, 18:00）
- [ ] 验证自动触发成功
- [ ] 检查收到邮件
- [ ] 确认邮件内容为过去24小时的TOP新闻

---

## 📊 监控要点

### 每日检查

1. **邮件接收:**
   - 第一个月：每天收到5封邮件
   - 30天后：每天收到1封邮件（8:00 AM）

2. **新闻时效性:**
   - 所有新闻都是过去24小时内的
   - 没有重复的旧新闻

3. **邮件数量:**
   - 每封邮件包含10-15条新闻
   - 如果少于10条，检查数据采集

### 每周检查

1. **Cloud Scheduler 执行历史:**
```bash
gcloud scheduler jobs describe deepdive-intensive-workflow \
    --location=asia-east1 \
    --project=deepdive-tracking
```

2. **Cloud Run 日志:**
```bash
gcloud run services logs read deepdive-tracking \
    --region=asia-east1 \
    --limit=100 | grep -i error
```

3. **数据库状态:**
   - 检查过去24小时内采集的新闻数量
   - 检查AI评分完成率

---

## 🎊 完成！

### 已实现的功能

✅ **过去24小时TOP新闻** - 只发送最新内容
✅ **早上8点发布** - 最佳阅读时间
✅ **第一个月每6小时** - 密集曝光
✅ **手动触发支持** - 随时可测试

### 预期效果

**第一个月:**
- 每天5次发布（0:00, 6:00, 8:00, 12:00, 18:00）
- 每周35次发布
- 高频曝光，建立用户习惯

**30天后:**
- 每天1次发布（8:00）
- 每周7次发布
- 正常运营模式

### 下一步

1. **立即:** 按上述步骤部署
2. **今天:** 手动测试触发
3. **明天:** 验证首次自动发布（8:00 AM）
4. **30天后:** 运行清理脚本删除密集调度

---

**🚀 准备部署！所有代码已更新完毕。**

参考快速部署清单: `DEPLOYMENT_CHECKLIST.md`
