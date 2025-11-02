# Phase 2 开发计划 - AI评分与分类模块

**计划完成时间：** 2025-11-03 到 2025-11-10
**优先级：** 🔴 P0 - 项目核心功能
**Owner：** Agent 7

---

## 📋 Phase 2 概览

### 核心目标
1. **AI评分模块** - 实现OpenAI GPT-4o集成，对新闻进行0-100分评分
2. **分类模块** - 将新闻分类到8大类别
3. **完整的API** - 支持查询、处理、导出
4. **测试覆盖** - 单元测试和集成测试覆盖率>85%

### 为什么优先？
- 这是产品的核心价值主张（用AI筛选AI资讯）
- 其他所有模块都依赖评分结果
- 直接影响内容质量和用户价值

---

## 🎯 详细任务分解

### 1️⃣ AI评分服务实现 (3-4天)

#### 1.1 核心功能设计
**文件位置：** `src/services/ai/`

```
ai/
├── __init__.py
├── scoring_service.py      ← 主要评分逻辑
├── classifier.py           ← 分类逻辑
├── prompt_templates.py     ← Prompt模板
└── models/
    ├── __init__.py
    └── scoring_response.py  ← 响应数据模型
```

#### 1.2 OpenAI集成
**需要实现：**
- GPT-4o API调用包装器
- Prompt工程（评分和分类提示词）
- 响应解析和验证
- 错误处理和重试机制
- 成本追踪

**关键Prompts：**
```python
SCORING_PROMPT = """
你是AI资讯评分专家。分析以下新闻的重要性和价值。
返回JSON格式的评分结果。

标题：{title}
内容：{content}

评分规则：
- 90-100：行业重大突破、影响深远
- 70-89：重要发展、技术突破
- 50-69：一般新闻、应用案例
- 30-49：公司新闻、市场动态
- 0-29：低相关性、辅助信息

返回格式：
{
    "score": <0-100>,
    "reasoning": "<评分理由>",
    "category": "<8大类之一>",
    "sub_categories": ["<子类别>"],
    "confidence": <0-1>,
    "key_points": ["<关键点1>", "<关键点2>"],
    "keywords": ["<关键词>"],
    "entities": {
        "companies": ["<公司名>"],
        "technologies": ["<技术>"],
        "people": ["<人名>"]
    }
}
"""
```

#### 1.3 数据存储
**目标表：** `processed_news`

**存储的字段：**
- `score` - 0-100分
- `score_breakdown` - 详细评分信息(JSON)
- `category` - 8大类之一
- `sub_categories` - 子类别列表
- `confidence` - 置信度0-1
- `summary_pro` - 专业版摘要
- `summary_sci` - 科普版摘要
- `keywords` - 关键词列表
- `entities` - 命名实体(JSON)
- `tech_terms` - 技术术语(JSON)
- `company_mentions` - 提及的公司
- `cost` - API调用成本
- `processing_time_ms` - 处理耗时

### 2️⃣ API端点实现 (2-3天)

#### 2.1 新闻查询API
```
GET /api/v1/news?skip=0&limit=10&status=raw&source_id=1
GET /api/v1/news/{id}
GET /api/v1/news/stats
```

**返回示例：**
```json
{
    "id": 1,
    "title": "OpenAI releases GPT-4o",
    "url": "https://...",
    "author": "OpenAI",
    "published_at": "2025-11-02T10:00:00Z",
    "source_name": "OpenAI Blog",
    "status": "raw",
    "quality_score": 0.95
}
```

#### 2.2 处理触发API
```
POST /api/v1/news/{id}/process
POST /api/v1/process-batch?limit=10
```

**请求体：**
```json
{
    "force": false
}
```

**响应：**
```json
{
    "processed_count": 5,
    "failed_count": 0,
    "total_cost": 0.035,
    "avg_processing_time_ms": 1250
}
```

#### 2.3 处理结果查询API
```
GET /api/v1/processed-news?skip=0&limit=10&category=tech_breakthrough&min_score=70
GET /api/v1/processed-news/{id}
```

**返回示例：**
```json
{
    "raw_news_id": 1,
    "score": 85,
    "category": "tech_breakthrough",
    "summary_pro": "OpenAI发布...",
    "summary_sci": "简单说就是...",
    "keywords": ["AI", "GPT-4o"],
    "confidence": 0.92
}
```

#### 2.4 统计API
```
GET /api/v1/statistics
GET /api/v1/statistics/by-category
GET /api/v1/statistics/by-source
```

**返回示例：**
```json
{
    "total_raw_news": 10,
    "total_processed": 8,
    "avg_score": 72.5,
    "processing_cost": 0.125,
    "by_category": {
        "tech_breakthrough": 3,
        "company_news": 2,
        ...
    }
}
```

### 3️⃣ 测试实现 (2-3天)

#### 3.1 单元测试
**目标覆盖率：** >85%

**测试文件位置：**
```
tests/
├── unit/
│   ├── services/
│   │   └── ai/
│   │       ├── test_scoring_service.py
│   │       ├── test_classifier.py
│   │       └── test_prompt_templates.py
│   └── api/
│       └── v1/
│           ├── test_news_endpoints.py
│           └── test_statistics_endpoints.py
├── integration/
│   ├── test_collection_to_processing.py
│   └── test_api_workflow.py
└── fixtures/
    ├── sample_news.json
    └── mock_openai_responses.json
```

**测试场景：**
- ✅ 评分服务：正常输入、异常输入、API错误
- ✅ 分类：各类别识别、边界情况
- ✅ 数据存储：保存、更新、查询
- ✅ API端点：参数验证、返回格式、错误处理
- ✅ 集成流程：采集→处理→存储→查询

#### 3.2 集成测试
**测试流程：**
```
1. 采集数据 (collection_manager.collect_all)
   ↓
2. 触发评分 (POST /api/v1/process-batch)
   ↓
3. 验证结果 (GET /api/v1/processed-news)
   ↓
4. 检查统计 (GET /api/v1/statistics)
```

### 4️⃣ 代码审查与优化 (1-2天)

#### 4.1 规范检查清单
- ✅ 代码风格 - black格式化
- ✅ 静态检查 - flake8，mypy
- ✅ 测试覆盖 - >85%
- ✅ 文档 - docstring完整
- ✅ 类型注解 - 所有函数都有类型提示
- ✅ 错误处理 - 完善的异常处理

#### 4.2 性能优化
- 批量处理支持（10-50条并发）
- 缓存策略（相同内容不重复评分）
- 连接池管理

---

## 📊 工作量估计

| 任务 | 工作量 | 依赖 |
|------|--------|------|
| AI评分服务 | 3-4天 | 无 |
| API端点 | 2-3天 | AI服务完成 |
| 测试覆盖 | 2-3天 | 所有代码完成 |
| 代码审查 | 1-2天 | 测试通过 |
| **总计** | **8-12天** | - |

---

## 🔧 技术栈要求

### 新增依赖
```toml
openai = "^1.3.0"              # OpenAI API客户端
tenacity = "^8.2.0"            # 重试机制
pydantic-settings = "^2.0.0"   # 设置管理
pytest-asyncio = "^0.21.0"     # 异步测试
pytest-mock = "^3.11.0"        # Mock支持
```

### 环境配置
**.env 中需要添加：**
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_MAX_RETRIES=3
AI_BATCH_SIZE=10
AI_COST_LIMIT_DAILY=100.0
```

---

## 📋 验收标准

### 代码层面
- ✅ 通过 black 格式化检查
- ✅ 通过 flake8 风格检查
- ✅ 通过 mypy 类型检查
- ✅ 测试覆盖率 ≥ 85%
- ✅ 所有测试通过
- ✅ 所有函数都有docstring

### 功能层面
- ✅ 能成功调用OpenAI API
- ✅ 评分结果正确存储到数据库
- ✅ 所有API端点可用
- ✅ 统计数据准确
- ✅ 错误处理完善

### 文档层面
- ✅ API文档完整
- ✅ 代码注释清晰
- ✅ README更新
- ✅ 交接文档完成

---

## 🎓 对下一个Agent的建议

如果无法在期限内完成所有工作，优先级顺序：

1. **高优先级（MUST）**
   - AI评分核心功能（不必完美，但要能工作）
   - 基础API端点（查询、处理、统计）
   - 单元测试框架（至少50%覆盖率）

2. **中优先级（SHOULD）**
   - 完整测试覆盖（>85%）
   - 错误处理和日志
   - 性能优化

3. **低优先级（CAN）**
   - 缓存策略
   - 高级统计功能
   - UI仪表板

---

## 📚 参考文档

- 产品需求：`docs/product/requirements.md`
- 系统设计：`docs/tech/system-design-summary.md`
- 技术规范：`.claude/standards/04-python-code-style.md`
- 测试规范：`.claude/standards/07-testing-standards.md`
- 数据库设计：`docs/tech/database-schema.md`

---

**准备开始Phase 2！** 🚀
