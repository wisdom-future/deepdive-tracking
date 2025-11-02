# API设计规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ REST优先，遵循HTTP规范
✅ 清晰的资源模型
✅ 版本隔离，向后兼容
✅ 一致的错误处理
✅ 充分的文档和示例
```

---

## RESTful设计规范

### 🔴 MUST - 严格遵守

1. **使用名词表示资源，不用动词**
   ```
   ✅ GET    /api/v1/contents           (列表)
   ✅ POST   /api/v1/contents           (创建)
   ✅ GET    /api/v1/contents/{id}      (详情)
   ✅ PUT    /api/v1/contents/{id}      (全量更新)
   ✅ PATCH  /api/v1/contents/{id}      (部分更新)
   ✅ DELETE /api/v1/contents/{id}      (删除)

   ❌ GET    /api/v1/get-contents
   ❌ POST   /api/v1/create-content
   ❌ GET    /api/v1/content-detail/{id}
   ❌ POST   /api/v1/delete-content/{id}
   ```

2. **使用 HTTP 方法的正确含义**
   ```
   GET     - 读取资源，幂等，安全
   POST    - 创建资源，非幂等
   PUT     - 全量替换资源，幂等
   PATCH   - 部分更新资源，幂等
   DELETE  - 删除资源，幂等
   ```

3. **子资源使用分层路径**
   ```
   ✅ GET    /api/v1/contents/{id}/reviews
   ✅ POST   /api/v1/contents/{id}/reviews
   ✅ GET    /api/v1/contents/{id}/reviews/{review_id}
   ✅ DELETE /api/v1/contents/{id}/reviews/{review_id}

   ❌ GET    /api/v1/reviews-for-content/{id}
   ❌ POST   /api/v1/create-review-for-content
   ```

4. **自定义操作使用POST**
   ```
   ✅ POST   /api/v1/contents/{id}/publish
   ✅ POST   /api/v1/contents/{id}/archive
   ✅ POST   /api/v1/contents/{id}/duplicate

   ❌ GET    /api/v1/contents/{id}/publish
   ❌ PUT    /api/v1/contents/{id}/publish-endpoint
   ```

5. **过滤、排序、分页使用查询参数**
   ```
   ✅ GET    /api/v1/contents?status=published&category=AI&limit=10&offset=0
   ✅ GET    /api/v1/contents?sort_by=created_at&sort_order=desc
   ✅ GET    /api/v1/contents?search=ChatGPT

   ❌ GET    /api/v1/contents/published/AI
   ❌ GET    /api/v1/contents/page/1
   ```

6. **API 版本隔离在路径中**
   ```
   ✅ /api/v1/contents
   ✅ /api/v2/contents

   ❌ /api/contents?version=1
   ❌ /api/contents/v1
   ```

### 🟡 SHOULD - 强烈建议

1. **使用kebab-case的路由路径**
   ```
   ✅ /api/v1/content-items
   ✅ /api/v1/data-sources
   ✅ /api/v1/admin/review-queue

   ❌ /api/v1/content_items
   ❌ /api/v1/ContentItems
   ```

2. **ID使用 {id} 或 {resource_id}**
   ```
   ✅ /api/v1/contents/{id}
   ✅ /api/v1/users/{user_id}/contents/{content_id}
   ```

---

## HTTP 状态码规范

### 🔴 MUST - 严格遵守

1. **2xx 成功响应**
   ```
   200 OK              - 请求成功，返回数据
   201 Created         - 创建资源成功
   204 No Content      - 删除成功，无返回内容
   ```

2. **4xx 客户端错误**
   ```
   400 Bad Request     - 请求参数错误
   401 Unauthorized    - 未认证
   403 Forbidden       - 已认证但无权限
   404 Not Found       - 资源不存在
   409 Conflict        - 资源冲突（如重复创建）
   422 Unprocessable   - 请求格式正确但验证失败
   ```

3. **5xx 服务器错误**
   ```
   500 Internal Error  - 服务器内部错误
   503 Service Unavailable - 服务暂时不可用
   ```

---

## 请求和响应格式

### 🔴 MUST - 严格遵守

1. **请求体使用 JSON**
   ```python
   # POST /api/v1/contents
   {
       "title": "OpenAI发布GPT-4",
       "body": "OpenAI官方发布了GPT-4模型...",
       "category": "AI",
       "source_id": 123
   }
   ```

2. **响应体统一格式**
   ```json
   // 成功响应 (200, 201)
   {
       "code": 0,
       "message": "success",
       "data": {
           "id": 123,
           "title": "OpenAI发布GPT-4",
           "body": "...",
           "category": "AI",
           "score": 85,
           "status": "published",
           "created_at": "2025-11-02T10:00:00Z",
           "updated_at": "2025-11-02T10:00:00Z"
       }
   }

   // 列表响应 (200)
   {
       "code": 0,
       "message": "success",
       "data": {
           "items": [...],
           "total": 100,
           "limit": 10,
           "offset": 0
       }
   }

   // 错误响应 (4xx, 5xx)
   {
       "code": 400,
       "message": "Invalid request",
       "error": {
           "field": "category",
           "reason": "Must be one of: AI, ML, DL, NLP, CV, RL, ..."
       }
   }
   ```

3. **使用 snake_case 的字段名**
   ```json
   ✅ {
       "user_id": 123,
       "created_at": "2025-11-02T10:00:00Z",
       "is_active": true
   }

   ❌ {
       "userId": 123,
       "createdAt": "2025-11-02T10:00:00Z",
       "IsActive": true
   }
   ```

4. **日期时间使用 ISO 8601 格式**
   ```
   ✅ "2025-11-02T10:00:00Z"
   ✅ "2025-11-02T10:00:00+08:00"

   ❌ "2025-11-02 10:00:00"
   ❌ "11/02/2025 10:00:00"
   ❌ 1667382000 (时间戳)
   ```

5. **布尔值使用 true/false**
   ```json
   ✅ {
       "is_published": true,
       "has_review": false
   }

   ❌ {
       "is_published": "true",
       "has_review": "no",
       "published": 1
   }
   ```

6. **null 表示缺失值**
   ```json
   ✅ {
       "id": 123,
       "optional_field": null
   }

   ❌ {
       "id": 123
       // 省略optional_field
   }
   ```

---

## 分页规范

### 🔴 MUST - 严格遵守

1. **使用 limit/offset 分页**
   ```
   ✅ GET /api/v1/contents?limit=10&offset=0
   ✅ GET /api/v1/contents?limit=10&offset=10

   ❌ GET /api/v1/contents?page=1&per_page=10
   ❌ GET /api/v1/contents/page/1
   ```

2. **分页响应格式**
   ```json
   {
       "code": 0,
       "message": "success",
       "data": {
           "items": [...],
           "total": 1000,
           "limit": 10,
           "offset": 0
       }
   }
   ```

3. **默认值和限制**
   ```
   默认 limit: 10
   最大 limit: 100
   默认 offset: 0

   ✅ GET /api/v1/contents              (limit=10, offset=0)
   ✅ GET /api/v1/contents?limit=50
   ✅ GET /api/v1/contents?limit=100&offset=200

   ❌ GET /api/v1/contents?limit=1000   (超过最大值)
   ```

---

## 查询参数规范

### 🔴 MUST - 严格遵守

1. **过滤使用明确的字段名**
   ```
   ✅ GET /api/v1/contents?status=published
   ✅ GET /api/v1/contents?category=AI&status=published
   ✅ GET /api/v1/contents?score_gte=80

   ❌ GET /api/v1/contents?filter=published
   ❌ GET /api/v1/contents?q=status:published
   ```

2. **排序规范**
   ```
   ✅ GET /api/v1/contents?sort_by=created_at&sort_order=desc
   ✅ GET /api/v1/contents?sort_by=score&sort_order=desc

   ❌ GET /api/v1/contents?sort=-created_at
   ❌ GET /api/v1/contents?order=desc
   ```

3. **搜索规范**
   ```
   ✅ GET /api/v1/contents?search=ChatGPT
   ✅ GET /api/v1/contents?search_field=title&search_value=ChatGPT

   ❌ GET /api/v1/contents?q=ChatGPT
   ❌ GET /api/v1/contents?keyword=ChatGPT
   ```

---

## 错误处理规范

### 🔴 MUST - 严格遵守

1. **统一的错误响应格式**
   ```json
   {
       "code": 400,
       "message": "Validation error",
       "error": {
           "field": "category",
           "reason": "Must be one of: AI, ML, DL, NLP, CV, RL, ..."
       },
       "timestamp": "2025-11-02T10:00:00Z",
       "request_id": "req_abc123xyz"
   }
   ```

2. **定义清晰的错误码**
   ```
   1000 - 参数验证错误
   1001 - 资源不存在
   1002 - 权限不足
   1003 - 业务规则冲突
   2000 - 数据库错误
   3000 - 第三方服务错误
   9000 - 未知错误
   ```

3. **验证错误详情**
   ```json
   {
       "code": 1000,
       "message": "Validation failed",
       "errors": [
           {
               "field": "title",
               "reason": "Required field"
           },
           {
               "field": "score",
               "reason": "Must be between 0 and 100"
           }
       ]
   }
   ```

---

## 认证和授权规范

### 🔴 MUST - 严格遵守

1. **使用 Bearer Token 认证**
   ```
   Authorization: Bearer <token>
   ```

2. **令牌放在 HTTP 头中**
   ```
   ✅ Authorization: Bearer eyJhbGciOiJIUzI1NiI...

   ❌ Authorization: <token>
   ❌ X-Auth-Token: <token>
   ❌ /api/v1/contents?token=<token>
   ```

3. **401 表示未认证，403 表示无权限**
   ```
   401 Unauthorized  - 没有提供token或token无效
   403 Forbidden     - token有效但没有权限
   ```

---

## API 文档规范

### 🔴 MUST - 严格遵守

1. **使用 OpenAPI 3.0 规范**
   ```yaml
   openapi: 3.0.0
   info:
     title: DeepDive Tracking API
     version: 1.0.0
   paths:
     /api/v1/contents:
       get:
         summary: 列表查询内容
         parameters:
           - name: limit
             in: query
             schema:
               type: integer
               default: 10
           - name: offset
             in: query
             schema:
               type: integer
               default: 0
         responses:
           '200':
             description: 成功
   ```

2. **每个端点都要有文档**
   - 描述(description)
   - 参数(parameters)
   - 请求体(request body)
   - 响应(responses)
   - 错误情况(error cases)
   - 使用示例(examples)

### 🟡 SHOULD - 强烈建议

1. **使用 FastAPI 自动生成文档**
   ```python
   from fastapi import FastAPI
   from fastapi.openapi.utils import get_openapi

   app = FastAPI(
       title="DeepDive Tracking API",
       version="1.0.0",
       docs_url="/api/docs",  # Swagger UI
       redoc_url="/api/redoc"  # ReDoc
   )

   @app.get("/api/v1/contents/{id}")
   async def get_content(
       id: int,
       **description="Get content by ID"**
   ) -> ContentResponse:
       """获取内容详情。

       根据内容ID查询详细信息。
       """
       pass
   ```

---

## FastAPI 实现规范

### 🔴 MUST - 严格遵守

1. **路由定义**
   ```python
   from fastapi import APIRouter, HTTPException, Path, Query
   from pydantic import BaseModel

   router = APIRouter(prefix="/api/v1/contents", tags=["contents"])

   @router.get("/{content_id}")
   async def get_content(
       content_id: int = Path(..., gt=0, description="Content ID")
   ) -> ContentResponse:
       """获取内容详情。"""
       try:
           content = await service.get(content_id)
           if not content:
               raise HTTPException(status_code=404, detail="Content not found")
           return ContentResponse(**content.dict())
       except Exception as e:
           logger.error(f"Error getting content: {str(e)}")
           raise HTTPException(status_code=500, detail="Internal server error")
   ```

2. **请求和响应模型**
   ```python
   from pydantic import BaseModel, Field, validator
   from typing import Optional

   class ContentCreateRequest(BaseModel):
       title: str = Field(..., min_length=1, max_length=200)
       body: str = Field(..., min_length=10)
       category: str = Field(..., regex="^(AI|ML|DL|NLP|CV|RL|NLG|AGI)$")
       source_id: int = Field(..., gt=0)

       @validator('title')
       def title_no_special_chars(cls, v):
           if any(c in v for c in '<>{}[]'):
               raise ValueError('Title contains invalid characters')
           return v

   class ContentResponse(BaseModel):
       id: int
       title: str
       body: str
       category: str
       score: int
       status: str
       created_at: datetime
       updated_at: datetime

       class Config:
           from_attributes = True  # 支持SQLAlchemy模型
   ```

3. **异常处理**
   ```python
   from fastapi import HTTPException

   @router.post("/")
   async def create_content(data: ContentCreateRequest) -> ContentResponse:
       try:
           content = await service.create(data)
           return ContentResponse(**content.dict())
       except ValidationError as e:
           raise HTTPException(status_code=400, detail=str(e))
       except Exception as e:
           logger.error(f"Error creating content: {str(e)}")
           raise HTTPException(status_code=500, detail="Internal server error")
   ```

4. **依赖注入**
   ```python
   from fastapi import Depends

   async def get_db_session() -> AsyncGenerator:
       async with SessionLocal() as session:
           yield session

   async def get_service(session: AsyncSession = Depends(get_db_session)):
       return ContentService(session)

   @router.get("/")
   async def list_contents(
       service: ContentService = Depends(get_service)
   ) -> List[ContentResponse]:
       contents = await service.list()
       return [ContentResponse(**c.dict()) for c in contents]
   ```

---

## API 设计检查清单

在创建新端点前检查：

- [ ] 端点路径遵循 RESTful 规范
- [ ] 使用正确的 HTTP 方法
- [ ] 定义了清晰的请求和响应模型
- [ ] 定义了所有可能的错误情况
- [ ] 提供了使用示例
- [ ] 编写了 OpenAPI 文档
- [ ] 实现了参数验证
- [ ] 实现了错误处理
- [ ] 使用了正确的 HTTP 状态码
- [ ] 文件名遵循命名规范

