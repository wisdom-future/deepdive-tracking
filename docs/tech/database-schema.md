# DeepDive Tracking - 数据库设计文档 v1.0

**版本：** 1.0
**最后更新：** 2025-11-02

---

## 目录

1. [数据库概览](#数据库概览)
2. [ER图](#er图)
3. [核心表设计](#核心表设计)
4. [索引策略](#索引策略)
5. [数据流](#数据流)
6. [初始化脚本](#初始化脚本)
7. [备份与恢复](#备份与恢复)

---

## 数据库概览

### 数据库选择

- **主数据库：PostgreSQL 15**
  - 强事务支持
  - JSONB类型支持动态数据
  - 完善的全文搜索
  - 自由开源

- **缓存数据库：Redis 7**
  - 热数据缓存
  - 任务队列备用
  - 会话存储

### 表分组

| 分组 | 表 | 用途 |
|------|-----|------|
| **信息源管理** | data_sources | 维护信息源配置 |
| **原始数据** | raw_news | 采集的原始新闻 |
| **处理结果** | processed_news | AI处理结果 |
| **审核流程** | content_review | 审核和编辑 |
| **已发布内容** | published_content | 最终发布内容 |
| **用户交互** | content_stats, user_feedback | 用户统计和反馈 |
| **定时发布** | publishing_schedules | 发布任务管理 |
| **系统日志** | operation_logs, cost_logs | 操作审计和成本追踪 |

---

## ER图

```
┌─────────────────────┐
│   data_sources      │  (信息源)
│─────────────────────│
│ id (PK)             │
│ name                │
│ type                │
│ url                 │
│ priority            │
│ is_enabled          │
│ last_check_at       │
│ error_count         │
└─────────────────────┘
          │ 1
          │
          │ N
          ↓
┌─────────────────────┐
│   raw_news          │  (原始新闻)
│─────────────────────│
│ id (PK)             │
│ source_id (FK)      │
│ title               │
│ url (UNIQUE)        │
│ content             │
│ published_at        │
│ hash (UNIQUE)       │
│ status              │
│ fetched_at          │
└─────────────────────┘
          │ 1
          │
          │ 1
          ↓
┌──────────────────────┐
│  processed_news      │  (处理结果)
│──────────────────────│
│ id (PK)              │
│ raw_news_id (FK)     │
│ score                │
│ category             │
│ keywords             │
│ summary_pro          │
│ summary_sci          │
│ tech_terms (JSONB)   │
│ processing_time_ms   │
│ cost                 │
└──────────────────────┘
          │ 1
          │
          │ 1
          ↓
┌──────────────────────┐
│  content_review      │  (审核)
│──────────────────────│
│ id (PK)              │
│ processed_news_id(FK)│
│ status               │
│ reviewed_by          │
│ reviewed_at          │
│ summary_pro_edited   │
│ summary_sci_edited   │
│ editor_notes         │
│ edited_by            │
└──────────────────────┘
          │ 1
          │
          │ 1
          ↓
┌──────────────────────┐
│ published_content    │  (已发布)
│──────────────────────│
│ id (PK)              │
│ processed_news_id(FK)│
│ content_review_id(FK)│
│ publish_status       │
│ channels             │
│ published_at         │
│ wechat_url           │
│ xiaohongshu_url      │
│ web_url              │
└──────────────────────┘
          │ 1
          │
          │ N
          ↓
┌──────────────────────┐
│  content_stats       │  (统计)
│──────────────────────│
│ id (PK)              │
│ published_content_id │
│ channel              │
│ view_count           │
│ like_count           │
│ share_count          │
│ completion_rate      │
│ nps_score            │
└──────────────────────┘
```

---

## 核心表设计

### 1. data_sources - 信息源配置表

```sql
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,

    -- 基本信息
    name VARCHAR(255) NOT NULL,           -- "OpenAI Blog"
    description TEXT,
    type VARCHAR(50) NOT NULL,            -- rss, crawler, api, twitter, email

    -- 访问配置
    url VARCHAR(2048),
    method VARCHAR(10) DEFAULT 'GET',
    headers JSONB DEFAULT '{}',           -- 自定义请求头
    params JSONB DEFAULT '{}',            -- 查询参数
    auth_type VARCHAR(50),                -- none, basic, bearer, custom
    auth_token VARCHAR(1024),             -- 加密存储

    -- 解析配置 (爬虫特有)
    css_selectors JSONB,                  -- {title: "h1", content: ".article"}
    xpath_patterns JSONB,

    -- 运行策略
    priority INT DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    refresh_interval INT DEFAULT 30,      -- 分钟
    max_items_per_run INT DEFAULT 50,
    is_enabled BOOLEAN DEFAULT TRUE,

    -- 状态追踪
    last_check_at TIMESTAMP,
    last_success_at TIMESTAMP,
    last_error TEXT,
    error_count INT DEFAULT 0,
    consecutive_failures INT DEFAULT 0,

    -- 能力标签
    supports_pagination BOOLEAN DEFAULT FALSE,
    supports_filter BOOLEAN DEFAULT FALSE,
    tags TEXT[],                          -- 标签: [tech, company, infrastructure]

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),

    -- 约束
    CONSTRAINT valid_type CHECK (type IN ('rss', 'crawler', 'api', 'twitter', 'email')),
    UNIQUE (name, type)
);

-- 索引
CREATE INDEX idx_sources_enabled_priority
    ON data_sources(is_enabled, priority DESC);
CREATE INDEX idx_sources_last_check
    ON data_sources(last_check_at);
CREATE INDEX idx_sources_type
    ON data_sources(type);
```

### 2. raw_news - 原始新闻表

```sql
CREATE TABLE raw_news (
    id SERIAL PRIMARY KEY,

    -- 来源关联
    source_id INT NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,

    -- 核心内容
    title VARCHAR(512) NOT NULL,
    url VARCHAR(2048) UNIQUE NOT NULL,
    content TEXT,                        -- 完整内容

    -- 内容特征
    html_content BYTEA,                 -- 原始HTML (可选)
    language VARCHAR(10) DEFAULT 'en',  -- 语言检测结果
    hash VARCHAR(64) UNIQUE NOT NULL,   -- Simhash用于去重

    -- 来源元数据
    author VARCHAR(255),
    source_name VARCHAR(255),
    published_at TIMESTAMP NOT NULL,    -- 新闻发布时间

    -- 采集信息
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 处理状态
    status VARCHAR(50) DEFAULT 'raw',   -- raw, processing, processed, failed
    error_message TEXT,                 -- 处理错误信息
    retry_count INT DEFAULT 0,
    next_retry_at TIMESTAMP,

    -- 检测结果
    is_duplicate BOOLEAN DEFAULT FALSE,
    is_spam BOOLEAN DEFAULT FALSE,
    quality_score FLOAT,                -- 初步质量评分 (0-1)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('raw', 'processing', 'processed', 'failed', 'duplicate'))
);

-- 复合索引
CREATE INDEX idx_raw_news_status_created
    ON raw_news(status, created_at DESC);
CREATE INDEX idx_raw_news_source_time
    ON raw_news(source_id, published_at DESC);
CREATE INDEX idx_raw_news_url
    ON raw_news(url);
CREATE INDEX idx_raw_news_hash
    ON raw_news(hash);  -- 去重查询
CREATE INDEX idx_raw_news_published
    ON raw_news(published_at DESC);

-- 分区策略（可选，数据量大时）
-- CREATE TABLE raw_news_2025_11 PARTITION OF raw_news
--     FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

### 3. processed_news - 处理结果表

```sql
CREATE TABLE processed_news (
    id SERIAL PRIMARY KEY,

    -- 原始数据关联
    raw_news_id INT NOT NULL UNIQUE REFERENCES raw_news(id) ON DELETE CASCADE,

    -- AI评分与分类
    score FLOAT NOT NULL CHECK (score BETWEEN 0 AND 100),
    score_breakdown JSONB,               -- {importance: 30, timeliness: 15, ...}
    category VARCHAR(50) NOT NULL,      -- 8类之一
    sub_categories TEXT[],               -- 细分类别
    confidence FLOAT,                    -- 分类置信度

    -- 内容生成
    summary_pro TEXT NOT NULL,           -- 专业版摘要 (200-300字)
    summary_sci TEXT NOT NULL,           -- 科普版摘要 (200-300字)

    -- 关键信息
    keywords TEXT[],                     -- [3-5个关键词]
    entities JSONB,                      -- {person: [...], org: [...], ...}

    -- 技术相关
    tech_terms JSONB,                    -- {term: "LLM", en: "Large Language Model", ...}
    infrastructure_tags TEXT[],          -- [GPU, RDMA, TPU, ...]
    company_mentions VARCHAR(255)[],     -- 提及的公司

    -- 分析元数据
    readability_score FLOAT,             -- 可读性评分
    sentiment VARCHAR(50),               -- positive, negative, neutral
    word_count INT,

    -- AI处理信息
    ai_models_used TEXT[],               -- [gpt-4o, claude-3.5-sonnet]
    processing_time_ms INT,              -- 处理耗时
    cost FLOAT,                          -- 成本，精确到0.001元
    cost_breakdown JSONB,                -- {scoring: 0.05, summary: 0.15, ...}

    -- 版本控制
    version INT DEFAULT 1,
    previous_id INT REFERENCES processed_news(id),  -- 前一个版本

    -- 质量指标
    quality_score FLOAT,                 -- 整体质量评分 (0-1)
    quality_notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_category CHECK (category IN (
        'company_news', 'tech_breakthrough', 'applications',
        'infrastructure', 'policy', 'market_trends',
        'expert_opinions', 'learning_resources'
    ))
);

-- 索引
CREATE INDEX idx_processed_score_desc
    ON processed_news(score DESC);
CREATE INDEX idx_processed_category
    ON processed_news(category);
CREATE INDEX idx_processed_confidence
    ON processed_news(confidence DESC);
CREATE INDEX idx_processed_created
    ON processed_news(created_at DESC);
CREATE INDEX idx_processed_company_mentions
    ON processed_news USING GIN (company_mentions);  -- 数组搜索
CREATE INDEX idx_processed_keywords
    ON processed_news USING GIN (keywords);
```

### 4. content_review - 审核与编辑表

```sql
CREATE TABLE content_review (
    id SERIAL PRIMARY KEY,

    -- 关联
    processed_news_id INT NOT NULL UNIQUE
        REFERENCES processed_news(id) ON DELETE CASCADE,

    -- 审核状态机
    status VARCHAR(50) DEFAULT 'pending',
    review_notes TEXT,                   -- 审核意见
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_decision VARCHAR(50),         -- approved, rejected, needs_edit

    -- 编辑修改
    title_edited VARCHAR(512),           -- 编辑修改的标题
    summary_pro_edited TEXT,             -- 编辑修改的专业版
    summary_sci_edited TEXT,             -- 编辑修改的科普版
    keywords_edited TEXT[],              -- 编辑修改的关键词
    category_edited VARCHAR(50),         -- 编辑修改的分类

    editor_notes TEXT,                   -- 编辑备注
    edited_by VARCHAR(255),
    edited_at TIMESTAMP,

    -- 修改历史
    change_log JSONB,                    -- [{field: "summary_pro", before: "...", after: "...", by: "editor1", at: "2025-11-02T10:00:00"}]

    -- 审核规则检查
    checked_sensitive_words BOOLEAN DEFAULT FALSE,
    has_sensitive_words BOOLEAN DEFAULT FALSE,
    sensitive_words_detail TEXT,

    checked_copyright BOOLEAN DEFAULT FALSE,
    copyright_issues TEXT,

    checked_technical_accuracy BOOLEAN DEFAULT FALSE,
    technical_accuracy_notes TEXT,

    -- 审核员反馈
    reviewer_confidence FLOAT,           -- 审核员对内容的置信度
    reviewer_tags TEXT[],                -- 审核员标注的标签

    -- 流程信息
    send_back_count INT DEFAULT 0,       -- 被退回次数
    final_decision_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'approved', 'rejected', 'needs_edit', 'in_review'
    ))
);

-- 索引
CREATE INDEX idx_review_status
    ON content_review(status);
CREATE INDEX idx_review_reviewed_at
    ON content_review(reviewed_at DESC);
CREATE INDEX idx_review_edited_by
    ON content_review(edited_by);
```

### 5. published_content - 已发布内容表

```sql
CREATE TABLE published_content (
    id SERIAL PRIMARY KEY,

    -- 关联
    processed_news_id INT NOT NULL
        REFERENCES processed_news(id) ON DELETE CASCADE,
    content_review_id INT
        REFERENCES content_review(id),
    raw_news_id INT NOT NULL
        REFERENCES raw_news(id),

    -- 发布状态
    publish_status VARCHAR(50) DEFAULT 'draft',  -- draft, scheduled, published, archived, failed

    -- 发布渠道
    channels TEXT[] NOT NULL,            -- ['wechat', 'xiaohongshu', 'web']

    -- 最终内容（可能与AI生成内容不同）
    final_title VARCHAR(512),
    final_summary_pro TEXT,
    final_summary_sci TEXT,
    final_keywords TEXT[],

    -- 发布时间
    scheduled_at TIMESTAMP,              -- 计划发布时间
    published_at TIMESTAMP,              -- 实际发布时间

    -- 渠道特定URL
    wechat_msg_id VARCHAR(255),          -- 微信消息ID
    wechat_url VARCHAR(2048),
    xiaohongshu_post_id VARCHAR(255),
    xiaohongshu_url VARCHAR(2048),
    web_url VARCHAR(2048),

    -- 版本信息
    content_version INT DEFAULT 1,       -- 修改版本

    -- 发布信息
    published_by VARCHAR(255),
    publish_error TEXT,
    retry_count INT DEFAULT 0,
    last_retry_at TIMESTAMP,

    -- 生成的媒体
    featured_image_url VARCHAR(2048),
    images JSONB,                        -- [{url: "...", caption: "..."}, ...]

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (publish_status IN (
        'draft', 'scheduled', 'published', 'archived', 'failed'
    ))
);

-- 索引
CREATE INDEX idx_published_status
    ON published_content(publish_status);
CREATE INDEX idx_published_published_at
    ON published_content(published_at DESC);
CREATE INDEX idx_published_scheduled
    ON published_content(scheduled_at) WHERE publish_status = 'scheduled';
CREATE INDEX idx_published_channels
    ON published_content USING GIN (channels);
```

### 6. content_stats - 内容统计表

```sql
CREATE TABLE content_stats (
    id SERIAL PRIMARY KEY,

    published_content_id INT NOT NULL
        REFERENCES published_content(id) ON DELETE CASCADE,

    -- 渠道统计
    channel VARCHAR(50) NOT NULL,        -- wechat, xiaohongshu, web

    -- 阅读数据
    view_count INT DEFAULT 0,
    unique_viewers INT DEFAULT 0,
    read_count INT DEFAULT 0,            -- 真实阅读（打开了完整内容）
    completion_rate FLOAT,               -- 完成率 (read_count / view_count)
    avg_read_time INT,                   -- 平均阅读时间（秒）

    -- 交互数据
    like_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    collection_count INT DEFAULT 0,      -- 收藏数

    -- 深度指标
    click_through_rate FLOAT,            -- CTR (click / view)
    social_share_rate FLOAT,             -- (share / view)

    -- 用户反馈
    nps_score INT,                       -- Net Promoter Score (-100 到 100)
    nps_feedback_count INT DEFAULT 0,
    average_rating FLOAT,                -- 平均评分 (1-5)
    rating_count INT DEFAULT 0,

    -- 流量来源
    referrer_stats JSONB,                -- {direct: 100, wechat: 50, ...}

    -- 时间序列数据
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP,

    CONSTRAINT valid_channel CHECK (channel IN ('wechat', 'xiaohongshu', 'web', 'email'))
);

-- 索引
CREATE INDEX idx_stats_content_channel
    ON content_stats(published_content_id, channel);
CREATE INDEX idx_stats_completion_rate
    ON content_stats(completion_rate DESC) WHERE completion_rate > 0;
CREATE INDEX idx_stats_updated
    ON content_stats(updated_at DESC);
```

### 7. publishing_schedules - 定时发布表

```sql
CREATE TABLE publishing_schedules (
    id SERIAL PRIMARY KEY,

    -- 发布计划
    schedule_type VARCHAR(50) NOT NULL,  -- daily_brief, weekly_report, xiaohongshu_daily
    content_ids INT[] NOT NULL,          -- 待发布的内容ID数组

    -- 计划时间
    scheduled_at TIMESTAMP NOT NULL,
    execution_window_start TIMESTAMP,    -- 执行窗口开始
    execution_window_end TIMESTAMP,      -- 执行窗口结束

    -- 执行信息
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    executed_at TIMESTAMP,

    -- 发布渠道
    target_channels TEXT[],              -- ['wechat', 'xiaohongshu']

    -- 模板与配置
    template_id INT,
    template_variables JSONB,

    -- 执行结果
    result JSONB,                        -- {
                                          --   wechat: {success: true, msg_id: "...", published_at: "..."},
                                          --   xiaohongshu: {success: false, error: "..."}
                                          -- }
    error_message TEXT,
    error_details JSONB,

    -- 重试机制
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    next_retry_at TIMESTAMP,

    -- 回滚信息
    can_rollback BOOLEAN DEFAULT TRUE,
    rollback_deadline TIMESTAMP,
    rolled_back BOOLEAN DEFAULT FALSE,
    rollback_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),

    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    ))
);

-- 索引
CREATE INDEX idx_schedules_time
    ON publishing_schedules(scheduled_at, status);
CREATE INDEX idx_schedules_status
    ON publishing_schedules(status) WHERE status IN ('pending', 'running');
```

### 8. cost_logs - 成本追踪表

```sql
CREATE TABLE cost_logs (
    id SERIAL PRIMARY KEY,

    -- 关联
    processed_news_id INT REFERENCES processed_news(id),
    publishing_schedule_id INT REFERENCES publishing_schedules(id),

    -- 成本信息
    service VARCHAR(100) NOT NULL,      -- openai, claude, wechat, xiaohongshu, etc
    operation VARCHAR(100) NOT NULL,    -- scoring, summarization, publishing

    -- 使用量和成本
    usage_units INT,                     -- tokens, API calls, messages
    unit_price FLOAT,                    -- 单价
    total_cost FLOAT,                    -- 总成本

    -- 详细信息
    request_id VARCHAR(255),             -- API请求ID
    model VARCHAR(100),                  -- 使用的模型
    metadata JSONB,                      -- 额外信息

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT positive_cost CHECK (total_cost >= 0)
);

-- 索引
CREATE INDEX idx_cost_service_date
    ON cost_logs(service, created_at DESC);
CREATE INDEX idx_cost_date
    ON cost_logs(created_at DESC);
```

### 9. operation_logs - 操作审计日志表

```sql
CREATE TABLE operation_logs (
    id SERIAL PRIMARY KEY,

    -- 操作信息
    operation_type VARCHAR(100) NOT NULL,  -- create, update, delete, publish, review, etc
    resource_type VARCHAR(100) NOT NULL,   -- raw_news, processed_news, content, etc
    resource_id INT,

    -- 操作者
    operator_id VARCHAR(255),
    operator_name VARCHAR(255),

    -- 操作内容
    action_detail TEXT,
    old_values JSONB,
    new_values JSONB,

    -- IP和环境
    ip_address VARCHAR(45),
    user_agent TEXT,

    -- 结果
    status VARCHAR(50),                  -- success, failure
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_operation_type_date
    ON operation_logs(operation_type, created_at DESC);
CREATE INDEX idx_operation_resource
    ON operation_logs(resource_type, resource_id);
CREATE INDEX idx_operation_operator
    ON operation_logs(operator_id, created_at DESC);
```

---

## 索引策略

### 索引总结表

| 表 | 索引 | 类型 | 优先级 | 说明 |
|-----|------|------|--------|------|
| raw_news | idx_raw_news_status_created | 复合 | P1 | 常用查询条件 |
| raw_news | idx_raw_news_hash | B-tree | P1 | 去重 |
| processed_news | idx_processed_score_desc | B-tree | P1 | 评分筛选 |
| processed_news | idx_processed_category | B-tree | P1 | 分类统计 |
| content_review | idx_review_status | B-tree | P1 | 审核流程 |
| published_content | idx_published_published_at | B-tree | P1 | 时间排序 |
| content_stats | idx_stats_completion_rate | B-tree | P2 | 质量分析 |
| cost_logs | idx_cost_date | B-tree | P2 | 成本统计 |

### 索引优化建议

1. **定期ANALYZE**：更新表统计信息
```sql
ANALYZE raw_news;
ANALYZE processed_news;
ANALYZE published_content;
```

2. **定期REINDEX**：避免索引膨胀
```sql
REINDEX INDEX idx_raw_news_status_created;
```

3. **监控慢查询**：识别需要新索引的查询
```sql
-- PostgreSQL日志配置
log_min_duration_statement = 1000;  -- 记录超过1秒的查询
```

---

## 数据流

### 数据生命周期

```
采集阶段 (T+0):
  → raw_news (status='raw')

处理阶段 (T+0~5分钟):
  → raw_news (status='processing')
  → processed_news (创建)
  → cost_logs (记录AI成本)

审核阶段 (T+5~20分钟):
  → content_review (status='pending')
  → 人工审核
  → content_review (status='approved/rejected/needs_edit')

编辑阶段 (T+20~60分钟):
  → content_review (编辑修改)
  → operation_logs (记录修改)

发布阶段 (T+次日8:45/17:45/周日19:45):
  → publishing_schedules (创建，status='pending')
  → published_content (创建，status='scheduled')
  → 执行发布
  → published_content (status='published')
  → publishing_schedules (status='completed')
  → cost_logs (记录发布成本)

统计阶段 (实时更新):
  → content_stats (view_count, like_count等)
  → operation_logs (记录用户交互)
```

---

## 初始化脚本

### 创建所有表

```sql
-- 1. 基础表
CREATE TABLE data_sources (...)
CREATE TABLE raw_news (...)
CREATE TABLE processed_news (...)
CREATE TABLE content_review (...)
CREATE TABLE published_content (...)

-- 2. 统计和日志表
CREATE TABLE content_stats (...)
CREATE TABLE publishing_schedules (...)
CREATE TABLE cost_logs (...)
CREATE TABLE operation_logs (...)

-- 3. 创建所有索引
CREATE INDEX idx_raw_news_status_created ON raw_news(status, created_at DESC);
-- ... (所有索引)
```

### 初始数据

```sql
-- 插入初始信息源
INSERT INTO data_sources (name, type, url, priority, refresh_interval) VALUES
('OpenAI Blog', 'rss', 'https://openai.com/blog/rss.xml', 10, 30),
('Anthropic News', 'rss', 'https://www.anthropic.com/feed.xml', 10, 30),
('Google DeepMind Blog', 'rss', 'https://deepmind.google/blog/feed.xml', 9, 30),
-- ... 更多源
```

---

## 备份与恢复

### 备份策略

```bash
# 每6小时完整备份
pg_dump -h localhost -U postgres -d deepdive > /backup/deepdive_$(date +%Y%m%d_%H%M%S).sql

# 或使用pg_basebackup (用于流复制)
pg_basebackup -h localhost -U postgres -D /backup/base -v
```

### 恢复流程

```bash
# 从备份文件恢复
psql -h localhost -U postgres < /backup/deepdive_20251102_100000.sql
```

---

**文档完成时间：** 2025-11-02
