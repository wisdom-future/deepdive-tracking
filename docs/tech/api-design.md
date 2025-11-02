# DeepDive Tracking - API 设计文档 v1.0

**版本：** 1.0
**最后更新：** 2025-11-02

---

## 目录

1. [API概览](#api概览)
2. [认证与授权](#认证与授权)
3. [核心API接口](#核心api接口)
4. [后台管理API](#后台管理api)
5. [错误处理](#错误处理)
6. [速率限制](#速率限制)
7. [API示例](#api示例)

---

## API概览

### API架构

```
┌─────────────────────────────────────┐
│      前端 / 第三方集成               │
└─────────────────────────────────────┘
           ↓ HTTP/HTTPS
┌─────────────────────────────────────┐
│      API Gateway (Nginx)             │
│  - 路由 / 速率限制 / 日志            │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│      FastAPI 应用层                  │
│  - 请求验证 / 业务逻辑              │
│  - 响应格式化 / 错误处理            │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│      服务层 (业务逻辑)               │
│  - 数据采集 / AI处理 / 发布          │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│      数据层 (数据库 / 缓存)          │
└─────────────────────────────────────┘
```

### API版本化

```
/api/v1/          # 当前稳定版
  ├─ /public/     # 公开API
  ├─ /admin/      # 管理API (需认证)
  └─ /internal/   # 内部API (仅限内部)
```

### API分类

| 分类 | 用途 | 认证 | 用户群体 |
|------|------|------|--------|
| **公开API** | 内容查询、统计 | 可选 | 外部用户 |
| **管理API** | 内容审核、配置管理 | 必须 | 编辑/管理员 |
| **内部API** | 系统内部通信 | 签名验证 | 内部服务 |

---

## 认证与授权

### 认证方式

#### 1. JWT Token (用于后台管理)

```
请求头：
Authorization: Bearer <jwt_token>

Token结构：
{
  "sub": "user_id",
  "name": "用户名",
  "role": "admin|editor|reviewer",
  "permissions": ["create", "edit", "publish"],
  "iat": 1635859200,
  "exp": 1635945600
}
```

#### 2. API Key (用于内部服务)

```
请求头：
X-API-Key: <api_key>

// 或查询参数
GET /api/v1/internal/status?api_key=<api_key>
```

#### 3. 签名认证 (用于第三方集成)

```
请求头：
X-Signature: <signature>
X-Timestamp: <timestamp>
X-Nonce: <nonce>

签名算法：
signature = HMAC-SHA256(
  "GET" + "\n" +
  "/api/v1/public/news\n" +
  "timestamp=1635859200&nonce=abc123\n",
  secret_key
)
```

### 权限模型

```
角色体系：
├─ admin       # 管理员，所有权限
├─ editor      # 编辑，可创建/编辑/发布内容
├─ reviewer    # 审核员，只能审核内容
└─ viewer      # 查看员，只读权限

资源权限：
├─ content    # 内容管理
├─ source     # 信息源管理
├─ settings   # 系统设置
└─ analytics  # 数据分析
```

---

## 核心API接口

### 1. 内容查询接口

#### 1.1 获取已发布内容列表

```
GET /api/v1/public/contents
查询参数：
  - page: int (default: 1)
  - page_size: int (default: 20, max: 100)
  - category: string[] (optional) - 分类筛选
  - sort: string (default: -published_at) - 排序字段
  - search: string (optional) - 关键词搜索
  - date_from: datetime (optional)
  - date_to: datetime (optional)

响应：
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 123,
        "title": "OpenAI发布GPT-4o",
        "category": "tech_breakthrough",
        "summary_pro": "...",
        "summary_sci": "...",
        "score": 85,
        "published_at": "2025-11-02T09:00:00Z",
        "view_count": 1234,
        "like_count": 56,
        "share_count": 23,
        "links": {
          "original": "https://openai.com/blog/...",
          "wechat": "https://mp.weixin.qq.com/...",
          "xiaohongshu": "https://xiaohongshu.com/..."
        }
      }
    ],
    "total": 500,
    "page": 1,
    "page_size": 20,
    "total_pages": 25
  }
}
```

#### 1.2 获取单条内容详情

```
GET /api/v1/public/contents/{id}

响应：
{
  "code": 0,
  "data": {
    "id": 123,
    "title": "OpenAI发布GPT-4o",
    "category": "tech_breakthrough",
    "score": 85,
    "summary_pro": "...",
    "summary_sci": "...",
    "keywords": ["GPT-4o", "LLM", "Multimodal"],
    "tech_terms": {
      "GPT-4o": {
        "cn": "GPT-4o",
        "en": "GPT-4o",
        "explanation": "OpenAI最新发布的多模态模型"
      }
    },
    "published_at": "2025-11-02T09:00:00Z",
    "original_source": "https://openai.com/blog/...",
    "stats": {
      "view_count": 1234,
      "like_count": 56,
      "completion_rate": 0.75
    }
  }
}
```

#### 1.3 获取分类统计

```
GET /api/v1/public/analytics/categories
查询参数：
  - period: day|week|month (default: day)

响应：
{
  "code": 0,
  "data": {
    "company_news": {
      "count": 45,
      "percentage": 22.5,
      "avg_score": 72.3
    },
    "tech_breakthrough": {
      "count": 65,
      "percentage": 32.5,
      "avg_score": 78.1
    },
    // ... 其他分类
  }
}
```

### 2. 内容审核接口（需要审核权限）

#### 2.1 获取待审核内容队列

```
GET /api/v1/admin/review/queue
查询参数：
  - status: pending|needs_edit|approved|rejected (default: pending)
  - sort: score|-created_at (default: -score)
  - page: int (default: 1)

需要权限：reviewer

响应：
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 123,
        "processed_news_id": 100,
        "raw_news_id": 50,
        "score": 85,
        "category": "tech_breakthrough",
        "summary_pro": "...",
        "summary_sci": "...",
        "status": "pending",
        "created_at": "2025-11-02T08:00:00Z",
        "ai_processing_time_ms": 2500,
        "cost": 0.25
      }
    ],
    "total": 120,
    "pending_count": 45
  }
}
```

#### 2.2 提交审核决策

```
POST /api/v1/admin/review/{content_id}/decision
需要权限：reviewer

请求体：
{
  "decision": "approved|rejected|needs_edit",
  "review_notes": "内容有效，推荐发布",
  "confidence": 0.95
}

响应：
{
  "code": 0,
  "message": "Review submitted successfully",
  "data": {
    "content_id": 123,
    "status": "approved",
    "reviewed_at": "2025-11-02T10:30:00Z"
  }
}
```

#### 2.3 编辑内容

```
PUT /api/v1/admin/contents/{content_id}/edit
需要权限：editor

请求体：
{
  "title_edited": "编辑后的标题",
  "summary_pro_edited": "编辑后的专业版摘要",
  "summary_sci_edited": "编辑后的科普版摘要",
  "keywords_edited": ["新关键词1", "新关键词2"],
  "category_edited": "applications",
  "editor_notes": "调整了技术术语的准确性"
}

响应：
{
  "code": 0,
  "data": {
    "content_id": 123,
    "version": 2,
    "edited_at": "2025-11-02T10:45:00Z"
  }
}
```

### 3. 信息源管理接口（需要管理权限）

#### 3.1 获取所有信息源

```
GET /api/v1/admin/sources
需要权限：admin

响应：
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "OpenAI Blog",
        "type": "rss",
        "url": "https://openai.com/blog/rss.xml",
        "priority": 10,
        "is_enabled": true,
        "last_check_at": "2025-11-02T10:00:00Z",
        "last_error": null,
        "error_count": 0,
        "next_check_at": "2025-11-02T10:30:00Z"
      }
    ],
    "total": 50
  }
}
```

#### 3.2 添加新信息源

```
POST /api/v1/admin/sources
需要权限：admin

请求体：
{
  "name": "Anthropic News",
  "type": "rss",
  "url": "https://www.anthropic.com/feed.xml",
  "priority": 9,
  "refresh_interval": 30,
  "tags": ["company", "ai"],
  "description": "Anthropic官方新闻源"
}

响应：
{
  "code": 0,
  "data": {
    "id": 51,
    "name": "Anthropic News",
    "created_at": "2025-11-02T11:00:00Z"
  }
}
```

#### 3.3 更新信息源

```
PUT /api/v1/admin/sources/{source_id}
需要权限：admin

请求体：
{
  "priority": 8,
  "is_enabled": false,
  "refresh_interval": 60
}

响应：
{
  "code": 0,
  "message": "Source updated successfully"
}
```

#### 3.4 删除信息源

```
DELETE /api/v1/admin/sources/{source_id}
需要权限：admin

响应：
{
  "code": 0,
  "message": "Source deleted successfully"
}
```

### 4. 发布管理接口

#### 4.1 创建发布计划

```
POST /api/v1/admin/publish/schedule
需要权限：editor

请求体：
{
  "schedule_type": "daily_brief|weekly_report|xiaohongshu_daily",
  "content_ids": [123, 124, 125],
  "scheduled_at": "2025-11-02T09:00:00Z",
  "target_channels": ["wechat", "xiaohongshu"]
}

响应：
{
  "code": 0,
  "data": {
    "schedule_id": 789,
    "status": "pending",
    "scheduled_at": "2025-11-02T09:00:00Z"
  }
}
```

#### 4.2 获取发布历史

```
GET /api/v1/admin/publish/history
查询参数：
  - status: pending|completed|failed
  - date_from: datetime
  - date_to: datetime
  - page: int

需要权限：editor

响应：
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 789,
        "schedule_type": "daily_brief",
        "scheduled_at": "2025-11-02T09:00:00Z",
        "executed_at": "2025-11-02T09:02:15Z",
        "status": "completed",
        "result": {
          "wechat": {
            "success": true,
            "msg_id": "msg_123456",
            "published_at": "2025-11-02T09:00:30Z"
          },
          "xiaohongshu": {
            "success": true,
            "post_id": "post_789012"
          }
        }
      }
    ]
  }
}
```

### 5. 数据分析接口

#### 5.1 获取内容质量报告

```
GET /api/v1/admin/analytics/quality
查询参数：
  - period: day|week|month (default: month)
  - category: string (optional)

需要权限：editor

响应：
{
  "code": 0,
  "data": {
    "period": "month",
    "metrics": {
      "total_published": 300,
      "avg_completion_rate": 0.72,
      "avg_like_rate": 0.08,
      "avg_share_rate": 0.03,
      "avg_nps_score": 42,
      "total_reach": 45000,
      "total_engagement": 3600
    },
    "by_category": {
      "tech_breakthrough": {
        "count": 95,
        "completion_rate": 0.78,
        "nps_score": 48
      }
    }
  }
}
```

#### 5.2 获取成本报告

```
GET /api/v1/admin/analytics/costs
查询参数：
  - period: day|week|month (default: month)
  - group_by: service|operation|channel

需要权限：admin

响应：
{
  "code": 0,
  "data": {
    "period": "month",
    "total_cost": 3500.50,
    "cost_breakdown": {
      "openai": 2000.00,
      "claude": 800.00,
      "infrastructure": 500.00,
      "publishing": 200.50
    },
    "daily_trend": [
      {"date": "2025-11-01", "cost": 120.50},
      {"date": "2025-11-02", "cost": 125.00}
    ]
  }
}
```

---

## 后台管理API

### 6. Prompt管理接口

#### 6.1 获取Prompt列表

```
GET /api/v1/admin/prompts
需要权限：admin

响应：
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 1,
        "name": "scoring_system",
        "version": 2,
        "model": "gpt-4o-mini",
        "status": "active",
        "content": "You are a news scoring assistant...",
        "created_at": "2025-10-15T10:00:00Z",
        "updated_at": "2025-11-01T14:30:00Z"
      }
    ]
  }
}
```

#### 6.2 创建新Prompt版本

```
POST /api/v1/admin/prompts
需要权限：admin

请求体：
{
  "name": "scoring_system",
  "model": "gpt-4o",
  "content": "You are a news scoring assistant...",
  "description": "Updated scoring criteria for better accuracy"
}

响应：
{
  "code": 0,
  "data": {
    "prompt_id": 3,
    "version": 3,
    "created_at": "2025-11-02T11:00:00Z"
  }
}
```

#### 6.3 测试Prompt

```
POST /api/v1/admin/prompts/{prompt_id}/test
需要权限：admin

请求体：
{
  "test_input": "标题：OpenAI发布GPT-4o\n摘要：OpenAI今天发布了新模型GPT-4o..."
}

响应：
{
  "code": 0,
  "data": {
    "prompt_id": 3,
    "test_output": "85",
    "execution_time_ms": 1234,
    "cost": 0.05
  }
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "code": <error_code>,
  "message": "<error_message>",
  "details": {
    "field": "error_description"
  },
  "request_id": "<unique_request_id>"
}
```

### 标准错误码

| 错误码 | HTTP状态 | 说明 | 示例 |
|--------|--------|------|------|
| 0 | 200 | 成功 | - |
| 400 | 400 | 请求参数错误 | 缺少必需字段 |
| 401 | 401 | 未认证 | Token过期 |
| 403 | 403 | 无权限 | 用户无权访问 |
| 404 | 404 | 资源不存在 | 内容不存在 |
| 409 | 409 | 冲突 | 重复的URL |
| 422 | 422 | 验证失败 | 数据格式不符 |
| 429 | 429 | 超过速率限制 | 请求过于频繁 |
| 500 | 500 | 服务器错误 | 数据库连接失败 |
| 503 | 503 | 服务不可用 | AI API不可用 |

### 错误示例

```json
// 认证失败
{
  "code": 401,
  "message": "Unauthorized",
  "details": {
    "reason": "Invalid or expired token"
  }
}

// 验证失败
{
  "code": 422,
  "message": "Validation failed",
  "details": {
    "priority": "Must be between 1 and 10",
    "refresh_interval": "Must be at least 5 minutes"
  }
}
```

---

## 速率限制

### 限流规则

```
用户级别限流：
- 未认证用户：100 req/hour per IP
- 已认证用户：1000 req/hour per user
- 管理员：5000 req/hour

端点级别限流：
- 内容查询：1000 req/hour
- AI处理：100 req/hour (成本考虑)
- 发布操作：50 req/hour

响应头：
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1635945600
```

### 超限响应

```json
{
  "code": 429,
  "message": "Too many requests",
  "details": {
    "reset_at": "2025-11-02T11:30:00Z",
    "retry_after": 300
  }
}

Response Header:
Retry-After: 300
```

---

## API示例

### 示例1：获取今日精选内容

```bash
curl -X GET "https://api.deepdive.tracking/api/v1/public/contents?page=1&sort=-score" \
  -H "Accept: application/json"

# 响应
{
  "code": 0,
  "data": {
    "items": [
      {
        "id": 123,
        "title": "Google发布Gemini 2.0",
        "category": "tech_breakthrough",
        "score": 92,
        "summary_pro": "Google发布了新一代AI模型Gemini 2.0，在推理、编程等多个任务上超过了GPT-4o...",
        "published_at": "2025-11-02T09:00:00Z",
        "links": {
          "original": "https://google.com/blog/gemini-2",
          "wechat": "https://mp.weixin.qq.com/..."
        }
      }
    ],
    "total": 8,
    "page": 1,
    "page_size": 20
  }
}
```

### 示例2：审核内容

```bash
curl -X POST "https://api.deepdive.tracking/api/v1/admin/review/123/decision" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approved",
    "review_notes": "内容准确，推荐发布",
    "confidence": 0.95
  }'

# 响应
{
  "code": 0,
  "message": "Review submitted successfully",
  "data": {
    "content_id": 123,
    "status": "approved"
  }
}
```

### 示例3：创建发布计划

```bash
curl -X POST "https://api.deepdive.tracking/api/v1/admin/publish/schedule" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_type": "daily_brief",
    "content_ids": [120, 121, 122, 123, 124],
    "scheduled_at": "2025-11-03T09:00:00Z",
    "target_channels": ["wechat", "xiaohongshu"]
  }'

# 响应
{
  "code": 0,
  "data": {
    "schedule_id": 456,
    "status": "pending"
  }
}
```

---

**API文档完成时间：** 2025-11-02
