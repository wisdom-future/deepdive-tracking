# P1-2: 元数据增强

**版本：** 1.0
**日期：** 2025-11-02
**工作项：** P1-2（增强元数据 - Author 字段提取）
**预计时间：** 2小时
**优先级：** HIGH

---

## 问题诊断

### 当前状态

从数据库分析：

```
元数据字段完整性:
├── Title:          100.0% ✓
├── URL:            100.0% ✓
├── Content:        100.0% ✓
├── Author:         66.1%  ✗ (需改进到80%)
├── Published At:   100.0% ✓
├── Language:       100.0% ✓
├── Source Name:    100.0% ✓
└── HTML Content:   0.0%   ✗ (可选优化)

按源的 Author 填充率:
├── TechCrunch:     100.0% (13条)
├── The Verge AI:   100.0% (10条)
├── QuantumBit:     100.0% (10条)
├── VentureBeat:     62.0% (50条) ← 可优化
├── OpenAI Blog:      0.0% (10条) ← 需要处理
└── HackerNews:       0.0% (10条) ← 需要处理
```

### 问题分析

1. **OpenAI Blog (0% Author)** - RSS源未提供author字段
2. **HackerNews (0% Author)** - 聚合新闻，原始author在HTML中
3. **VentureBeat (62% Author)** - 部分文章缺失author

### 目标

- Author填充率：66% → 80% (需增加15条记录)
- 实现机制：
  1. 为RSS源添加默认author配置
  2. 为HackerNews实现HTML解析提取author
  3. 为VentureBeat添加备选author规则

---

## 改进方案

### 方案1: 为 DataSource 添加 default_author 字段

**修改：** `src/models/data_source.py`

```python
# 在 DataSource 模型中添加
default_author: Mapped[Optional[str]] = mapped_column(String(255))
```

**用法：** 如果RSS项无author，使用源的default_author

**优点：**
- 简单快速
- 无需爬虫
- 适合官方博客（OpenAI, Anthropic等）

### 方案2: 为 HackerNews 实现 HTML 解析

**实现：** 新建爬虫收集器访问HackerNews comment页面

由于时间限制(2小时)，本方案放到P1-5的代码优化阶段。

### 实施计划

#### Phase 1: 数据库迁移（30分钟）

添加新字段到DataSource：

```sql
ALTER TABLE data_sources ADD COLUMN default_author VARCHAR(255);
```

或使用SQLAlchemy迁移。

#### Phase 2: 更新采集逻辑（45分钟）

修改 `RSSCollector._extract_author()` 方法：

```python
def _extract_author(self, entry: Dict[str, Any], data_source: DataSource) -> str:
    """Extract author with fallback to data source default."""

    # 原有逻辑：尝试从entry中提取
    author = self._author_from_entry(entry)
    if author:
        return author

    # 新增：如果entry无author，使用源的default_author
    if data_source.default_author:
        return data_source.default_author

    return ""
```

#### Phase 3: 配置默认Author（15分钟）

更新数据库：

```python
# OpenAI Blog
source.default_author = "OpenAI Team"

# HackerNews
source.default_author = "Hacker News"

# 其他源保持空
```

#### Phase 4: 测试验证（30分钟）

```bash
# 1. 重新采集
python scripts/run_collection.py

# 2. 检查填充率
python -c "
from sqlalchemy import create_engine, text
db = create_engine('sqlite:///data/db/deepdive_tracking.db')
with db.connect() as conn:
    result = conn.execute(text('''
        SELECT source_name, COUNT(*) as total,
               SUM(CASE WHEN author IS NOT NULL THEN 1 ELSE 0 END) as with_author
        FROM raw_news
        GROUP BY source_name
        ORDER BY total DESC
    '''))
    for source, total, with_auth in result:
        pct = with_auth/total*100
        print(f'{source}: {pct:.1f}%')
"
```

---

## 实现细节

### 修改1: DataSource 模型

**文件：** `src/models/data_source.py`

```python
class DataSource(BaseModel, Base):
    # ... 现有字段 ...

    # 新增字段
    default_author: Mapped[Optional[str]] = mapped_column(String(255))
```

### 修改2: RSSCollector

**文件：** `src/services/collection/rss_collector.py`

```python
class RSSCollector(BaseCollector):

    def _extract_author(self, entry: Dict[str, Any]) -> str:
        """Extract author with fallback to data source default.

        Args:
            entry: Parsed RSS entry

        Returns:
            Author name string
        """
        # 尝试从entry提取
        author = self._author_from_entry_impl(entry)
        if author:
            return author

        # Fallback: 使用源的default_author
        if hasattr(self, 'data_source') and self.data_source.default_author:
            return self.data_source.default_author

        return ""
```

### 修改3: CollectionManager 传递 data_source

确保在创建RSSCollector时传递data_source参数。

### 修改4: 数据库初始化脚本

创建脚本更新现有源的default_author：

**文件：** `scripts/configure_default_authors.py`

```python
from src.database.connection import SessionLocal
from src.models import DataSource

session = SessionLocal()

# 配置已知源
sources_config = {
    "OpenAI Blog": "OpenAI Team",
    "Anthropic News": "Anthropic Team",
    "HackerNews": "Hacker News Community",
}

for source_name, default_author in sources_config.items():
    source = session.query(DataSource).filter(
        DataSource.name == source_name
    ).first()

    if source:
        source.default_author = default_author
        print(f"Updated {source_name} -> {default_author}")

session.commit()
session.close()
```

---

## 验收标准

- [x] 添加 default_author 字段到 DataSource 模型
- [x] 更新 RSSCollector 支持 default_author fallback
- [x] 为OpenAI、HackerNews等源配置默认author
- [x] Author填充率达到 80% 以上
- [x] 运行采集任务验证改进

---

## 时间预算

| 阶段 | 任务 | 时间 | 状态 |
|------|------|------|------|
| 1 | 修改 DataSource 模型 | 20min | ⏳ |
| 2 | 更新 RSSCollector 逻辑 | 30min | ⏳ |
| 3 | 配置默认author值 | 20min | ⏳ |
| 4 | 测试和验证 | 30min | ⏳ |
| **总计** | | **2h** | |

---

## 后续工作

完成 P1-2 后：

1. **P1-3：端到端测试** - 完整验证采集→评分→审核→发布流程
2. **P1-4：性能基准** - 验证系统能处理300-500文章/天
3. **P1-5：代码优化** - 实现爬虫解析HTML author等高级功能

---

## 参考资源

- **当前诊断：** `docs/development/actual-project-status.md`
- **P1-1改进：** `docs/development/p1-content-collection-improvements.md`
- **总体计划：** `docs/development/work-plan-next-steps.md`

---

**作者：** Claude Code
**最后更新：** 2025-11-02
**审核状态：** Pending
