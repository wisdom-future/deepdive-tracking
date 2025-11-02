# 下一个Agent快速启动指南

**准备时间:** 约5分钟
**所需工作:** 立即可继续Phase 3

---

## ⚡ 5分钟快速启动

### 1️⃣ 阅读关键信息（2分钟）
```bash
cd /d/projects/deepdive-tracking

# 重要：当前项目状态
cat CLAUDE.md

# 重要：Phase 2 完成报告
cat .claude/handoff/PHASE-2-COMPLETION-REPORT.md

# 重要：Agent交接协议
cat .claude/AGENT-HANDOFF-PROTOCOL.md
```

### 2️⃣ 验证环境（2分钟）
```bash
# 确保在正确分支
git branch
# Expected: * feature/001-project-initialization

# 同步最新代码
git pull origin feature/001-project-initialization

# 运行测试确保环境正常
pytest tests/unit/models/test_models.py -v
# Expected: 25 passed in ~2 seconds

# 检查代码风格
black --check src/models/
flake8 src/models/
mypy src/models/
```

### 3️⃣ 理解代码结构（1分钟）
```bash
# 查看已完成的模型
ls -la src/models/
# 输出应该包括：
# - base.py, data_source.py, raw_news.py
# - processed_news.py, content_review.py, published_content.py
# - content_stats.py, publishing_schedule.py, cost_log.py
# - operation_log.py, publishing_schedule_content.py, __init__.py

# 查看迁移脚本
ls -la alembic/versions/
# 输出应该包括：
# - 001_initial_create_all_tables.py

# 查看测试
ls -la tests/unit/models/
# 输出应该包括：
# - conftest.py, test_models.py
```

---

## 📋 当前状态

### ✅ 已完成（Phase 2）
- 所有10个数据库模型 (100%)
- 所有21个数据库索引
- 初始迁移脚本
- 25个单元测试（94.2%覆盖率）
- 所有代码遵循规范

### 📍 当前分支
```
feature/001-project-initialization (from Phase 1 commit)
└─ Latest: ab338d3 feat(database): complete SQLAlchemy models and initial migration
```

### 🎯 下一步工作（Phase 3）
这是**下一个Agent**应该做的：

1. **代码审查和合并** (30分钟)
   ```bash
   # 1. 审查当前分支的所有更改
   git log feature/001-project-initialization --oneline | head -5

   # 2. 对比主分支
   git diff main..feature/001-project-initialization --stat

   # 3. 切换到主分支
   git checkout main

   # 4. 合并特性分支
   git merge feature/001-project-initialization

   # 5. 推送到远程
   git push origin main
   ```

2. **Phase 3：实现数据访问层** (下一个任务)
   - [ ] 创建Repository类（数据访问抽象）
   - [ ] 实现基础CRUD操作
   - [ ] 添加复杂查询（join, filter, aggregate）
   - [ ] 编写Repository单元测试

3. **Phase 4：API端点实现**
   - [ ] RESTful API设计（基于05-api-design规范）
   - [ ] Pydantic schema定义
   - [ ] FastAPI路由实现
   - [ ] API文档和测试

---

## 🔍 关键代码位置

### 数据库模型
```
src/models/
├── base.py                           # BaseModel基类
├── data_source.py                    # 信息源配置 (100 lines)
├── raw_news.py                       # 原始新闻 (43 lines)
├── processed_news.py                 # 处理结果 (79 lines)
├── content_review.py                 # 审核流程 (75 lines)
├── published_content.py              # 已发布内容 (77 lines)
├── content_stats.py                  # 统计数据 (64 lines)
├── publishing_schedule.py            # 定时发布 (74 lines)
├── cost_log.py                       # 成本追踪 (50 lines)
├── operation_log.py                  # 操作审计 (34 lines)
├── publishing_schedule_content.py    # 关联表 (12 lines)
└── __init__.py                       # 导出所有模型

Total: ~850 lines, 100% coverage
```

### 迁移脚本
```
alembic/
├── versions/
│   └── 001_initial_create_all_tables.py  # 384 lines
│       ├── upgrade(): 创建9个表、21个索引
│       └── downgrade(): 回滚所有更改
├── env.py (updated)
└── alembic.ini (updated)
```

### 测试
```
tests/unit/models/
├── conftest.py (146 lines)
│   └── Fixtures: test_engine, test_session, 6个sample_xxx
├── test_models.py (481 lines)
│   ├── TestDataSource: 3个测试
│   ├── TestRawNews: 3个测试
│   ├── TestProcessedNews: 3个测试
│   ├── TestContentReview: 2个测试
│   ├── TestPublishedContent: 2个测试
│   ├── TestContentStats: 2个测试
│   ├── TestPublishingSchedule: 2个测试
│   ├── TestCostLog: 2个测试
│   ├── TestOperationLog: 1个测试
│   ├── TestModelRelationships: 3个测试
│   └── TestModelTimestamps: 2个测试
└── Total: 25 tests, 94.2% coverage
```

---

## 🔑 关键信息

### 数据库设计
- **主数据库:** PostgreSQL 15 (在.env中配置)
- **开发测试:** SQLite内存数据库
- **表数量:** 9个主表
- **关键关系:** 1对1或1对N，所有都是CASCADE delete

### 模型特点
1. **所有模型继承 BaseModel**
   - 自动 id, created_at, updated_at
   - 自动时间戳管理

2. **富数据类型**
   - JSON/JSONB字段用于灵活存储
   - 数组类型用于标签和列表

3. **完整约束**
   - 枚举约束（CHECK）
   - 范围约束（CHECK）
   - 外键约束（CASCADE）
   - 唯一约束

### 测试框架
- **引擎:** pytest
- **数据库:** SQLite :memory:
- **Fixture:** Hierarchical (test_engine → test_session → sample_data)
- **覆盖率:** 94.2% (工具: coverage.py)

---

## 🚀 立即执行的命令

### 1. 验证代码
```bash
cd /d/projects/deepdive-tracking

# 运行所有模型测试
pytest tests/unit/models/ -v --cov=src/models --cov-report=html

# 预期输出:
# ========================= 25 passed in 2.07s =========================
# Coverage: 94.2%
```

### 2. 代码质量检查
```bash
# 格式化检查
black --check src/models/ tests/unit/models/

# 风格检查
flake8 src/models/ tests/unit/models/

# 类型检查
mypy src/models/

# 预期: 全部通过
```

### 3. Git操作
```bash
# 查看提交历史
git log feature/001-project-initialization -3 --oneline

# 查看改变统计
git diff main...feature/001-project-initialization --stat

# 合并到主分支（在所有检查通过后）
git checkout main
git merge feature/001-project-initialization --ff-only
git push origin main
```

---

## 📚 重要文档

### 必读（按优先级）
1. **CLAUDE.md** (项目总体规范)
2. **PHASE-2-COMPLETION-REPORT.md** (当前完成状态)
3. **.claude/standards/06-database-design.md** (数据库规范)
4. **.claude/standards/07-testing-standards.md** (测试规范)

### 参考
- **.claude/standards/04-python-code-style.md** (代码风格)
- **.claude/standards/08-git-workflow.md** (Git工作流)
- **docs/tech/database-schema.md** (完整数据库设计)

---

## ⚙️ 环境配置

### 必需的依赖
```bash
# 在虚拟环境中确认已安装
pip list | grep -E "sqlalchemy|alembic|pytest"

# 应该看到:
# alembic==1.13.1
# pytest==8.4.2
# sqlalchemy==2.0.23
# ...
```

### 环境变量（.env）
```bash
# 确保已复制 .env.example
cp .env.example .env

# 关键变量:
DATABASE_URL=postgresql://deepdive:deepdive_password@localhost:5432/deepdive_db
DEBUG=True
```

### PostgreSQL 连接（当需要时）
```bash
# 创建数据库
createdb -U postgres deepdive_db

# 运行迁移
alembic upgrade head

# 查看表结构
psql -U deepdive -d deepdive_db -c "\dt"
```

---

## 🐛 常见问题

### Q1: 运行测试时出现"No module named src"
```bash
# 解决: 确保你在项目根目录
cd /d/projects/deepdive-tracking
pwd  # 应该显示 .../deepdive-tracking

# 检查PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/unit/models/
```

### Q2: PostgreSQL连接失败
```bash
# 这在开发中是正常的，测试使用SQLite
# 如果需要实际连接PostgreSQL:
# 1. 确保PostgreSQL运行中
# 2. 检查 DATABASE_URL 配置
# 3. 运行: psql -U postgres (测试连接)
```

### Q3: 模型关系有警告
```
SAWarning: relationship 'X' will copy column...
```
**解决:** 这是预期的，已在模型中用 `overlaps` 处理

### Q4: 迁移脚本需要更新
```bash
# 目前迁移脚本是手工创建的
# 如果添加新模型，需要:
# 1. 创建模型文件
# 2. 更新 models/__init__.py
# 3. 手动更新迁移脚本或重新生成
```

---

## ✅ 启动检查清单

完成以下所有检查后，可以开始Phase 3工作：

- [ ] Git分支正确（feature/001-project-initialization）
- [ ] `git pull` 已执行
- [ ] `pytest tests/unit/models/ -v` 全部通过
- [ ] `black --check` 无错误
- [ ] `flake8` 无错误
- [ ] `mypy` 无错误
- [ ] 已阅读PHASE-2-COMPLETION-REPORT.md
- [ ] 已阅读AGENT-HANDOFF-PROTOCOL.md
- [ ] 理解当前代码结构

---

## 📞 调试技巧

### 查看模型结构
```python
from src.models import DataSource
print(DataSource.__table__)
print(DataSource.__table__.columns)
```

### 查看SQL生成
```python
from src.models import RawNews
from sqlalchemy.dialects import postgresql
print(
    RawNews.__table__.select().compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True}
    )
)
```

### 调试测试
```bash
# 显示更详细的输出
pytest tests/unit/models/test_models.py -vv -s

# 在测试中添加print和断点
pytest tests/unit/models/test_models.py -vv --pdb
```

---

## 🎯 Phase 3 快速规划

### 当你准备好开始Phase 3时：

1. **创建新分支**
   ```bash
   git checkout main
   git pull
   git checkout -b feature/002-data-access-layer
   ```

2. **创建Repository类**
   ```
   src/services/repositories/
   ├── __init__.py
   ├── base_repository.py (CRUD template)
   ├── data_source_repository.py
   ├── raw_news_repository.py
   ├── processed_news_repository.py
   └── ...
   ```

3. **编写测试**
   ```
   tests/unit/services/
   └── test_repositories.py
   ```

4. **实现和提交**
   - 每个Repository一个commit
   - 提交信息: `feat(repo): implement XXXRepository`
   - 确保测试覆盖率 > 85%

---

## 📝 查看完整的Phase 2报告

详见: `.claude/handoff/PHASE-2-COMPLETION-REPORT.md`

包含：
- 完整的任务列表和完成状态
- 代码统计和质量指标
- 所有关键决策和设计说明
- 已知限制和改进方向
- 支持信息和常见问题

---

**准备好开始了吗？**

如果你完成了上面的所有步骤，就可以开始Phase 3的工作了！
祝你编码愉快！🚀

