# 数据库查询指南

## 快速查看数据的方法

你现在可以直接通过API查看数据库中的数据。无需复杂的数据库工具！

### 方法1️⃣：在浏览器中直接查看（需要认证）

如果看到 403 Forbidden 错误，请使用方法2（命令行）。

**查看已处理的新闻（带评分和摘要）：**
```
https://deepdive-tracking-orp2dcdqua-de.a.run.app/data/news?table=processed&limit=50&offset=0
```

**查看原始新闻：**
```
https://deepdive-tracking-orp2dcdqua-de.a.run.app/data/news?table=raw&limit=50&offset=0
```

⚠️ 如果浏览器显示 403 Forbidden，请改用方法2命令行查询

---

### 方法2️⃣：使用命令行查询

**查询已处理新闻（前20条）：**

```bash
SERVICE_URL="https://deepdive-tracking-orp2dcdqua-de.a.run.app"
ID_TOKEN=$(gcloud auth print-identity-token --audiences="$SERVICE_URL" 2>/dev/null)

curl -X GET \
  -H "Authorization: Bearer $ID_TOKEN" \
  "$SERVICE_URL/data/news?table=processed&limit=20&offset=0"
```

**查询原始新闻（前20条）：**

```bash
SERVICE_URL="https://deepdive-tracking-orp2dcdqua-de.a.run.app"
ID_TOKEN=$(gcloud auth print-identity-token --audiences="$SERVICE_URL" 2>/dev/null)

curl -X GET \
  -H "Authorization: Bearer $ID_TOKEN" \
  "$SERVICE_URL/data/news?table=raw&limit=20&offset=0"
```

---

### API参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `table` | 查询表名 | processed | raw 或 processed |
| `limit` | 返回记录数 | 100 | 1-100 |
| `offset` | 分页偏移 | 0 | 0, 10, 20... |

**示例URL：**
- `?table=processed&limit=10&offset=0` - 查询前10条已处理新闻
- `?table=raw&limit=50&offset=50` - 查询第51-100条原始新闻
- `?table=processed&limit=5&offset=5` - 查询第6-10条已处理新闻

---

## 数据说明

### 已处理新闻表 (processed)

返回的数据包含：

```json
{
  "id": "新闻ID",
  "raw_news_id": "对应原始新闻ID",
  "title": "新闻标题",
  "score": 75.0,              // AI评分 0-100
  "category": "tech_breakthrough", // 分类
  "summary_zh": "中文摘要",
  "summary_en": "英文摘要",
  "confidence": 0.85,         // 置信度
  "created_at": "创建时间"
}
```

### 原始新闻表 (raw)

返回的数据包含：

```json
{
  "id": "新闻ID",
  "title": "新闻标题",
  "url": "新闻链接",
  "source_name": "来源",
  "author": "作者",
  "published_at": "发布时间",
  "status": "raw",
  "is_duplicate": false
}
```

---

## 数据统计

API响应中包含的统计信息：

```json
{
  "status": "success",
  "table": "processed",
  "total_records": 10,        // 表中总记录数
  "returned_records": 5,      // 本次返回的记录数
  "limit": 5,
  "offset": 0,
  "data": [...],
  "timestamp": "2025-11-03T23:41:08.801627"
}
```

---

## 当前数据库状态

```
数据库中现有：
- 原始新闻: 10 条
- 已处理新闻: 10 条
```

### 示例新闻

| ID | 标题 | 来源 | 评分 |
|----|----|------|------|
| 1 | AWS and OpenAI announce multi-year strategic partnership | OpenAI Blog | 75.0 |
| 2 | Expanding Stargate to Michigan | OpenAI Blog | 75.0 |
| 3 | Introducing Aardvark: OpenAI's agentic security researcher | OpenAI Blog | 75.0 |
| 4 | How we built OWL | OpenAI Blog | 75.0 |
| 5 | Technical Report: gpt-oss-safeguard | OpenAI Blog | 75.0 |

---

## 故障排除

### Q: 浏览器中看到 403 Forbidden 错误？
A: 这是正常的，/data/news 端点需要认证。请使用方法2（命令行）查询：

```bash
SERVICE_URL="https://deepdive-tracking-orp2dcdqua-de.a.run.app"
ID_TOKEN=$(gcloud auth print-identity-token --audiences="$SERVICE_URL" 2>/dev/null)
curl -H "Authorization: Bearer $ID_TOKEN" "$SERVICE_URL/data/news?table=processed&limit=50"
```

### Q: 得到 401 错误？
A: 认证令牌过期。重新运行 `gcloud auth print-identity-token` 获取新令牌。

### Q: 得到 404 错误？
A: 端点名称错误。应该是 `/data/news` 而不是其他名称。

### Q: 想要查看更多数据？
A: 增加 `limit` 参数（最多100条），或使用 `offset` 分页。

### Q: 想导出全部数据？
A: 可以循环查询：offset=0, offset=100, offset=200...

---

## API 端点总结

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/data/news` | 查询新闻数据 |
| GET | `/diagnose/database` | 数据库诊断信息 |
| POST | `/publish/email` | 发布到邮件 |
| POST | `/publish/github` | 发布到 GitHub |
| POST | `/trigger-workflow` | 触发完整工作流 |
| POST | `/init-db` | 初始化数据库 |
| GET | `/health` | 健康检查 |

---

**最后更新:** 2025-11-03
**服务地址:** https://deepdive-tracking-orp2dcdqua-de.a.run.app
