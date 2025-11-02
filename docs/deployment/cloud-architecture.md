# 云端部署架构设计

**状态：** 架构设计完成 (GCP)
**目标：** 实现云端自闭环的自动化系统
**成本策略：** 免费存储 + 付费 AI API
**平台：** Google Cloud Platform (GCP)

---

## 📊 当前状态

### 本地开发环境 (✅ 完成)
- ✅ SQLite 数据库 (本地)
- ✅ Python Flask/FastAPI 后端
- ✅ Redis (内存缓存)
- ✅ Celery (任务队列)
- ✅ 手动执行的脚本
- ✅ HTML 内容清理

### 待解决问题
- ⏳ 数据存储在本地 → 迁移到 Cloud SQL
- ⏳ 无法云端执行 → 部署到 Cloud Functions
- ⏳ 无法定时自动运行 → 配置 Cloud Scheduler
- ⏳ 无法扩展性 → 使用云端托管服务
- ⏳ 无法多地域部署 → 全球 CDN 加速

---

## 🏗️ 云端架构方案

### 平台选择：GCP (Google Cloud Platform)

**选择原因：**
1. ✅ 免费额度最慷慨 (永久免费服务)
2. ✅ 数据库免费配额最高 (3.75GB RAM)
3. ✅ 全球部署支持，延迟低
4. ✅ Secret Manager 密钥管理 (无限免费)

**替代方案：**
- AWS (国际覆盖但免费额度较少)
- 阿里云 (国内但需要备案)

---

## 📐 完整架构设计

### 数据流

```
RSS 源 → Cloud Functions (采集) → Cloud SQL
               ↓
           Pub/Sub (消息)
               ↓
Cloud Functions (评分) → OpenAI API
               ↓
           Pub/Sub (消息)
               ↓
Cloud Functions (审核) → Web UI
               ↓
           Pub/Sub (消息)
               ↓
Cloud Functions (发布) → WeChat / 小红书 / Website
               ↓
           Cloud Logging (日志)
```

---

## ⏰ 自闭环工作流

### 采集阶段 (08:00)
- Cloud Scheduler 触发
- collection_fn 启动 (512MB, 900s 超时)
- 从 15 个 RSS 源爬取数据
- HTML 清理和去重 (Redis 检查)
- 保存到 Cloud SQL
- 发送消息到 Pub/Sub

### 评分阶段 (09:00 自动触发)
- Pub/Sub 消息触发
- scoring_fn 并发运行 (5-10 并发)
- 调用 OpenAI API GPT-4o
- 计算成本并记录
- 保存评分结果到 Cloud SQL
- 发送消息到 Pub/Sub

### 审核阶段 (14:00)
- Cloud Scheduler 触发
- review_fn 启动
- 查询待审核的文章
- 人工通过 Web UI 审核
- 调整评分/分类
- 标记为 published_ready

### 发布阶段 (18:00)
- Cloud Scheduler 触发
- publish_fn 启动 (3 并发)
- 查询 published_ready 的文章
- 生成 Markdown/HTML 格式
- 发送到 WeChat API
- 发送到小红书 API
- 更新 Website
- 更新状态为 published

---

## 💾 存储方案

### 主数据库: Cloud SQL (PostgreSQL)
- **配置:** 0.6 vCPU, 3.75GB RAM (永久免费)
- **存储:** 10GB (初期足够)
- **备份:** 自动每日备份 (7天保留)
- **成本:** ¥0 (开发) / ¥500 (生产 HA)

### 缓存层: Memorystore (Redis)
- **配置:** 1GB (开发版永久免费)
- **用途:** 采集去重、API 结果缓存、队列
- **成本:** ¥0 (开发) / ¥100 (生产)

### 消息队列: Pub/Sub
- **配置:** 100GB/月 (永久免费)
- **用途:** 异步处理、事件驱动
- **成本:** ¥0

### 日志存储: Cloud Logging
- **配置:** 50GB/月 (永久免费)
- **用途:** 日志聚合、追踪分析
- **成本:** ¥0

### 对象存储: Cloud Storage
- **配置:** 1GB/月 (永久免费)
- **用途:** 数据库备份、静态资源
- **成本:** ¥0

### 备份数据库: Firestore
- **配置:** 1GB (永久免费)
- **用途:** 文档存储、快速查询
- **成本:** ¥0

---

## 🔐 密钥管理

使用 GCP Secret Manager 管理所有 API 密钥：

```python
from google.cloud import secretmanager

def get_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

**管理的密钥：**
- `openai-api-key` - OpenAI GPT-4o
- `wechat-app-secret` - 微信 API
- `cloud-sql-password` - 数据库密码
- `redis-password` - Redis 密码

---

## ⚙️ 计算资源

### Cloud Functions

**采集函数 (collection_fn)**
- 触发: Cloud Scheduler 每日 08:00
- 内存: 512MB
- 超时: 900 秒
- 月执行: 30 次
- 成本: ¥0 (200万次免费)

**评分函数 (scoring_fn)**
- 触发: Pub/Sub 消息
- 内存: 512MB
- 超时: 600 秒
- 月执行: 3,600 次 (118篇 × 30天)
- 并发: 5-10
- 成本: ¥0 (200万次免费)

**审核函数 (review_fn)**
- 触发: Cloud Scheduler 每日 14:00
- 内存: 256MB
- 超时: 300 秒
- 月执行: 30 次
- 成本: ¥0

**发布函数 (publish_fn)**
- 触发: Cloud Scheduler 每日 18:00
- 内存: 512MB
- 超时: 300 秒
- 月执行: 30 次
- 并发: 3
- 成本: ¥0

---

## 📊 总成本估算

### 初期方案 (仅免费层)
| 服务 | 配置 | 成本 |
|-----|------|------|
| Cloud SQL | 0.6 vCPU (免费) | ¥0 |
| Memorystore | 1GB (免费) | ¥0 |
| Cloud Functions | 200万次 (免费) | ¥0 |
| Pub/Sub | 100GB/月 (免费) | ¥0 |
| Cloud Logging | 50GB/月 (免费) | ¥0 |
| Cloud Storage | 1GB/月 (免费) | ¥0 |
| Secret Manager | 无限 (免费) | ¥0 |
| OpenAI API | GPT-4o 3,600次 | ¥40-100 |
| **总计** | | **¥40-100** |

### 生产轻量级方案
| 服务 | 配置 | 成本 |
|-----|------|------|
| Cloud SQL HA | 2 vCPU | ¥500 |
| Memorystore | 2GB | ¥100 |
| Cloud Functions | 50GB-s (超额) | ¥5 |
| Cloud CDN | 1TB | ¥100 |
| OpenAI API | GPT-4o 5,000次 | ¥150 |
| **总计** | | **¥855** |

---

## 🔄 数据库迁移

### SQLite → Cloud SQL

**步骤 1: 创建 Cloud SQL 实例**
```bash
gcloud sql instances create deepdive-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

**步骤 2: 迁移数据**
```python
# 使用 SQLAlchemy + Alembic
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**步骤 3: 更新连接**
```python
# 开发环境
DATABASE_URL = "sqlite:///./data/db/deepdive.db"

# 生产环境
DATABASE_URL = os.getenv("CLOUDSQL_CONNECTION_NAME")
```

---

## 📋 实施计划

### Phase 1: 本地完整功能 (进行中)
- [ ] 完成采集、评分、审核、发布功能
- [ ] 本地 SQLite 数据库
- [ ] 单元测试覆盖率 > 85%
- [ ] 所有脚本可手动执行

### Phase 2: 云端准备 (待启动)
- [ ] 创建 GCP 项目
- [ ] 创建 Cloud SQL PostgreSQL
- [ ] 创建 Memorystore Redis
- [ ] 创建 Secret Manager 密钥

### Phase 3: 云端部署 (待启动)
- [ ] 部署 4 个 Cloud Functions
- [ ] 配置 Cloud Scheduler
- [ ] 配置 Pub/Sub 主题
- [ ] 端到端流程测试

### Phase 4: 自动化监控 (待启动)
- [ ] 配置 Cloud Monitoring 告警
- [ ] 配置日志聚合
- [ ] 创建监控仪表板
- [ ] 成本监控配置

### Phase 5: 优化扩展 (待启动)
- [ ] 性能优化
- [ ] 成本优化
- [ ] 功能扩展
- [ ] 多地域部署

---

**当前阶段：** Phase 1 进行中
**下一步：** 完成所有本地功能实现

