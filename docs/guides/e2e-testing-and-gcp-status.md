# E2E测试和GCP部署状态报告

## 📋 执行摘要

### 本地E2E测试命令
| 命令 | 说明 | 状态 |
|------|------|------|
| `pytest tests/e2e/` | 运行所有E2E测试 | ⚠️ 需要数据库连接 |
| `python tests/e2e/test_complete_workflow.py 5` | 完整工作流测试(5篇文章) | ⚠️ API方法已变更 |
| `python tests/e2e/test_workflow_simple.py 5` | 简化工作流测试 | ⚠️ 需要数据库连接 |
| `python scripts/publish/send_top_news_email.py` | 邮件发布测试 | ⚠️ 需要数据库连接 |
| `python scripts/publish/send_top_ai_news_to_github.py` | GitHub发布测试 | ⚠️ 需要数据库连接 |

### GCP部署状态
| 组件 | 状态 | 说明 |
|------|------|------|
| **Cloud Run** | 🟢 已部署 | 应用程序运行在 `deepdive-tracking` 服务 |
| **Cloud SQL** | 🟢 已配置 | PostgreSQL 实例在 `asia-east1` 区域 |
| **部署脚本** | 🟢 可用 | 位于 `infra/gcp/deploy_to_cloud_run.sh` |
| **IAM角色** | 🟡 已配置 | Service account: `726493701291-compute@developer.gserviceaccount.com` |

---

## 🏠 本地环境设置

### 前置要求

```bash
# 1. Python 3.10+
python --version

# 2. PostgreSQL 本地运行
# Windows: 下载 PostgreSQL 14+ 或使用 WSL
# macOS: brew install postgresql
# Linux: apt-get install postgresql

# 3. 启动 PostgreSQL 服务
# Windows: Services > PostgreSQL > Start
# macOS/Linux: pg_ctl -D /usr/local/var/postgres start

# 4. 安装依赖
pip install -r requirements.txt
```

### 数据库初始化

```bash
# 本地创建数据库
createdb deepdive_db

# 创建用户
psql -U postgres -c "CREATE USER deepdive_user WITH PASSWORD 'deepdive_password';"

# 授予权限
psql -U postgres -c "ALTER DATABASE deepdive_db OWNER TO deepdive_user;"

# 验证连接
psql -h localhost -U deepdive_user -d deepdive_db -c "SELECT 1;"
```

---

## ✅ 本地E2E测试命令

### 1. 完整工作流测试

```bash
# 采集 → 评分 → 审核 → 发布 (完整流程)
python tests/e2e/test_complete_workflow.py 3

# 说明:
# - 参数 3 表示处理3篇文章
# - 输出包含采集、评分、审核、发布的详细统计
# - 需要OpenAI API配置
```

**预期输出:**
```
================================================================================
  DeepDive Tracking - 完整端到端工作流测试
================================================================================

[步骤 1] 采集 RSS 新闻 (Collection)
  采集完成: 3 篇文章 (耗时: 2.34秒)

[步骤 2] AI 评分 (Scoring)
  找到 3 篇待评分的文章
  [1/3] Article Title 1... ✓ (评分: 75)

[步骤 3] 自动审核 (Auto Review)
  ✓ 自动审核成功
    自动批准: 2

[步骤 4] 微信发布 (WeChat Publishing)
  ✓ WeChat 发布完成
    成功发布: 2 篇
```

### 2. 简化工作流测试 (仅评分和发布)

```bash
# 使用现有采集的数据，跳过采集步骤
python tests/e2e/test_workflow_simple.py 5

# 说明:
# - 只测试评分、审核、发布
# - 更快速，适合开发阶段
```

### 3. 单个模块测试

```bash
# 只测试邮件发布
python scripts/publish/send_top_news_email.py

# 只测试 GitHub 发布
python scripts/publish/send_top_ai_news_to_github.py

# 运行所有 pytest 测试
pytest tests/ -v --cov=src --cov-fail-under=85
```

### 4. 快速API测试

```bash
# 启动本地服务器
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 在另一个终端测试API端点
curl http://localhost:8000/health

# 初始化数据库
curl -X POST http://localhost:8000/init-db

# 运行测试邮件发布
curl -X POST http://localhost:8000/test-email

# 查看数据库诊断
curl http://localhost:8000/diagnose/database
```

---

## 🚀 GCP部署状态

### 当前部署配置

**项目信息:**
- Project ID: `deepdive-engine`
- Region: `asia-east1`
- Service Name: `deepdive-tracking`
- Service Account: `726493701291-compute@developer.gserviceaccount.com`

**资源配置:**
- Memory: 1 Gi
- CPU: 1
- Timeout: 900秒 (15分钟)
- 允许未认证请求: 是

### Cloud Run 服务状态

```bash
# 查看服务状态
gcloud run services describe deepdive-tracking --region asia-east1

# 查看最近日志
gcloud run services logs read deepdive-tracking --region asia-east1 --limit 50

# 查看部署历史
gcloud run services list-revisions deepdive-tracking --region asia-east1
```

### Cloud SQL 数据库配置

**连接信息:**
- 类型: PostgreSQL 15
- 实例连接名: `deepdive-engine:asia-east1:deepdive-db`
- 数据库名: `deepdive_db`
- 用户: `deepdive_user`
- 端口: 5432

**在Cloud Run中的连接方式:**
```
postgresql://deepdive_user:deepdive_password@/deepdive_db
(使用Unix socket via Cloud SQL Connector)
```

### 部署命令

```bash
# 标准部署（完整构建）
./infra/gcp/deploy_to_cloud_run.sh

# 干运行模式（不实际部署，仅显示命令）
./infra/gcp/deploy_to_cloud_run.sh --dry-run

# 跳过构建，使用现有镜像
./infra/gcp/deploy_to_cloud_run.sh --skip-build

# 指定项目和区域
./infra/gcp/deploy_to_cloud_run.sh --project-id my-project --region us-central1
```

---

## 🔧 故障排除

### 本地数据库连接错误

**错误:** `connection refused at "localhost" port 5432`

**解决方案:**
```bash
# 1. 检查 PostgreSQL 是否运行
pg_isready -h localhost

# 2. 启动 PostgreSQL
# Windows: 在 Services 中启动 PostgreSQL 服务
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql

# 3. 验证 .env 数据库 URL
cat .env | grep DATABASE_URL

# 4. 测试连接
psql -h localhost -U deepdive_user -d deepdive_db -c "SELECT 1;"
```

### API 方法变更错误

**错误:** `'CollectionManager' has no attribute 'collect_from_all_sources'`

**说明:** E2E测试脚本引用的方法名已更改

**解决方案:** 更新E2E测试脚本以使用正确的方法名
```python
# 旧代码
collected_count = collection_manager.collect_from_all_sources()

# 新代码 (查看 CollectionManager 源码确认正确方法)
collected_count = collection_manager.collect()
```

### 编码错误 (Windows)

**错误:** `UnicodeEncodeError: 'gbk' codec can't encode character`

**解决方案:** 在Windows上使用UTF-8编码运行脚本
```bash
# 设置环境变量
set PYTHONIOENCODING=utf-8

# 或使用 Python 的 UTF-8模式
python -X utf8 scripts/publish/send_top_news_email.py
```

### GCP权限错误

**错误:** `Permission denied` 或 `Not authorized`

**解决方案:**
```bash
# 确认已登录
gcloud auth login

# 设置正确的项目
gcloud config set project deepdive-engine

# 检查权限
gcloud projects get-iam-policy deepdive-engine \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount/726493701291-compute@developer.gserviceaccount.com"
```

---

## 📊 环境变量配置

### 本地开发 (.env 文件)

```bash
# 必需的变量
DATABASE_URL=postgresql://deepdive_user:deepdive_password@localhost:5432/deepdive_db
OPENAI_API_KEY=sk-proj-...your_key...
SMTP_PASSWORD="your_gmail_app_password"
GITHUB_TOKEN=github_pat_...your_token...
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret

# 可选变量
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

### GCP Cloud Run

环境变量由 `deploy_to_cloud_run.sh` 脚本自动设置:
- `GOOGLE_CLOUD_PROJECT`
- `DATABASE_URL` (使用Cloud SQL Connector)
- `DEBUG=False`
- `LOG_LEVEL=INFO`

---

## 📈 CI/CD流程

### GitHub Actions工作流

项目已配置自动化部署:
1. 推送到main分支 → 运行测试
2. 测试通过 → 构建Docker镜像
3. 推送到GCR → 部署到Cloud Run

```bash
# 查看部署状态
gcloud run services describe deepdive-tracking --region asia-east1 --format='value(status.url)'
```

---

## 🎯 下一步行动

### 本地测试清单
- [ ] 启动本地PostgreSQL
- [ ] 配置.env文件
- [ ] 运行 `python tests/e2e/test_workflow_simple.py 3`
- [ ] 验证邮件发布功能
- [ ] 验证GitHub发布功能

### GCP部署清单
- [ ] 验证Cloud Run服务正在运行
- [ ] 检查Cloud SQL连接
- [ ] 查看服务日志
- [ ] 运行触发工作流API

### 生产环境清单
- [ ] 配置生产数据库凭证
- [ ] 设置日志监控
- [ ] 配置告警规则
- [ ] 建立备份计划

---

## 📞 常见问题

**Q: 如何从GCP Cloud Run触发工作流?**
```bash
curl -X POST https://deepdive-tracking-XXXXX.asia-east1.run.app/trigger-workflow
```

**Q: 如何查看Cloud SQL数据库中的数据?**
```bash
# 使用Cloud Console SQL编辑器或
gcloud sql connect deepdive-db --user=deepdive_user
```

**Q: 测试需要多少时间?**
- 完整工作流 (10篇文章): 2-5 分钟 (含OpenAI API调用)
- 简化工作流 (10篇文章): 30-60 秒
- 单元测试: 10-15 秒

---

**最后更新:** 2024-11-03
**维护者:** DeepDive Tracking 团队
