# 数据采集系统 - 3个致命问题诊断

**状态：** 🔴 严重 - 系统无法使用
**诊断日期：** 2025-11-02
**问题来源：** 用户在CLAUDE.md中的直接指责

---

## 问题总结

用户明确指出数据采集功能根本不能使用，存在3个巨大的致命问题：

```
整体而言，数据采集功能根本不能使用！！！
```

---

## 问题1：内容信息不完整

**问题陈述：**
> data_collection_raw_data集合中，各类数据基本没有有效的信息，
> 只存储了极其基本的信息，啥都没有

**具体表现：**
- ❌ 采集的新闻内容为空或不完整
- ❌ 缺少重要字段（作者、发布时间、内容摘要等）
- ❌ 存储的数据无法用于后续的AI评分和分析

**影响范围：**
- 无法为AI评分提供足够的上下文信息
- 生成的总结无法准确反映新闻内容
- 用户无法理解新闻的实际含义

**需要修复：**
1. 检查RSSCollector的内容提取逻辑
2. 验证爬虫选择器是否正确
3. 确保保存所有重要字段

---

## 问题2：资源引用缺失

**问题陈述：**
> data_collection_raw_data的数据表中，根本没有对resource的任何引用！

**具体表现：**
- ❌ RawNews表中缺少对DataSource的正确关联
- ❌ 采集来源信息不完整或不准确
- ❌ 无法追踪数据来自哪个具体的采集源

**当前数据模型分析：**
```python
# src/models/raw_news.py
source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False)
# ✅ 这个字段存在

# 但问题可能是：
# 1. 实际保存时没有设置source_id
# 2. 外键约束没有生效
# 3. DataSource记录不存在或被删除
```

**影响范围：**
- 无法根据来源过滤新闻
- 无法统计各来源的采集质量
- 无法管理来源配置和性能

**需要修复：**
1. 验证采集时是否正确设置了source_id
2. 检查外键约束是否被执行
3. 确保DataSource记录在采集前存在
4. 添加验证逻辑确保完整性

---

## 问题3：去重机制无效

**问题陈述：**
> resource-xxx的数据集合，存在大量的重复，
> 在业务代码上根本没有进行判重和去重

**具体表现：**
- ❌ 大量重复的新闻记录被存储
- ❌ 虽然有is_duplicate字段，但去重逻辑有问题
- ❌ 多次采集同一条新闻，都被当作新数据

**当前实现分析：**
```python
# src/models/raw_news.py
hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)

# ✅ hash字段存在且唯一
# ❌ 但是否被正确使用？

# src/services/collection/collection_manager.py
# 统计中有 total_duplicates，但去重逻辑可能不完整
```

**问题分析：**
1. Hash计算方式是否正确？
2. 是否在保存前检查重复？
3. 是否正确设置is_duplicate标志？
4. 同一条新闻从多个源采集，是否识别为重复？

**影响范围：**
- 数据库膨胀，存储大量重复数据
- 评分结果重复计算，浪费API成本
- 用户看到大量重复的新闻
- 数据分析结果失真

**需要修复：**
1. 验证hash值生成的正确性
2. 实现proper的去重算法
3. 处理不同来源的相同新闻
4. 清理已有的重复数据

---

## 诊断步骤

### 第一步：检查现有数据
```bash
# 连接到数据库并查询
sqlite3 data/db/tracking.db

# 查看raw_news表
SELECT id, source_id, title, content, hash, is_duplicate, created_at
FROM raw_news
LIMIT 10;

# 检查是否有内容
SELECT id, title, content IS NULL as no_content, length(content) as content_len
FROM raw_news;

# 检查source_id是否正确
SELECT id, source_id, COUNT(*) FROM raw_news GROUP BY source_id;

# 检查重复
SELECT hash, COUNT(*) as count FROM raw_news GROUP BY hash HAVING count > 1;
```

### 第二步：运行采集并观察
```bash
# 运行采集（如果实现了的话）
python -m src.scripts.run_collection

# 观察日志输出
# - 采集了多少条新闻
# - 识别了多少条重复
# - 错误是什么
```

### 第三步：检查采集代码
重点检查：
1. `src/services/collection/rss_collector.py` - 内容提取是否完整
2. `src/services/collection/collection_manager.py` - 去重逻辑
3. 采集任务的实现

---

## 修复优先级

**Critical (必须)：**
1. ✅ 第2问题 - 确保source_id被正确保存（影响可追踪性）
2. ✅ 第1问题 - 采集完整的新闻内容（影响AI评分质量）
3. ✅ 第3问题 - 实现有效的去重（影响数据质量和成本）

**Timeline：**
- 本任务：诊断具体原因，制定修复计划
- 下一任务：实施修复，验证有效性
- 再后一任务：运行真实数据采集，验证完整系统

---

## 当前状态总结

**已验证的工作部分：**
- ✅ 数据库模型定义完整
- ✅ AI评分系统工作正常
- ✅ API端点实现（虽然覆盖率低）

**确认不工作的部分：**
- ❌ 数据采集系统（3个问题）
- ❌ 端到端流程（缺少真实数据）
- ❌ 实际新闻评分（没有真实新闻）

**关键认识：**
> "用样本数据验证AI评分"不等于"系统能工作"

需要：
1. 修复数据采集
2. 采集真实新闻
3. 对真实新闻进行评分
4. 验证完整系统

---

## 下一步行动

1. **立即** - 运行诊断脚本查看数据库实际状况
2. **今天** - 定位具体的代码问题
3. **本周** - 实施修复
4. **验证** - 用真实新闻运行完整系统

---

**备注：** 本文档反映了用户的严厉但中肯的批评。
这正是我们需要关注的核心问题。
