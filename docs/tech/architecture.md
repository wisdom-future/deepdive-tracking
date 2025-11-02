# DeepDive Tracking - 技术架构设计文档 v1.0

**文档类型：** 系统设计文档
**版本：** 1.0
**最后更新：** 2025-11-02
**设计者：** 架构团队
**审核者：** 待审核

---

## 目录

1. [系统概览](#系统概览)
2. [架构设计理念](#架构设计理念)
3. [系统总体架构](#系统总体架构)
4. [核心模块设计](#核心模块设计)
5. [数据流设计](#数据流设计)
6. [存储设计](#存储设计)
7. [缓存策略](#缓存策略)
8. [异步处理](#异步处理)
9. [可靠性设计](#可靠性设计)
10. [扩展性设计](#扩展性设计)
11. [安全设计](#安全设计)
12. [性能指标](#性能指标)
13. [部署架构](#部署架构)
14. [监控告警](#监控告警)

---

## 系统概览

### 系统定义

DeepDive Tracking 是一个**内容生产与分发系统**，核心目的是自动化采集AI资讯、AI智能评分、内容优化、多渠道发布。

### 系统规模预估

| 指标 | 数值 | 说明 |
|------|------|------|
| 日采集量 | 300-500条 | 50个信息源 |
| 日发布量 | 5-10条 | 精选内容 |
| 月活跃用户 | 500-10000+ | MVP到12月增长 |
| QPS | 10-50 | 初期低流量 |
| 月API成本 | ¥1500-4000 | OpenAI + Claude |
| 日数据存储 | 100-200MB | 原始数据 + 处理结果 |

---

## 架构设计理念

### 1. 分层架构（Layered Architecture）

```
┌─────────────────────────────────────────┐
│     表现层 (Presentation Layer)         │
│  - API接口 / 后台Web界面 / 推送接口    │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│     应用层 (Application Layer)          │
│  - 业务逻辑 / 工作流编排 / 规则引擎    │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│     服务层 (Service Layer)              │
│  - 数据采集 / AI处理 / 内容管理         │
│  - 发布分发 / 用户管理 / 统计分析      │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│     数据层 (Data Layer)                 │
│  - 数据库 / 缓存 / 消息队列 / 对象存储 │
└─────────────────────────────────────────┘
```

### 2. 设计原则

1. **高内聚，低耦合**
   - 各模块职责清晰，接口明确
   - 模块间通过消息队列和事件驱动

2. **可扩展性优先**
   - 采用插件式架构支持新信息源
   - AI模型可动态切换（OpenAI/Claude）
   - 发布渠道可灵活添加

3. **容错和降级**
   - API失败自动重试
   - 关键服务有备用方案
   - 非核心功能可灰度关闭

4. **成本优化**
   - 缓存优先，减少API调用
   - 批量处理，提升效率
   - 成本实时监控

---

## 系统总体架构

### 整体架构图

```
┌────────────────────────────────────────────────────────────────┐
│                    外部信息源                                   │
│  RSS | 爬虫 | Twitter/X | arXiv/GitHub | 官网API | 其他源      │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                   数据采集引擎                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ RSS爬虫 │ 网页爬虫 │ API客户端 │ 社交媒体监控 │ 去重过滤   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           消息队列 (RabbitMQ/Celery)                     │  │
│  │  raw_news_queue → processing_queue → review_queue        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                   AI处理引擎                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 评分模块 │ 分类模块 │ 专业摘要 │ 科普摘要 │ 关键词提取    │  │
│  │  (0-100) │ (8类别) │ (Claude) │ (OpenAI) │               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  cache (Redis) | cost_tracker | quality_metrics          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                   内容管理系统                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 审核队列 │ 编辑器 │ 模板管理 │ 版本管理 │ 发布队列       │  │
│  │(score≥70)│       │         │         │               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                   发布分发系统                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 微信API │ 小红书API │ Web发布 │ 邮件推送 │ RSS Feed      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 用户追踪 │ 统计分析 │ 反馈收集 │ 迭代优化               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                   数据存储层                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL │ Redis │ Elasticsearch │ S3/OSS │ 日志系统   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│                   后台管理系统                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Dashboard │ 源管理 │ 审核管理 │ Prompt管理 │ 数据分析    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 核心模块设计

### 1. 数据采集引擎（Data Collection Engine）

#### 架构图

```
┌─────────────────────────────────────────┐
│       信息源管理 (Source Manager)       │
│ - 源注册、启用禁用、优先级管理          │
│ - 失败重试、速率限制、健康检查          │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│      多源采集器 (Multi-Source Collector)│
│ ┌─────────────────────────────────────┐ │
│ │ RSS爬虫   | Scrapy爬虫 | API客户端  │ │
│ │ Twitter监听 | 邮件监听 | Webhook   │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│      数据清洗与去重 (Cleanup & Dedup)  │
│ - 格式化、编码转换、HTML清洁            │
│ - Simhash去重、URL规范化                │
│ - 元数据提取（发布时间、作者、链接）   │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│    存储与队列 (Storage & Queuing)       │
│ - 原始数据入库 (raw_news table)         │
│ - 发送至处理队列 (RabbitMQ)             │
│ - 成功确认后更新状态                    │
└─────────────────────────────────────────┘
```

#### 关键设计点

**1. 信息源管理**
```python
class DataSource:
    id: int
    name: str              # "OpenAI Blog"
    type: str              # "rss", "crawler", "api", "twitter"
    url: str               # 信息源地址
    priority: int          # 1-10，优先级
    refresh_interval: int  # 刷新间隔（分钟）
    is_enabled: bool
    headers: dict          # 自定义请求头
    params: dict           # 自定义参数
    created_at: datetime
    last_check_at: datetime
    last_error: str
    error_count: int
```

**2. 采集策略**
- RSS源：30分钟检查一次，提取标题、摘要、原链接
- 网页爬虫：60分钟检查一次，CSS选择器提取内容
- API：实时查询，带速率限制
- Twitter：30分钟检查一次，监听特定账户
- 去重：基于URL规范化 + Simhash算法

**3. 失败处理**
```
失败重试策略：
- 第1次失败：5分钟后重试
- 第2次失败：15分钟后重试
- 第3次失败：60分钟后重试
- 连续3次失败：告警 + 临时禁用
- 恢复机制：每天尝试重新启用
```

---

### 2. AI处理引擎（AI Processing Engine）

#### 架构图

```
┌─────────────────────────────────────────────────┐
│         AI任务分配器 (Task Router)              │
│ - 根据任务类型选择模型                          │
│ - 支持OpenAI / Claude / 本地模型                │
│ - 成本和性能自动优化                            │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│        并行处理池 (Processing Pool)             │
│ ┌──────────────────────────────────────────┐    │
│ │ 评分模块 (Scoring)      → OpenAI         │    │
│ │ 分类模块 (Classification) → OpenAI       │    │
│ │ 专业摘要 (Pro Summary)   → Claude        │    │
│ │ 科普摘要 (Sci Summary)   → OpenAI        │    │
│ │ 关键词提取 (Keywords)    → Claude        │    │
│ │ 技术标签 (Tech Tags)     → 规则引擎      │    │
│ └──────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────┐
│       缓存与结果管理 (Cache & Results)          │
│ - Redis缓存相同Prompt的结果                     │
│ - 成本追踪                                      │
│ - 质量评分                                      │
└─────────────────────────────────────────────────┘
```

#### 任务类型和模型选择

| 任务 | 输入 | 输出 | 推荐模型 | 成本 |
|------|------|------|--------|------|
| 评分 | 标题+摘要 | 0-100分 | GPT-4o mini | 低 |
| 分类 | 标题+内容 | 8个分类之一 | GPT-4o mini | 低 |
| 专业摘要 | 完整文章 | 200-300字 | Claude 3.5 Sonnet | 中 |
| 科普摘要 | 完整文章 | 200-300字 | GPT-4o | 中 |
| 关键词提取 | 标题+摘要 | 3-5个关键词 | Claude 3.5 Haiku | 低 |
| 中英对照 | 术语列表 | 对照表 | Claude 3.5 Haiku | 低 |

#### 评分逻辑

```
评分维度（总分100分）：
┌─ 重要性 (30分)
│  ├─ 是否涉及大公司动态 (OpenAI/Google/Meta等) +10
│  ├─ 是否涉及SOTA模型/算法 +10
│  ├─ 是否涉及关键技术路线 +10
│
├─ 时效性 (20分)
│  ├─ 发布时间最近 <24h +15
│  ├─ 发布时间 24-48h +10
│  ├─ 发布时间 >48h +5
│
├─ 专业深度 (20分)
│  ├─ 包含技术细节分析 +20
│  ├─ 包含高层总结 +10
│  ├─ 仅有标题/链接 +0
│
├─ 内容完整性 (15分)
│  ├─ 有完整内容 +15
│  ├─ 仅有摘要 +10
│  ├─ 仅有标题 +5
│
├─ 受众适配 (10分)
│  ├─ 与核心用户高度相关 +10
│  ├─ 中等相关性 +5
│  ├─ 低相关性 +0
│
└─ 质量评分 (5分)
   ├─ 来源可信度高 +5
   ├─ 来源中等 +3
   └─ 来源可信度低 +0

发布阈值：≥70分进入审核队列
```

#### Prompt模板管理

```
system_prompts/
├── scoring_system_prompt.txt      # 评分系统提示词
├── classification_system_prompt.txt # 分类系统提示词
├── pro_summary_system_prompt.txt   # 专业摘要系统提示词
├── sci_summary_system_prompt.txt   # 科普摘要系统提示词
└── user_prompts/
    ├── scoring_v1.txt
    ├── scoring_v2.txt (A/B测试)
    └── ...

版本控制：
- 每个Prompt有版本号
- 可A/B测试对比效果
- 定期迭代优化
```

---

### 3. 内容管理系统（CMS）

#### 审核队列设计

```
┌─────────────────────────────────┐
│    已处理内容 (score ≥70)       │
│ 等待人工审核                     │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│   人工审核决策                   │
│ ├─ 通过 → 编辑优化 → 待发布     │
│ ├─ 修改 → 编辑器 → 审核         │
│ └─ 拒绝 → 记录原因 → 学习反馈   │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  编辑优化                        │
│ - 修改摘要/标题                  │
│ - 调整标签/分类                  │
│ - 排版预览                       │
│ - 生成图片/引用                  │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  定时发布                        │
│ - 每日9点：微信快讯              │
│ - 每日18点：小红书              │
│ - 每周日20点：周报               │
└─────────────────────────────────┘
```

#### 内容模型

```python
class Content:
    id: int
    source_id: int              # raw_news关联
    title: str                  # 标题
    original_url: str           # 原文链接
    source_name: str            # 信息源名称

    # AI处理结果
    score: float                # 评分 0-100
    category: str               # 分类 (8类之一)
    keywords: list[str]         # 关键词

    # 双版本内容
    summary_pro: str            # 专业版摘要
    summary_sci: str            # 科普版摘要
    tech_terms: dict            # 术语对照

    # 编辑处理
    review_status: str          # pending/approved/rejected/modified
    reviewed_by: str            # 审核人
    reviewed_at: datetime
    editor_notes: str           # 编辑备注

    # 发布信息
    publish_status: str         # draft/published/archived
    published_at: datetime
    channels: list[str]         # [wechat, xiaohongshu, web]

    # 统计数据
    view_count: int
    like_count: int
    share_count: int
    nps_score: int              # 用户反馈

    created_at: datetime
    updated_at: datetime
```

---

### 4. 发布分发系统（Publishing System）

#### 多渠道发布

```
微信公众号 (WeChat Official Account)
├─ 每日快讯 (Daily Brief)
│  ├─ 今日头条 (1条深度)
│  ├─ Top 5 (5条精简)
│  └─ 一句话速览 (5-8条)
│
├─ 周报 (Weekly Report)
│  ├─ 本周概览
│  ├─ 深度解读 (2-3篇)
│  ├─ 数据看板
│  └─ 下周预告
│
└─ 深度文章 (Occasional)

小红书 (Xiaohongshu)
├─ 图文卡片 (Daily 1-2)
│  ├─ 视觉化封面
│  ├─ 3图内容
│  └─ 话题标签
│
└─ 知识系列

Web平台 (Future)
├─ 首页时间线
├─ 分类筛选
├─ 搜索功能
└─ 历史归档

邮件推送 (Future)
├─ 每日摘要
├─ 周报完整版
└─ 自定义订阅
```

#### 发布流程

```python
class PublishingTask:
    id: int
    content_ids: list[int]          # 待发布内容
    schedule_time: datetime         # 定时发布时间
    channels: list[str]             # 发布渠道
    templates: dict                 # 渠道专用模板

    # 执行追踪
    status: str                     # pending/running/completed/failed
    executed_at: datetime
    results: dict                   # {channel: {success, error, url}}

    # 回滚机制
    can_rollback: bool
    rollback_deadline: datetime
```

---

## 数据流设计

### 完整数据流

```
时间轴 (Timeline):

T+0: 数据采集
└─ 50个信息源 → 300-500条新闻 → raw_news表

T+0~T+5分钟: AI处理（并行）
├─ 评分 (30s/条，平行100条)
├─ 分类 (20s/条)
├─ 关键词提取 (15s/条)
├─ 专业摘要 (45s/条)
└─ 科普摘要 (45s/条)

T+5~T+20分钟: 内容审核
└─ score ≥70的内容 → 审核队列 → 人工审核 (可并行)

T+20~T+60分钟: 编辑优化
└─ 通过的内容 → 编辑器优化 → 最终审核

T+8:45（早上）: 微信发布
└─ 每日快讯按模板生成 → 微信API → 9:00发布

T+17:45（下午）: 小红书发布
└─ 图文卡片生成 → 小红书API → 18:00发布

T+19:45（周日晚）: 周报发布
└─ 周报内容聚合 → 微信API → 20:00发布
```

### 关键指标计算

```
实时计算（Redis）:
- 日采集量
- 日处理量
- 通过率（AI评分70+的比例）
- 人工审核率（需要人工干预的比例）
- 发布延迟（从采集到发布的时间）

定时计算（每小时）:
- 成本统计（API调用费用）
- 质量评分（通过率、用户反馈）
- 系统健康度（各组件可用性）

离线计算（每天/周）:
- 用户参与度 (DAU/WAU)
- 内容质量分析
- 竞品监控
- 趋势分析
```

---

## 存储设计

### 数据库Schema

#### 核心表结构

```sql
-- 信息源管理
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- rss, crawler, api, twitter
    url VARCHAR(2048),
    priority INT DEFAULT 5,
    refresh_interval INT DEFAULT 30,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_check_at TIMESTAMP,
    last_error TEXT,
    error_count INT DEFAULT 0
);
CREATE INDEX idx_sources_enabled ON data_sources(is_enabled, priority);

-- 原始新闻
CREATE TABLE raw_news (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL REFERENCES data_sources(id),
    title VARCHAR(255) NOT NULL,
    url VARCHAR(2048) UNIQUE NOT NULL,
    content TEXT,
    published_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash CHAR(32) NOT NULL UNIQUE,  -- Simhash
    status VARCHAR(50) DEFAULT 'raw',  -- raw, processing, processed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES data_sources(id)
);
CREATE INDEX idx_raw_news_status ON raw_news(status, created_at);
CREATE INDEX idx_raw_news_source ON raw_news(source_id, published_at);

-- 处理结果
CREATE TABLE processed_news (
    id SERIAL PRIMARY KEY,
    raw_news_id INT NOT NULL REFERENCES raw_news(id),

    -- AI评分结果
    score FLOAT NOT NULL,
    category VARCHAR(50) NOT NULL,
    keywords TEXT[],  -- JSON array

    -- 双版本内容
    summary_pro TEXT NOT NULL,        -- 专业版
    summary_sci TEXT NOT NULL,        -- 科普版
    tech_terms JSONB,                 -- 术语对照

    -- 元数据
    word_count INT,
    readability_score FLOAT,

    -- 处理信息
    ai_model VARCHAR(100),
    processing_time_ms INT,
    cost FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raw_news_id) REFERENCES raw_news(id)
);
CREATE INDEX idx_processed_news_score ON processed_news(score DESC);
CREATE INDEX idx_processed_news_category ON processed_news(category);

-- 内容审核
CREATE TABLE content_review (
    id SERIAL PRIMARY KEY,
    processed_news_id INT NOT NULL REFERENCES processed_news(id),

    -- 审核状态
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, modified
    review_notes TEXT,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,

    -- 编辑修改
    title_edited VARCHAR(255),
    summary_pro_edited TEXT,
    summary_sci_edited TEXT,
    editor_notes TEXT,
    edited_by VARCHAR(255),
    edited_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processed_news_id) REFERENCES processed_news(id)
);
CREATE INDEX idx_review_status ON content_review(status);

-- 已发布内容
CREATE TABLE published_content (
    id SERIAL PRIMARY KEY,
    processed_news_id INT NOT NULL REFERENCES processed_news(id),
    content_review_id INT REFERENCES content_review(id),

    -- 发布信息
    publish_status VARCHAR(50) DEFAULT 'draft',  -- draft, published, archived
    channels TEXT[],  -- {wechat, xiaohongshu, web}
    published_at TIMESTAMP,

    -- 渠道特定URL
    wechat_url VARCHAR(2048),
    xiaohongshu_url VARCHAR(2048),
    web_url VARCHAR(2048),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processed_news_id) REFERENCES processed_news(id),
    FOREIGN KEY (content_review_id) REFERENCES content_review(id)
);

-- 用户互动与统计
CREATE TABLE content_stats (
    id SERIAL PRIMARY KEY,
    published_content_id INT NOT NULL REFERENCES published_content(id),

    -- 渠道统计
    channel VARCHAR(50),
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    completion_rate FLOAT,  -- 完成率

    -- 用户反馈
    nps_score INT,  -- Net Promoter Score
    feedback_count INT DEFAULT 0,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (published_content_id) REFERENCES published_content(id)
);
CREATE INDEX idx_stats_channel ON content_stats(channel);

-- 定时发布任务
CREATE TABLE publishing_schedules (
    id SERIAL PRIMARY KEY,
    schedule_type VARCHAR(50) NOT NULL,  -- daily_brief, weekly_report, xiaohongshu
    content_ids INT[],  -- JSON array of content IDs

    -- 执行信息
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed

    -- 结果追踪
    result_json JSONB,  -- {wechat: {success, msg_id}, xiaohongshu: {...}}
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_schedules_time ON publishing_schedules(scheduled_at, status);
```

#### 数据库设计原则

1. **规范化设计**
   - 避免数据冗余
   - 通过关联表管理关系

2. **性能优化**
   - 为常用查询字段建立索引
   - 分区大表（按时间）
   - 归档旧数据

3. **可审计性**
   - 所有表包含 created_at, updated_at
   - 记录操作人员和修改时间

---

## 缓存策略

### Redis缓存分层

```
Layer 1: 热数据缓存 (1小时 TTL)
├─ processed_news:{id} → 处理结果
├─ daily_brief:{date} → 每日快讯内容
└─ weekly_report:{week} → 周报内容

Layer 2: 中等频率数据 (1天 TTL)
├─ source_health:{source_id} → 信息源健康状态
├─ ai_model_cost:{date} → 每日AI成本
└─ category_stats:{date} → 分类统计

Layer 3: 低频访问数据 (7天 TTL)
├─ user_feedback:{content_id} → 用户反馈汇总
├─ content_quality:{month} → 月度质量分析
└─ publication_stats:{month} → 月度发布统计

Cache Keys示例:
raw_news:processing_queue → 处理队列内容ID列表
scheduled_tasks:pending → 待执行的定时任务
ai_prompt:scoring:v2 → Prompt版本管理
```

### 缓存失效策略

```
1. 主动失效 (Active Invalidation)
   - 内容发布时清除相关缓存
   - Prompt更新时清除所有AI缓存
   - 数据源配置变更时清除统计缓存

2. 被动失效 (Passive Invalidation)
   - 定时清理过期数据（每小时）
   - TTL自动过期

3. 双写一致性 (Write Through)
   - 更新DB同时更新Cache
   - 失败时Cache和DB保持一致性
```

---

## 异步处理

### 任务队列设计

```
任务队列架构 (使用 Celery + RabbitMQ):

┌──────────────────────────────────────┐
│        数据采集任务                   │
│ celery_queue_collection               │
│ 优先级: 高 | 并发: 10                 │
│ 重试: 3次 | 超时: 5分钟               │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        AI处理任务                     │
│ celery_queue_ai_processing            │
│ 优先级: 中 | 并发: 20                 │
│ 重试: 2次 | 超时: 2分钟               │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        内容发布任务                   │
│ celery_queue_publishing               │
│ 优先级: 中 | 并发: 5                  │
│ 重试: 3次 | 超时: 10分钟              │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│        数据分析任务                   │
│ celery_queue_analytics                │
│ 优先级: 低 | 并次: 2                  │
│ 重试: 1次 | 超时: 30分钟              │
└──────────────────────────────────────┘
```

### 定时任务

```
Celery Beat 定时任务配置:

每30分钟:
├─ 执行所有enabled的RSS爬虫任务
├─ 检查所有API数据源
└─ 更新信息源健康状态

每小时:
├─ 清理过期的缓存
├─ 统计AI成本
├─ 更新实时指标

每天 8:45:
└─ 准备每日快讯 → 9:00发送

每天 17:45:
└─ 准备小红书内容 → 18:00发送

每周日 19:45:
└─ 生成周报 → 20:00发送

每天 0:00:
├─ 生成日报表
├─ 数据备份
└─ 日志归档
```

---

## 可靠性设计

### 高可用设计

```
1. 数据库高可用
   ├─ 主从复制 (PostgreSQL Replication)
   ├─ 自动故障转移
   └─ 定期备份 (每6小时)

2. API超时和重试
   ├─ 超时设置: OpenAI=30s, Claude=30s, 其他API=10s
   ├─ 指数退避重试: 1s → 2s → 4s → 8s → abort
   ├─ 熔断器: 连续失败5次自动禁用

3. 消息队列可靠性
   ├─ RabbitMQ持久化配置
   ├─ 消息确认机制 (ack)
   ├─ 死信队列处理失败任务

4. 信息源多源备份
   ├─ 同类信息源备用 (多个RSS源)
   ├─ 关键信息源人工检查
   └─ 故障自动转移

5. 缓存降级
   ├─ Redis宕机时使用数据库查询
   ├─ 性能下降但服务可用
```

### 数据一致性保证

```
1. 事务设计
   ├─ 原始数据入库 ✓
   ├─ 处理结果入库 ✓
   ├─ 发布信息更新 ✓
   └─ 如任一步失败，记录错误重试

2. 幂等性设计
   ├─ 每条news有唯一hash
   ├─ 去重前置，避免重复处理
   ├─ 发布任务追踪，防止重复发送

3. 审计日志
   ├─ 所有数据变更记录操作人
   ├─ 支持数据回滚
   ├─ 完整的操作链路
```

---

## 扩展性设计

### 水平扩展

```
1. 无状态服务设计
   └─ API Server 可横向扩展 (Nginx负载均衡)

2. 消息队列扩展
   └─ RabbitMQ集群部署

3. 缓存扩展
   └─ Redis集群/Sentinel

4. 数据库扩展
   └─ 读写分离，从库用于查询分析

5. 存储扩展
   └─ S3/OSS对象存储自动扩展
```

### 功能扩展

```
1. 插件式信息源框架
   ├─ 定义统一的Source接口
   ├─ 新信息源 = 实现接口
   └─ 无需修改核心代码

2. AI模型扩展
   ├─ 智能路由可支持多个模型
   ├─ 成本和性能自动优化
   └─ 支持本地模型集成

3. 发布渠道扩展
   ├─ 定义发布接口
   ├─ 添加新渠道 (如Telegram, Slack)
   └─ 模板自适应

4. 内容处理扩展
   ├─ 支持添加新的分析维度
   ├─ 支持用户自定义规则
   └─ 支持插件式处理流程
```

---

## 安全设计

### API安全

```
1. 认证与授权
   ├─ Admin后台: JWT Token + 角色权限
   ├─ 内部API: 签名验证 (HMAC-SHA256)
   ├─ 第三方API: OAuth2认证

2. 请求限流
   ├─ IP限流: 100 req/min
   ├─ 用户限流: 1000 req/day
   ├─ 分层限流: 优先级高的请求优先

3. 数据加密
   ├─ 传输层: HTTPS + TLS 1.3
   ├─ 存储层: 敏感字段加密 (AES-256)
   ├─ API密钥管理: 密钥库加密存储
```

### 数据安全

```
1. 访问控制
   ├─ 最小权限原则 (Least Privilege)
   ├─ 数据库账户分级
   ├─ 操作审计日志

2. 隐私保护
   ├─ 用户数据加密存储
   ├─ PII数据脱敏
   ├─ GDPR合规

3. 备份与恢复
   ├─ 多地域备份
   ├─ 定期恢复演练
   ├─ RPO: 6小时, RTO: 1小时
```

### 内容安全

```
1. 敏感词过滤
   ├─ 发布前自动检查
   ├─ 涉及政策/法律术语标注
   ├─ 定期更新黑名单

2. 版权保护
   ├─ 检查来源有效性
   ├─ 标注出处
   ├─ 不直接复制原文

3. 恶意内容检测
   ├─ 垃圾信息检测
   ├─ 虚假信息识别
   ├─ 异常行为监控
```

---

## 性能指标

### 系统SLA目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 可用性 (Availability) | >99.5% | 每月允许 3.6小时宕机 |
| 采集延迟 (Collection Latency) | <5分钟 | 新闻发布到采集 |
| 处理延迟 (Processing Latency) | <20分钟 | 采集到AI处理完成 |
| 发布延迟 (Publishing Latency) | <1小时 | 内容审核到发布 |
| API响应时间 (Response Time) | <2s | 95%请求 |
| 数据库查询 (Query Response) | <500ms | 95%查询 |
| 缓存命中率 (Cache Hit Rate) | >80% | 减少数据库压力 |

### 成本指标

| 项目 | 预算 | 说明 |
|------|------|------|
| OpenAI API | ¥1000-2000/月 | 评分、分类、科普摘要 |
| Claude API | ¥500-800/月 | 专业摘要、深度分析 |
| 服务器 | ¥300-500/月 | 2核4G起步 |
| 数据库/缓存 | ¥200-300/月 | 托管服务 |
| 存储 | ¥100-200/月 | S3/OSS |
| 其他 (DNS/CDN) | ¥100/月 | 辅助服务 |
| **总计** | **¥2300-3800/月** | MVP阶段 |

### 单条内容成本分析

```
成本结构（假设月处理10000条，发布300条）:

采集成本: ¥0.01/条  （服务器+流量）
评分成本: ¥0.05/条  （OpenAI GPT-4o mini）
分类成本: ¥0.03/条  （OpenAI GPT-4o mini）
专业摘要: ¥0.15/条  （Claude 3.5 Sonnet）
科普摘要: ¥0.10/条  （OpenAI GPT-4o）
关键词提取: ¥0.02/条 （Claude 3.5 Haiku）
─────────────────────
单条总成本: ¥0.36/条

发布的300条内容:
总成本 ÷ 300条 = ¥12/条  （含overhead）
```

---

## 部署架构

### 容器化部署

```dockerfile
# Dockerfile 示例
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose 本地开发

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/deepdive
      REDIS_URL: redis://redis:6379
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    depends_on:
      - postgres
      - redis
      - rabbitmq

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: deepdive
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"

  celery_worker:
    build: .
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - rabbitmq
      - postgres

  celery_beat:
    build: .
    command: celery -A tasks beat --loglevel=info
    depends_on:
      - rabbitmq

volumes:
  postgres_data:
```

### 生产部署 (Kubernetes)

```yaml
# 简化示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deepdive-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deepdive-api
  template:
    metadata:
      labels:
        app: deepdive-api
    spec:
      containers:
      - name: api
        image: deepdive:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: deepdive-secrets
              key: db_url
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
```

---

## 监控告警

### 监控指标体系

```
系统健康度指标:
├─ CPU使用率 (目标 <70%)
├─ 内存使用率 (目标 <80%)
├─ 磁盘使用率 (目标 <80%)
├─ 网络带宽 (目标 <60%)
└─ 连接数 (目标 <1000)

应用层指标:
├─ 请求QPS
├─ 响应时间 (p50, p95, p99)
├─ 错误率 (<0.1%)
├─ 缓存命中率 (>80%)
└─ 数据库慢查询 (>1s)

业务指标:
├─ 日采集量
├─ 日处理量
├─ 通过率 (score≥70的比例)
├─ 发布延迟
└─ 用户参与度 (DAU/WAU)

依赖服务:
├─ OpenAI API可用性
├─ Claude API可用性
├─ 数据库连接健康
├─ Redis连接健康
├─ RabbitMQ队列堆积
└─ 各信息源可用性
```

### 告警规则示例

```
告警规则 (Alert Rules):

1. API可用性告警
   - 条件: 错误率 > 1% 持续5分钟
   - 级别: P1 (严重)
   - 行动: 立即告警 → 自动回滚

2. 数据库告警
   - 条件: 连接数 > 80 或 慢查询 > 5个/分钟
   - 级别: P1 (严重)
   - 行动: 告警 → 查看日志

3. API成本告警
   - 条件: 日成本 > 预算110%
   - 级别: P2 (高)
   - 行动: 告警 → 自动降级模型

4. 信息源异常告警
   - 条件: 单个源连续失败3次
   - 级别: P2 (高)
   - 行动: 告警 + 自动禁用 + 转移到备用源

5. 队列堆积告警
   - 条件: 待处理任务 > 1000条
   - 级别: P2 (高)
   - 行动: 告警 + 自动扩容

6. 缓存故障告警
   - 条件: Redis连接失败
   - 级别: P2 (高)
   - 行动: 告警 + 自动降级到DB查询
```

### 监控栈选择

```
日志: ELK Stack (Elasticsearch + Logstash + Kibana)
指标: Prometheus + Grafana
追踪: Jaeger (分布式追踪)
告警: AlertManager + 企业微信/钉钉机器人
```

---

## 总结与建议

### 架构亮点

1. ✅ **高内聚低耦合**
   - 清晰的分层架构
   - 模块间通过MQ解耦

2. ✅ **高可靠性**
   - 多源备份
   - 完善的重试和降级机制
   - 详细的审计日志

3. ✅ **成本优化**
   - AI模型智能选择
   - Redis缓存减少API调用
   - 成本实时监控

4. ✅ **易于扩展**
   - 插件式信息源
   - 灵活的发布渠道
   - 可定制的处理流程

### 实施建议

**Phase 1 (Month 1-2): MVP核心功能**
- [ ] 数据采集引擎（RSS + 简单爬虫）
- [ ] AI处理引擎（评分 + 分类 + 摘要）
- [ ] 内容审核系统
- [ ] 微信发布

**Phase 2 (Month 3-4): 完整MVP**
- [ ] 小红书发布
- [ ] 管理后台
- [ ] 监控告警
- [ ] 性能优化

**Phase 3 (Month 5-6): 扩展功能**
- [ ] Web平台
- [ ] 个性化订阅
- [ ] 高级分析

---

**文档版本历史：**
- v1.0 (2025-11-02): 初版发布
