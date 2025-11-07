# P0修复验证指南：去重机制修复

## 📋 修复内容总结

本次P0修复解决了数据采集功能中**去重机制完全失效**的严重问题：

### ✅ 已完成的修改

1. **数据模型增强** - `src/models/collection/raw_news.py`
   - 添加 `content_simhash` 字段（BigInteger，带索引）
   - 用于存储内容的64位Simhash指纹

2. **数据库迁移** - `alembic/versions/003_add_content_simhash.py`
   - 新增 `content_simhash` 列
   - 创建索引 `ix_raw_news_content_simhash`

3. **去重逻辑重构** - `src/services/collection/collection_manager.py`
   - **修复前问题**：
     - ❌ Simhash计算了但从未使用
     - ❌ 重复记录仍被保存（只打标记）
     - ❌ 无内容相似度检测

   - **修复后行为**：
     - ✅ 精确去重：检查URL/Title hash
     - ✅ 相似去重：检查Content Simhash（Hamming距离≤3）
     - ✅ 跳过重复：不保存重复记录到数据库
     - ✅ 存储Simhash：保存每条记录的simhash值

4. **相似度检测方法** - `_find_similar_content()`
   - 基于Hamming距离检测内容相似度
   - 时间窗口优化（默认7天）
   - 阈值可配置（默认3位不同）

---

## 🚀 部署步骤

### 1. 运行数据库迁移

```bash
# 进入项目目录
cd D:\projects\deepdive-tracking

# 运行迁移（添加content_simhash字段）
alembic upgrade head

# 验证迁移成功
alembic current
# 应显示: 003 (head)
```

**预期输出：**
```
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, Add content_simhash field to RawNews table for similarity detection.
```

---

### 2. 验证数据库结构

```bash
# 连接数据库（根据您的配置调整）
psql -d deepdive_tracking

# 检查字段是否添加
\d raw_news

# 应看到：
# content_simhash | bigint | | |
```

**或使用SQL查询：**
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'raw_news'
  AND column_name = 'content_simhash';
```

**预期结果：**
```
  column_name    | data_type | is_nullable
-----------------+-----------+-------------
 content_simhash | bigint    | YES
```

---

## 🧪 功能测试

### 测试1：清空数据并进行首次采集

```bash
# ⚠️ 警告：这会删除所有raw_news数据，仅在测试环境执行！
psql -d deepdive_tracking -c "TRUNCATE raw_news RESTART IDENTITY CASCADE;"

# 运行采集脚本
python scripts/collection/collect_news.py

# 查看采集统计
```

**预期输出示例：**
```
INFO - Collection from TechCrunch: 50 collected, 45 new, 5 duplicates
INFO - Collection from VentureBeat: 30 collected, 20 new, 10 duplicates
```

**验证点：**
- ✅ `new` 数量 = 数据库实际插入数量
- ✅ `duplicates` 数量 = 被跳过的重复数量

---

### 测试2：验证精确去重（URL/Title Hash）

```sql
-- 查询数据库中的记录数
SELECT COUNT(*) as total_records FROM raw_news;

-- 查询有多少唯一的hash
SELECT COUNT(DISTINCT hash) as unique_hashes FROM raw_news;

-- 如果去重有效，这两个数字应该相等
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT hash) as unique_hashes,
    COUNT(*) - COUNT(DISTINCT hash) as hash_collisions
FROM raw_news;
```

**预期结果：**
```
 total_records | unique_hashes | hash_collisions
---------------+---------------+-----------------
           150 |           150 |               0
```

---

### 测试3：验证Simhash相似度去重

```sql
-- 检查有多少记录有simhash
SELECT
    COUNT(*) as total,
    COUNT(content_simhash) as with_simhash,
    COUNT(*) - COUNT(content_simhash) as without_simhash,
    ROUND(100.0 * COUNT(content_simhash) / COUNT(*), 2) as simhash_coverage
FROM raw_news;
```

**预期结果：**
```
 total | with_simhash | without_simhash | simhash_coverage
-------+--------------+-----------------+------------------
   150 |          145 |               5 |            96.67
```

**说明：**
- 有内容的记录应该有simhash
- 无内容或内容为空的记录simhash为NULL（正常）

---

### 测试4：重复采集测试（关键测试！）

```bash
# 第一次采集
python scripts/collection/collect_news.py

# 记录统计：假设采集到150条，新增100条，重复50条

# 立即第二次采集（相同数据源）
python scripts/collection/collect_news.py

# 预期统计：采集到150条，新增0条，重复150条
```

**验证SQL：**
```sql
-- 查询数据库记录数，应该保持不变
SELECT COUNT(*) FROM raw_news;

-- 第一次采集后：100条
-- 第二次采集后：仍然100条（不应增加）
```

**预期行为：**
- ✅ 第二次采集检测到所有内容都是重复
- ✅ 数据库记录数不增加
- ✅ 日志显示 `duplicates` 数量等于 `collected` 数量

---

### 测试5：相似内容检测

手动测试相似内容是否被正确检测：

```python
# 创建测试脚本：test_simhash_dedup.py
from src.database import SessionLocal
from src.services.collection.deduplication import ContentDeduplicator

# 准备两篇相似内容
content1 = "OpenAI releases GPT-5 with breakthrough performance in AI reasoning tasks."
content2 = "OpenAI launches GPT-5 with significant improvements in AI reasoning capabilities."

dedup = ContentDeduplicator()

simhash1 = dedup.compute_simhash(content1)
simhash2 = dedup.compute_simhash(content2)

# 计算Hamming距离
hamming_distance = bin(simhash1 ^ simhash2).count('1')

print(f"Simhash 1: {simhash1}")
print(f"Simhash 2: {simhash2}")
print(f"Hamming Distance: {hamming_distance}")
print(f"Will be considered duplicate: {hamming_distance <= 3}")
```

**预期结果：**
- 相似内容的Hamming距离应该 ≤ 3
- 不同内容的Hamming距离应该 > 3

---

## 📊 数据质量验证SQL

### 检查去重效果

```sql
-- 1. 总体去重统计
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT hash) as unique_by_hash,
    COUNT(DISTINCT content_simhash) as unique_by_simhash,
    MIN(fetched_at) as first_collection,
    MAX(fetched_at) as last_collection
FROM raw_news;

-- 2. 按数据源统计
SELECT
    source_name,
    COUNT(*) as total,
    COUNT(DISTINCT hash) as unique_hash,
    COUNT(content_simhash) as with_simhash,
    ROUND(AVG(LENGTH(content)), 0) as avg_content_length
FROM raw_news
GROUP BY source_name
ORDER BY total DESC;

-- 3. 检查是否还有is_duplicate=true的记录（不应该有）
SELECT COUNT(*) as duplicate_marked_records
FROM raw_news
WHERE is_duplicate = true;
-- 应返回 0

-- 4. 检查simhash覆盖率
SELECT
    CASE
        WHEN content_simhash IS NOT NULL THEN 'With Simhash'
        ELSE 'Without Simhash'
    END as simhash_status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM raw_news
GROUP BY simhash_status;

-- 5. 检查近期采集的去重情况（最近24小时）
SELECT
    DATE_TRUNC('hour', fetched_at) as collection_hour,
    COUNT(*) as records_saved
FROM raw_news
WHERE fetched_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', fetched_at)
ORDER BY collection_hour DESC;
```

---

## 🔍 问题排查

### 问题1：迁移失败

**症状：** `alembic upgrade head` 报错

**排查步骤：**
```bash
# 检查当前版本
alembic current

# 查看迁移历史
alembic history

# 如果卡在旧版本，手动运行
alembic upgrade 003
```

**解决方案：**
- 检查数据库连接配置
- 确认是否有足够的数据库权限
- 查看 `alembic/versions/003_add_content_simhash.py` 是否有语法错误

---

### 问题2：Simhash全部为NULL

**症状：** 采集后所有 `content_simhash` 都是 NULL

**排查步骤：**
```sql
-- 检查有多少记录有内容
SELECT
    COUNT(*) as total,
    COUNT(content) as with_content,
    COUNT(CASE WHEN LENGTH(content) > 0 THEN 1 END) as with_non_empty_content
FROM raw_news;
```

**可能原因：**
1. RSS源没有提供内容（只有摘要）
2. 内容提取失败
3. `deduplicator.compute_simhash()` 出错

**解决方案：**
- 检查采集器日志
- 验证RSS源是否提供内容
- 测试 `ContentDeduplicator.compute_simhash()` 方法

---

### 问题3：重复内容仍被保存

**症状：** 第二次采集后记录数增加

**排查步骤：**
```python
# 测试去重逻辑
from src.database import SessionLocal
from src.services.collection.collection_manager import CollectionManager

db = SessionLocal()
manager = CollectionManager(db)

# 测试查找相似内容
test_simhash = 12345678901234567890  # 替换为真实simhash
similar = manager._find_similar_content(test_simhash)
print(f"Found {len(similar)} similar items")
```

**可能原因：**
1. 时间窗口设置（默认7天）过短
2. Hamming阈值（默认3）过严格
3. 内容变化导致simhash差异较大

**解决方案：**
- 调整 `time_window_days` 参数（增加到14或30天）
- 调整 `hamming_threshold` 参数（增加到5或6）

---

### 问题4：性能问题

**症状：** 采集速度变慢

**排查步骤：**
```sql
-- 检查索引是否存在
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'raw_news';

-- 应该看到：
-- ix_raw_news_content_simhash
```

**可能原因：**
1. `_find_similar_content()` 查询整个表
2. 索引未创建或未使用

**解决方案：**
```sql
-- 手动创建索引（如果缺失）
CREATE INDEX ix_raw_news_content_simhash ON raw_news(content_simhash);

-- 分析表统计信息
ANALYZE raw_news;
```

---

## 📈 性能基准

### 预期性能指标

| 指标 | 修复前 | 修复后 | 改善 |
|------|--------|--------|------|
| 数据库膨胀 | 300条→300条保存 | 300条→150条保存 | -50% |
| 去重准确率 | 0% (全部保存) | >95% | +95% |
| 采集速度 | 100条/分钟 | 80-90条/分钟 | -10-20% |
| 存储空间 | 100% | 50-60% | -40-50% |

**说明：**
- 采集速度略有下降（增加了相似度检查）
- 存储空间大幅减少（不保存重复）
- 后续AI处理成本降低（无需处理重复）

---

## ✅ 验收标准

修复被认为成功，当且仅当：

1. ✅ 数据库迁移成功，`content_simhash` 字段存在
2. ✅ 采集后 >90% 的记录有有效的 simhash 值
3. ✅ 重复采集时，数据库记录数不增加
4. ✅ 相同内容只保存一次（无论来源）
5. ✅ 相似内容被正确识别为重复
6. ✅ 日志中 `duplicates` 统计准确
7. ✅ 无 `is_duplicate=true` 的记录存在
8. ✅ 采集性能下降 < 20%

---

## 🎯 下一步（可选优化）

修复完成后，可以考虑以下优化（不在P0范围内）：

1. **P1优化：全文抓取**
   - 对RSS摘要进行全文抓取
   - 提高内容完整性

2. **性能优化：**
   - 使用SimHash索引算法（LSH）加速查询
   - 批量检查相似度，减少数据库查询

3. **监控告警：**
   - 采集去重率监控
   - 异常重复率告警

4. **数据清理：**
   - 删除历史重复记录
   - 重新计算旧记录的simhash

---

## 📞 支持

如有问题，请：

1. 查看采集日志：`logs/collection_*.log`
2. 检查数据库错误：`psql` 错误信息
3. 运行验证SQL检查数据质量
4. 提供详细的错误信息和日志

---

## 📝 修改文件清单

```
修改的文件：
✅ src/models/collection/raw_news.py
✅ src/services/collection/collection_manager.py

新增的文件：
✅ alembic/versions/003_add_content_simhash.py
✅ P0_DEDUPLICATION_FIX_VERIFICATION.md (本文档)

需要运行：
⚠️ alembic upgrade head

需要安装（如未安装）：
⚠️ pip install black flake8 mypy (代码质量检查工具)
```

---

**修复完成时间：** 2025-11-07
**预计测试时间：** 30-60分钟
**风险等级：** 🟡 中等（需要数据库迁移）

**建议：** 先在开发/测试环境验证，确认无误后再部署到生产环境。
