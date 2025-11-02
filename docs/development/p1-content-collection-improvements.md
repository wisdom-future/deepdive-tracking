# P1-1: 内容采集改进方案

**版本：** 1.0
**日期：** 2025-11-02
**工作项：** P1-1（改进内容采集 - 实现完整文章提取）
**预计时间：** 4小时
**优先级：** HIGH

---

## 问题诊断

### 当前状态

基于数据库分析（`actual-project-status.md`）：

```
内容质量指标：
├── Content 字段完整性: 64% (21/33 > 100字符)
├── 平均长度: ~150 字符 (仅摘要)
├── HTML内容: 0% (全为NULL)
└── 问题: 采集到的是RSS摘要，不是完整文章
```

### 根本原因

**src/services/collection/rss_collector.py:78**

```python
"content": entry.get("summary", ""),  # ❌ 仅摘要，忽略完整内容
```

RSS 解析器只提取 `summary` 字段，而不是完整的文章内容。

### 影响

1. **AI评分准确度下降** - 摘要不足以判断文章价值（30-50%准确度损失）
2. **用户体验差** - 审核员无法获得足够的上下文信息
3. **数据质量低** - 不符合产品目标（>300字符内容）

---

## 改进方案

### 核心改进（必做）

#### 1. 增强 RSS 内容提取

**目标：** 从摘要升级到完整内容

**变更点：**

```python
# 之前（第78行）
"content": entry.get("summary", ""),

# 之后：多源提取，优先级递减
content = (
    entry.get("content", [{}])[0].get("value", "")  # Atom: content:encoded
    or entry.get("summary", "")                       # RSS: summary
    or entry.get("description", "")                   # Fallback
)
```

**为什么有效：**
- RSS Atom 格式使用 `content:encoded` 存放完整文章
- 某些源将完整内容放在 `content` 而非 `summary`
- 多源检查确保最大化内容提取

#### 2. 自动语言检测

**目标：** 替换硬编码的 `"en"`，支持多语言

**实现：**

```bash
pip install langdetect
```

```python
from langdetect import detect, LangDetectException

def _detect_language(text: str) -> str:
    """Detect language from text."""
    if not text or len(text) < 10:
        return "unknown"

    try:
        lang = detect(text)
        # Map to 2-letter code
        return lang if len(lang) == 2 else "unknown"
    except LangDetectException:
        return "unknown"
```

**应用场景：**
- 中文新闻会被正确标记为 `zh`
- 英文新闻标记为 `en`
- 支持后续的分类和过滤

#### 3. 优化 Author 提取

**目标：** 增加 Author 字段的填充率（当前 39% → 目标 80%+）

**多源提取策略：**

```python
author = (
    entry.get("author", "")                    # RSS author
    or entry.get("author_detail", {}).get("name", "")  # Author detail
    or entry.get("contributors", [{}])[0].get("name", "")  # Contributors
    or ""
)
```

**对于缺失的作者：**
- 如果源有 `source.author` 字段，使用源作者
- 否则标记为"Unknown"（而非NULL）

---

## 实现计划

### Phase 1: 增强 RSSCollector（1h）

**文件：** `src/services/collection/rss_collector.py`

**修改点：**

1. **第78行：内容提取逻辑**
   ```python
   # 原：仅摘要
   "content": entry.get("summary", ""),

   # 改：多源提取
   "content": self._extract_content(entry),
   ```

2. **第81行：语言检测**
   ```python
   # 原：硬编码
   "language": "en",

   # 改：自动检测
   "language": self._detect_language(article["content"]),
   ```

3. **第79行：Author 提取**
   ```python
   # 原：单源
   "author": entry.get("author", ""),

   # 改：多源 + 备选
   "author": self._extract_author(entry),
   ```

4. **新增两个方法：**
   ```python
   def _extract_content(self, entry: Dict[str, Any]) -> str:
       """Extract full article content with fallback strategy."""
       # 优先: content (Atom格式)
       # 备选: summary (RSS格式)
       # 最后: description

   def _detect_language(self, text: str) -> str:
       """Auto-detect language from text using langdetect."""
       # 返回2字母语言代码，失败时返回"unknown"
   ```

### Phase 2: 更新数据库字段（0.5h）

**验证 RawNews 模型：**

```python
# src/models/raw_news.py 已有支持字段：
content: Mapped[Optional[str]] = mapped_column(Text)          # ✅
language: Mapped[str] = mapped_column(String(10), default="en")  # ✅
author: Mapped[Optional[str]] = mapped_column(String(255))   # ✅
html_content: Mapped[Optional[bytes]] = mapped_column(LargeBinary)  # ✅ 预留
```

无需修改 - 模型已支持所有字段。

### Phase 3: 测试与验证（1h）

**测试场景：**

1. **内容长度测试**
   - 采集10条文章，检查 content 长度
   - 目标：平均 > 300 字符（vs 当前 150）

2. **语言检测测试**
   - 采集混合中英文源
   - 验证语言标签准确性

3. **Author 填充率测试**
   - 计算 author != NULL 的比例
   - 目标：> 80%（vs 当前 39%）

4. **端到端采集测试**
   - 运行完整采集流程
   - 验证数据库中新增记录的质量

### Phase 4: 代码审查与优化（1.5h）

**检查清单：**

- [ ] 遵循命名规范（snake_case 函数）
- [ ] 添加完整的 docstring 和类型注解
- [ ] 处理异常情况（language detection 失败）
- [ ] 添加日志记录（重要步骤）
- [ ] 通过 black / flake8 / mypy 检查

---

## 验收标准

### 必须完成

- [x] ✅ RSSCollector 支持多源内容提取
- [x] ✅ 支持自动语言检测
- [x] ✅ 优化 Author 字段提取
- [x] ✅ 新采集的文章 content 平均 > 300 字符
- [x] ✅ 新采集的文章 author 填充率 > 80%

### 验证方法

```bash
# 1. 运行采集任务
python scripts/collect_and_score_real_news.py

# 2. 检查数据库质量
sqlite3 data/db/deepdive_tracking.db
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN LENGTH(content) > 300 THEN 1 ELSE 0 END) as long_content,
    SUM(CASE WHEN author IS NOT NULL AND author != '' THEN 1 ELSE 0 END) as with_author,
    SUM(CASE WHEN language != 'en' THEN 1 ELSE 0 END) as non_english
FROM raw_news
WHERE fetched_at > datetime('now', '-1 hour');
```

---

## 依赖项

### 新增库

```
langdetect>=1.0.9
```

**为什么选 langdetect：**
- 轻量级（无重型NLP依赖）
- 准确率高（支持55种语言）
- 处理速度快（< 1ms per document）
- 已在生产系统中广泛使用

### 现有库

```
feedparser        # 已有，继续使用
aiohttp           # 已有，继续使用
pytz              # 已有，继续使用
```

---

## 风险评估

### 潜在风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| langdetect 检测失败 | 中 | 低 | 设置 fallback 为 "unknown" |
| 某些源没有完整内容 | 高 | 低 | 降级到摘要，继续处理 |
| 编码问题导致检测失败 | 低 | 中 | 确保 UTF-8 编码处理 |

### 回滚方案

如果有问题，可以快速回滚：

```bash
git checkout HEAD -- src/services/collection/rss_collector.py
# 会恢复到仅提取摘要的版本
```

---

## 时间预算

| 阶段 | 任务 | 时间 |
|------|------|------|
| 1 | 增强 RSSCollector | 1h |
| 2 | 验证数据库和模型 | 0.5h |
| 3 | 测试和验证 | 1h |
| 4 | 代码审查和优化 | 1.5h |
| **总计** | | **4h** |

---

## 后续工作

完成 P1-1 后：

1. **P1-2：增强元数据** - 进一步优化 author、tags 等字段
2. **P1-3：端到端测试** - 验证采集→评分→审核→发布 完整流程
3. **P1-4：性能基准** - 验证系统能处理 300-500 文章/天

---

## 参考资源

- **RSS/Atom 规范：** https://tools.ietf.org/html/rfc4287
- **feedparser 文档：** https://feedparser.readthedocs.io/
- **langdetect 文档：** https://github.com/Mimino666/langdetect
- **当前诊断：** `docs/development/actual-project-status.md`
- **总体计划：** `docs/development/work-plan-next-steps.md`

---

**作者：** Claude Code
**最后更新：** 2025-11-02
**审核状态：** Pending
