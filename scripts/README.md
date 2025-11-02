# Scripts - 脚本使用指南

**目录结构已重组** - 现在所有脚本都分类清晰

---

## 📁 目录结构

```
scripts/
├── 00-setup/          ← 初始化（仅需运行一次）
├── 01-collection/     ← 采集新闻数据
├── 02-evaluation/     ← AI 评分
├── 03-verification/   ← 结果查看和演示
├── quickstart/        ← 快速启动工具
└── README.md          ← 本文件
```

---

## 🚀 快速开始

### 第一次使用：初始化系统 (5分钟)

```bash
cd scripts/00-setup
python 1_init_data_sources.py      # 添加 15 个数据源
python 2_configure_authors.py      # 配置默认 author
```

### P1-3 端到端测试 (10分钟)

```bash
# Step 1: 采集新闻 (2分钟)
cd scripts/01-collection
python collect_news.py

# Step 2: 评分新闻 (5分钟)
cd scripts/02-evaluation
python score_batch.py

# Step 3: 查看结果 (1分钟)
cd scripts/03-verification
python view_summary.py
```

### 一键启动

```bash
cd scripts/quickstart
bash run_all.sh
```

---

## 📚 各目录说明

### 📁 **00-setup** (初始化)

**何时运行：** 首次使用

**包含的脚本：**

| 脚本 | 功能 | 耗时 |
|------|------|------|
| `1_init_data_sources.py` | 添加 15 个数据源 | 1s |
| `2_configure_authors.py` | 配置源的默认 author | 1s |

**典型输出：**
```
✓ 源未找到: 源名
✓ 源名: → 默认 author
已更新 3 个数据源
```

---

### 📁 **01-collection** (采集)

**何时运行：** 需要采集新闻

**包含的脚本：**

| 脚本 | 功能 | 耗时 |
|------|------|------|
| `collect_news.py` | 采集新闻 + 显示 TOP 10 | 30-60s |
| `diagnose_sources.py` | 诊断数据源问题 | 30-60s |

**示例：**

```bash
# 采集新闻
python collect_news.py
# 输出：采集统计、TOP 10 新闻、SQL 查询示例

# 诊断问题源
python diagnose_sources.py
# 输出：每个源的连接状态、HTTP 状态码
```

---

### 📁 **02-evaluation** (评分)

**何时运行：** 采集后，需要评分新闻

**包含的脚本：**

| 脚本 | 功能 | 耗时 |
|------|------|------|
| `score_batch.py` | 批量评分所有未评分文章 | 3-5min |
| `score_missing.py` | 补评分失败的文章 | 取决于数量 |
| `test_api.py` | 测试 OpenAI API 连接 | 5-10s |

**示例：**

```bash
# 批量评分 (推荐用于 P1-3)
python score_batch.py
# 输出：成功数、失败数、成本、性能统计

# 重新评分失败的文章
python score_missing.py
# 输出：补评分的数量和结果

# 测试 API
python test_api.py
# 输出：API 连接状态、响应格式验证
```

---

### 📁 **03-verification** (验证)

**何时运行：** 评分后，查看最终结果

**包含的脚本：**

| 脚本 | 功能 | 耗时 |
|------|------|------|
| `view_summary.py` | 查看数据库摘要 + TOP 10 | 1-2s |
| `demo_mock.py` | 模拟演示（无需 API Key） | 5-10s |

**示例：**

```bash
# 查看数据库摘要
python view_summary.py
# 输出：raw_news 统计、processed_news 统计、TOP 10、SQL 命令

# 离线演示
python demo_mock.py
# 输出：完整的采集 → 评分 → 结果流程（模拟数据）
```

---

### 📁 **quickstart** (快速启动)

**一键运行完整测试：**

```bash
bash run_all.sh
```

**包含的脚本：**

| 脚本 | 功能 |
|------|------|
| `run_all.sh` | 一键运行采集 → 评分 → 查看 |
| `README_quickstart.md` | 快速启动说明 |

---

## 🎯 常见使用场景

### 场景 1: 第一次使用
```bash
cd scripts/00-setup
python 1_init_data_sources.py
python 2_configure_authors.py
```

### 场景 2: P1-3 完整测试 (推荐)
```bash
cd scripts/quickstart
bash run_all.sh
```

### 场景 3: 只采集，不评分
```bash
cd scripts/01-collection
python collect_news.py
```

### 场景 4: 只评分
```bash
cd scripts/02-evaluation
python score_batch.py
```

### 场景 5: 只查看结果
```bash
cd scripts/03-verification
python view_summary.py
```

### 场景 6: 诊断问题
```bash
cd scripts/01-collection
python diagnose_sources.py  # 找出无效的源

# 或者
cd scripts/02-evaluation
python test_api.py  # 测试 API 连接
```

---

## 📊 脚本选择矩阵

| 需求 | 脚本 | 目录 | 耗时 |
|------|------|------|------|
| 第一次初始化 | `1_init_data_sources.py` | 00-setup | 1s |
| 采集新闻 | `collect_news.py` | 01-collection | 1min |
| 评分新闻 | `score_batch.py` | 02-evaluation | 5min |
| 查看结果 | `view_summary.py` | 03-verification | 1s |
| 一键测试 | `run_all.sh` | quickstart | 10min |
| 诊断采集问题 | `diagnose_sources.py` | 01-collection | 1min |
| 测试 API | `test_api.py` | 02-evaluation | 10s |
| 离线演示 | `demo_mock.py` | 03-verification | 10s |

---

## ✅ P1-3 测试清单

- [ ] 运行 `00-setup/1_init_data_sources.py` (首次)
- [ ] 运行 `00-setup/2_configure_authors.py` (首次)
- [ ] 运行 `01-collection/collect_news.py` (采集)
- [ ] 检查 TOP 10 输出
- [ ] 运行 `02-evaluation/score_batch.py` (评分)
- [ ] 检查成功率 > 95%
- [ ] 运行 `03-verification/view_summary.py` (查看)
- [ ] 验证数据完整性

---

## 🔧 故障排查

### 问题：脚本找不到
```bash
# 确保当前在正确的目录
cd scripts/01-collection
python collect_news.py

# 或者用完整路径
python scripts/01-collection/collect_news.py
```

### 问题：数据库错误
```bash
# 清空重新初始化
rm data/db/deepdive_tracking.db
python scripts/01-collection/collect_news.py  # 会自动创建
```

### 问题：API 错误
```bash
# 测试 API 连接
python scripts/02-evaluation/test_api.py
```

---

## 📝 脚本详细文档

每个子目录都有详细的 README：

- `01-collection/README_collection.md` - 采集脚本详解
- `02-evaluation/README_evaluation.md` - 评分脚本详解
- `03-verification/README_verification.md` - 验证脚本详解
- `quickstart/README_quickstart.md` - 快速启动详解

---

## 🎓 推荐学习路径

### 新手 (5分钟)
1. 阅读本文件
2. 运行 `quickstart/run_all.sh`
3. 查看输出结果

### 进阶 (20分钟)
1. 读各子目录的 README
2. 分别运行各个脚本
3. 理解每个脚本的功能

### 深入 (1小时)
1. 阅读脚本源代码
2. 修改参数测试
3. 创建自己的脚本

---

## 📞 快速参考

```bash
# 初始化
python scripts/00-setup/1_init_data_sources.py
python scripts/00-setup/2_configure_authors.py

# 采集
python scripts/01-collection/collect_news.py

# 评分
python scripts/02-evaluation/score_batch.py

# 查看
python scripts/03-verification/view_summary.py

# 一键运行
bash scripts/quickstart/run_all.sh

# 诊断
python scripts/01-collection/diagnose_sources.py
python scripts/02-evaluation/test_api.py

# 演示
python scripts/03-verification/demo_mock.py
```

---

## ✨ 目录重组优势

✓ **清晰分类** - 每个目录对应一个功能模块
✓ **易于查找** - 知道脚本位置和用途
✓ **执行顺序** - 数字前缀确保逻辑顺序
✓ **相关聚集** - 相关脚本在同一目录
✓ **文档完整** - 每个目录有 README
✓ **快速启动** - quickstart 目录方便测试

---

**最后更新：** 2025-11-02
**脚本状态：** ✅ 已重组和分类
**推荐开始：** `bash scripts/quickstart/run_all.sh`
