# 验证脚本 (Verification Scripts)

**用途：** 查看和验证采集、评分结果

---

## 📋 脚本列表

### 1. `view_summary.py` - 数据库摘要 (推荐用于 P1-3 第三步)

**功能：**
- 显示 raw_news 表统计
- 显示 processed_news 表统计
- 显示 data_sources 配置
- 显示 TOP 10 最新新闻
- 按源的详细统计
- 提供 SQL 查询示例

**运行：**
```bash
python view_summary.py
```

**输出示例：**
```
[1] RAW_NEWS Table Summary
Total articles:       115
  - Status 'raw':     15 (待处理)
  - Status 'proc':    100 (已评分)
  - With author:      86 (74.8%)
Avg content length:   4921 chars
Unique sources:       15

[2] PROCESSED_NEWS Table Summary
Total scored:         100
Avg score:            76/100
Unique categories:    8

[3] DATA_SOURCES Configuration
Total sources:        15
Enabled:              15
With default author:  3

[4] TOP 10 Latest News
1. 标题 (来源) (作者) [Content: 5234 chars]
   Fetched: 2025-11-02 21:10:00

2. 标题 (来源) (作者) [Content: 4156 chars]
   Fetched: 2025-11-02 21:09:45
...

[5] Statistics by Data Source
Source                 | Total | Author % | Avg Len
───────────────────────────────────────────────
TechCrunch             | 20    | 100.0%   | 5234
VentureBeat AI         | 18    | 88.9%    | 4856
The Verge AI           | 12    | 100.0%   | 4123
...

[6] Quick Query Commands
[SQL 示例列表]

[Summary]
Collection Status: 115 articles, 100 scored (86.96%)
Metadata Quality:  86 articles have author (74.78%)
✓ Ready for P1-3 end-to-end testing!
```

**耗时：** 1-2 秒

**何时使用：**
- P1-3 第三步（最后验证）
- 查看整体统计
- 导出 SQL 查询

---

### 2. `demo_mock.py` - 模拟演示

**功能：**
- 完整的采集 → 评分 → 结果流程演示
- 使用模拟数据（无需真实 API）
- 快速验证系统设计
- 离线演示

**运行：**
```bash
python demo_mock.py
```

**输出示例：**
```
DeepDive Tracking - Mock Demo
════════════════════════════════

[1] 模拟采集新闻...
    采集源: 5 个
    新闻数: 50 条
    成功: ✓

[2] 模拟评分...
    评分: 50/50 (100%)
    平均分: 76/100

[3] 显示结果...
    TOP 10 新闻:
    1. [92/100] 标题 A...
    2. [88/100] 标题 B...
    ...

演示完成！✓
```

**耗时：** 5-10 秒

**何时使用：**
- 离线演示（无需 API Key）
- 验证系统流程
- 教学和演示

---

## 🚀 使用流程

### P1-3 第三步（推荐）
```bash
cd scripts/03-verification
python view_summary.py
```

### 离线演示
```bash
python demo_mock.py
```

---

## 📊 数据库查询参考

### 快速查询示例

#### 1. 查看 raw_news 统计
```sql
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN status='raw' THEN 1 END) as raw,
  COUNT(CASE WHEN status='processed' THEN 1 END) as processed
FROM raw_news;
```

#### 2. 查看 TOP 10 新闻
```sql
SELECT title, source_name, author, LENGTH(content)
FROM raw_news
ORDER BY fetched_at DESC
LIMIT 10;
```

#### 3. 按源统计
```sql
SELECT
  source_name,
  COUNT(*) as count,
  COUNT(CASE WHEN author IS NOT NULL THEN 1 END) as with_author
FROM raw_news
GROUP BY source_name
ORDER BY count DESC;
```

#### 4. 查看评分结果
```sql
SELECT
  r.title,
  p.score,
  p.category,
  p.summary
FROM raw_news r
JOIN processed_news p ON r.id = p.raw_news_id
ORDER BY p.score DESC
LIMIT 10;
```

#### 5. 查找未评分的新闻
```sql
SELECT title, source_name
FROM raw_news
WHERE id NOT IN (SELECT raw_news_id FROM processed_news);
```

---

## 🎯 验证成功标准

✅ P1-3 完成标准：
- [ ] raw_news: 100+ 条
- [ ] processed_news: > 95 条（已评分）
- [ ] Author 填充率: > 75%
- [ ] 内容长度: 平均 > 3000 字
- [ ] TOP 10: 正确显示最新文章

---

## 📊 数据质量检查清单

### 内容质量
- [ ] Content 不为空 (100%)
- [ ] Content > 100 字 (> 80%)
- [ ] Content > 300 字 (> 50%)

### 元数据质量
- [ ] Title 不为空 (100%)
- [ ] URL 不为空 (100%)
- [ ] Author 不为空 (> 75%)
- [ ] Language 检测 (> 90%)

### 评分质量
- [ ] Score 在 0-100 范围 (100%)
- [ ] 有分类标签 (100%)
- [ ] 有摘要文本 (100%)

---

## 🔍 常见查询

### 找出问题数据

#### 内容为空的文章
```sql
SELECT title, source_name FROM raw_news WHERE content IS NULL OR content = '';
```

#### 缺少 author 的文章
```sql
SELECT title, source_name FROM raw_news WHERE author IS NULL OR author = '';
```

#### 未评分的文章
```sql
SELECT title, source_name FROM raw_news
WHERE id NOT IN (SELECT raw_news_id FROM processed_news);
```

#### 评分很低的文章 (< 60)
```sql
SELECT r.title, p.score, p.summary
FROM raw_news r
JOIN processed_news p ON r.id = p.raw_news_id
WHERE p.score < 60
ORDER BY p.score;
```

---

## ⚠️ 常见问题

### Q1: TOP 10 显示不了

**症状：** view_summary.py 输出中没有 TOP 10

**原因：** 数据库中没有新闻数据

**解决：**
```bash
# 先运行采集
cd scripts/01-collection
python collect_news.py

# 再运行验证
cd scripts/03-verification
python view_summary.py
```

### Q2: Author 填充率很低

**症状：** Author % 显示很低（< 50%）

**原因：** 某些源没有配置 default_author

**解决：**
```bash
# 运行配置脚本
cd scripts/00-setup
python 2_configure_authors.py

# 再重新采集
cd scripts/01-collection
python collect_news.py
```

### Q3: 内容长度很短

**症状：** Avg content length 显示 < 500

**原因：** 采集的内容不完整

**解决：** 这是正常的。系统已在 P1-1 中改进了内容提取。

---

## 📝 导出数据

### 导出为 CSV

```bash
# 导出所有新闻
sqlite3 data/db/deepdive_tracking.db \
  "SELECT * FROM raw_news" > export_raw_news.csv

# 导出已评分的新闻
sqlite3 data/db/deepdive_tracking.db \
  "SELECT r.*, p.score, p.category FROM raw_news r
   JOIN processed_news p ON r.id = p.raw_news_id" > export_scored.csv
```

### 导出为 JSON

```bash
# 使用 Python 导出
python << 'PYTHON'
import sqlite3
import json

conn = sqlite3.connect('data/db/deepdive_tracking.db')
cursor = conn.cursor()

# 查询数据
cursor.execute('''
  SELECT title, source_name, author, score
  FROM raw_news r
  JOIN processed_news p ON r.id = p.raw_news_id
  LIMIT 10
''')

# 转为 JSON
data = [dict(zip([col[0] for col in cursor.description], row))
        for row in cursor.fetchall()]

with open('export.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✓ 导出成功: export.json")
PYTHON
```

---

## 🎓 学习资源

- **数据库架构：** docs/tech/database-schema.md
- **系统设计：** docs/tech/system-design-summary.md
- **完整流程：** docs/development/p1-ready-for-testing.md

---

**最后更新：** 2025-11-02
**脚本状态：** ✅ 生产就绪
