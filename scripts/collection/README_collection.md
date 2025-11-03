# 采集脚本 (Collection Scripts)

**用途：** 从 15 个数据源采集 AI 新闻

---

## 📋 脚本列表

### 1. `collect_news.py` - 主采集脚本 (推荐用于 P1-3 第一步)

**功能：**
- 从 15 个数据源采集新闻
- 自动去重（基于 SHA256 hash）
- 保存到 raw_news 表
- 显示采集统计
- 显示 TOP 10 最新新闻
- 提供 SQL 查询示例

**运行：**
```bash
python collect_news.py
```

**输出示例：**
```
[1] 连接数据库...OK
[2] 获取数据源...15 个源已启用
[3] 开始采集...
    异步并发采集中...
[4] 采集统计
    总采集: 95 条
    新增: 77 条
    重复: 18 条
[5] 最新新闻 TOP 10
    1. AI 新突破：Google DeepMind... (TechCrunch)
    2. OpenAI 发布新模型... (VentureBeat)
    ...
[6] 数据库查询命令
    [SQL 示例]
[7] 下一步建议
```

**耗时：** 30-60 秒

**何时使用：**
- P1-3 第一步
- 定期采集新闻
- 验证采集功能

---

### 2. `diagnose_sources.py` - 数据源诊断

**功能：**
- 测试每个数据源的连接
- 验证 HTTP 状态
- 检查 RSS 格式
- 显示错误详情
- 找出无效的源

**运行：**
```bash
python diagnose_sources.py
```

**输出示例：**
```
诊断数据源...
  OpenAI Blog:         ✓ OK (HTTP 200)
  TechCrunch:         ✓ OK (HTTP 200)
  Google DeepMind:    ✗ ERROR (HTTP 404)
  Meta AI Research:   ⚠ TIMEOUT (30s)
  ...

结果统计:
  正常: 12/15 (80%)
  错误: 2/15 (13%)
  超时: 1/15 (7%)

建议:
  • 禁用失效的源
  • 更新失效源的 URL
  • 检查网络连接
```

**耗时：** 30-60 秒

**何时使用：**
- 采集失败时诊断问题
- 定期检查源可用性
- 优化数据源列表

---

## 🚀 使用流程

### 第一次使用
```bash
# 确保数据源已初始化
cd scripts/00-setup
python 1_init_data_sources.py
python 2_configure_authors.py

# 然后采集
cd scripts/01-collection
python collect_news.py
```

### P1-3 第一步
```bash
cd scripts/01-collection
python collect_news.py
```

### 诊断问题
```bash
python diagnose_sources.py
```

---

## 📊 采集统计说明

### "总采集" (Total Collected)
RSS 源返回的总条目数。某些源可能返回多达 100+ 条，但系统会限制为 50 条/源。

### "新增" (New)
经过去重后，新保存到数据库的条数。

### "重复" (Duplicates)
根据标题 + URL hash 判断为重复，被排除的条数。

### 示例
```
总采集: 95
  源A: 20 条  → 新增 15 条, 重复 5 条
  源B: 18 条  → 新增 18 条, 重复 0 条
  源C: 12 条  → 新增 12 条, 重复 0 条
  ...
  小计: 新增 77 条, 重复 18 条
```

---

## 🔍 数据采集细节

### 采集来源

| 源名 | 类型 | URL | 优先级 |
|------|------|-----|--------|
| OpenAI Blog | RSS | https://openai.com/... | 9 |
| TechCrunch AI | RSS | https://techcrunch.com/... | 7 |
| VentureBeat AI | RSS | https://venturebeat.com/... | 7 |
| ... | ... | ... | ... |

### 采集字段

从 RSS 提取的字段：
```
title        - 文章标题（必需）
url          - 源链接（必需）
content      - 文章内容（可选 → 多源提取）
author       - 作者名（可选 → fallback 到 default_author）
published_at - 发布时间（可选 → fallback 到当前时间）
language     - 语言（自动检测）
```

### 去重机制

```
hash = SHA256(title.lower() + "|" + url.lower())
↓
检查 raw_news 表中是否已存在此 hash
↓
如果存在 → 跳过（重复）
如果不存在 → 保存新记录
```

---

## 🎯 采集成功标准

✅ P1-3 验收标准：
- [ ] 采集 > 100 条新闻
- [ ] 新增 > 80 条（新的）
- [ ] 无采集错误（或错误 < 2 个）
- [ ] TOP 10 正确显示

---

## ⚠️ 常见问题

### Q1: 采集很慢

**症状：** 脚本运行超过 2 分钟

**原因：** 网络慢或源响应慢

**解决：**
```bash
# 运行诊断找出慢源
python diagnose_sources.py

# 看诊断结果，找出超时的源
# 可以暂时禁用这些源
```

### Q2: 采集失败，HTTP 404

**症状：** 某些源无法采集

**原因：** 源 URL 失效或更改

**解决：**
```bash
# 运行诊断
python diagnose_sources.py

# 更新失效源的 URL
# 或者禁用失效的源
```

### Q3: 重复太多

**症状：** "重复: 50 条" （太多）

**原因：** 同一源的文章未更新，或数据库已有大量历史数据

**解决：** 正常现象。系统工作正常。
- 第一次采集会有重复，因为已有历史数据
- 之后的采集重复会更少

---

## 🔧 高级选项

### 修改采集数量

编辑 `collect_news.py`，找到这一行：
```python
max_items = 50  # 每个源最多采集 50 条
```

改为你想要的数字，比如：
```python
max_items = 100  # 采集 100 条
```

### 采集特定源

修改 SQL 过滤条件：
```python
# 只采集启用的源
sources = db.query(DataSource).filter(DataSource.is_enabled == True)

# 可以改为只采集特定源
sources = db.query(DataSource).filter(
    DataSource.name.in_(['TechCrunch', 'VentureBeat'])
)
```

### 清空历史数据重新采集

```bash
# 小心！会删除所有数据
sqlite3 data/db/deepdive_tracking.db
> DELETE FROM raw_news;  -- 删除所有原始新闻
> DELETE FROM processed_news;  -- 删除所有评分结果

# 然后重新采集
python collect_news.py
```

---

## 📊 性能参考

| 项目 | 值 |
|------|-----|
| 采集 15 个源 | ~30-60 秒 |
| 并发级别 | 15 (每源一个) |
| 单源超时 | 30 秒 |
| 去重性能 | < 1ms per item |

---

## 🎓 学习资源

- **采集设计：** docs/tech/system-design-summary.md
- **数据库架构：** docs/tech/database-schema.md
- **完整流程：** docs/development/p1-ready-for-testing.md

---

**最后更新：** 2025-11-02
**脚本状态：** ✅ 生产就绪
