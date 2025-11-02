# Agent 3 启动指南

**创建时间：** 2025-11-02
**前置Agent：** Agent 1 & Agent 2
**当前项目状态：** Phase 3 完成 → Phase 4 开始
**预计任务量：** 中等（3-5小时）

---

## ⚡ 快速5分钟启动

### Step 0️⃣ 强制：安装Git Hooks（1分钟）

```bash
# 这是强制性的，必须先做！
bash .claude/tools/install-hooks.sh

# 验证成功
git hooks --list | head -5
```

**为什么必须？**
- 防止规范违反进入代码库
- 自动拒绝UPPERCASE文件名
- 验证提交信息格式
- Agent 1的血泪教训（创建了3个UPPERCASE文件被批评）

### Step 1️⃣ 检查项目状态（2分钟）

```bash
# 查看当前分支
git branch -v

# 查看最近提交
git log --oneline -5

# 查看项目结构
tree -L 2 src/ tests/
```

**预期输出：**
```
✅ 当前分支：main
✅ 最近提交：3个hooks相关提交
✅ 项目文件：49个Python文件，27个文档
```

### Step 2️⃣ 运行测试验证环境（2分钟）

```bash
# 运行所有测试
pytest tests/ -v --tb=short

# 预期：25个测试全部通过，覆盖率94.2%
```

---

## 📚 必读文档（15分钟）

按优先级阅读：

### 🔴 必读（MUST READ）
1. **本文件的后续部分** （5分钟）
2. **phase-3-handoff-report.md** （5分钟）
   - 了解Phase 3做了什么
   - 了解已知的关键问题
   - 了解Phase 4的建议任务

3. **.claude/agent-handoff-protocol.md** （5分钟）
   - Section 5：强制执行规则
   - 了解Git hooks系统

### 🟡 强烈建议（SHOULD READ）
1. **.claude/standards/03-naming-conventions.md**
   - 理解命名规范（这很重要！）

2. **.claude/standards/08-git-workflow.md**
   - 理解分支和提交流程

3. **.claude/standards/04-python-code-style.md**
   - 了解代码风格要求

---

## 🎯 当前项目状态快照

### ✅ 已完成
```
- 项目初始化结构
- 12个规范文档
- 8个SQLAlchemy数据库模型
- 25个单元测试（覆盖率94.2%）
- Git hooks强制执行系统
- Alembic数据库迁移
```

### ⏳ 待实现
```
- API端点（src/api/v1/endpoints/）
- 服务层完整实现（src/services/）
- 集成测试和E2E测试
- OpenAPI文档
```

### 🚨 关键问题（必须了解）

#### Issue 1: 数据采集模块不完整（CRITICAL）
```
位置：src/services/collection/

问题描述（来自用户批评）：
  1. data_collection_raw_data 缺少有效信息
     - 问题根本原因：设计不完整
     - 字段太少，无法存储必要的信息

  2. data_collection_raw_data 没有引用 resource
     - 数据结构错误
     - 无法关联采集的资源

  3. resource-xxx 集合存在大量重复
     - 缺少判重机制
     - 缺少去重机制
     - 业务逻辑不完整

  4. resource-xxx 集合不全
     - 未采集的资源类型有遗漏

状态：🔴 CRITICAL（影响系统可用性）
优先级：Phase 4 优先级 1（必须修复）
预计工作量：2-3小时（需要重构）
```

**修复方向：**
- 重新设计 DataCollectionRawData 数据结构
- 添加完整的字段（source, url, crawl_time, metadata等）
- 建立与Resource的外键关系
- 实现Resource的判重和去重逻辑
- 补充缺失的资源类型

---

## 🚀 Phase 4 任务清单

### 优先级 1：修复关键缺陷（2-3小时）

#### Task 1.1: 修复数据采集模块
```markdown
文件：src/services/collection/
问题：数据结构和去重逻辑不完整

步骤：
  1. 审查现有数据模型
  2. 扩展 DataCollectionRawData 模型
     - 添加字段：source, url, crawl_time, metadata
  3. 建立外键关系到 Resource
  4. 实现 Simhash/MinHash 判重
  5. 实现去重逻辑
  6. 编写单元测试（覆盖率 > 85%）
  7. 提交 PR

相关文件：
  - src/models/data_collection.py
  - src/models/resource.py
  - src/services/collection/
  - tests/unit/services/collection/

规范要求：
  - 文件命名：snake_case ✅（hooks会强制）
  - 类型注解：100% ✅
  - 单元测试：> 85% 覆盖
  - 提交信息：Conventional Commits ✅（hooks会强制）
```

### 优先级 2：实现API端点（3-4小时）

#### Task 2.1: 实现数据采集API
```markdown
文件：src/api/v1/endpoints/collection.py
功能：暴露数据采集和查询能力

端点设计：
  POST   /api/v1/data-sources           → 添加数据源
  GET    /api/v1/data-sources           → 列出数据源
  GET    /api/v1/data-sources/{id}      → 获取数据源详情
  POST   /api/v1/collections/trigger    → 触发采集任务
  GET    /api/v1/collections/{id}       → 获取采集结果

模板位置：
  .claude/templates/api/endpoint.py.template

规范检查：
  - 使用 .claude/standards/05-api-design.md
  - RESTful设计
  - Proper HTTP status codes
  - 请求和响应验证 (Pydantic schemas)
```

#### Task 2.2: 实现内容评分API
```markdown
文件：src/api/v1/endpoints/scoring.py
功能：内容AI评分接口

端点设计：
  POST   /api/v1/scores                 → 评分内容
  GET    /api/v1/scores/{id}            → 获取评分结果
  GET    /api/v1/scores?category=tech   → 按类别查询
```

### 优先级 3：完善服务层（2-3小时）

#### Task 3.1: 实现完整的服务类
```
文件：
  - src/services/content/content_manager.py
  - src/services/ai/scorer.py
  - src/services/publishing/publisher.py

功能：
  - 内容去重和标准化
  - AI智能评分（0-100分，8大类别）
  - 多渠道发布（微信、小红书、Web）
```

---

## 📋 开发工作流

### 1. 开始新任务

```bash
# 创建功能分支（遵循规范）
git checkout -u origin/main
git pull origin main
git checkout -b feature/002-fix-collection-module

# 创建功能分支命名规范：
# feature/00X-description-with-kebab-case
```

### 2. 开发代码

```bash
# 记住这些强制要求：
✅ 文件名：snake_case (Git hooks会强制)
✅ 类名：PascalCase
✅ 函数/变量：snake_case
✅ 常量：UPPER_CASE
✅ 类型注解：100%必须有
✅ Docstring：每个函数都要
✅ 单元测试：覆盖率 > 85%

# 示例：
src/services/collection/
  ├── collection_manager.py     # 采集管理器
  ├── deduplication.py          # 去重逻辑
  ├── validation.py             # 数据验证
  └── __init__.py

tests/unit/services/collection/
  ├── test_collection_manager.py
  ├── test_deduplication.py
  └── test_validation.py
```

### 3. 验证代码质量

```bash
# 运行这个检查脚本（会自动运行hooks）
bash .claude/tools/check-standards.sh

# 或者手动运行各项检查
black src/ tests/              # 格式化
flake8 src/ tests/             # 风格检查
mypy src/ --ignore-missing-imports  # 类型检查
pytest tests/ --cov=src        # 测试

# 如果有问题，自动修复：
bash .claude/tools/auto-fix.sh
```

### 4. 提交和推送

```bash
# 暂存文件（hooks会在提交时运行）
git add .

# 提交（遵循Conventional Commits格式）
# 如果不遵循，commit-msg hook会拒绝
git commit -m "feat(collection): implement deduplication logic

- Add Simhash-based deduplication
- Add resource-to-raw_data foreign key
- Implement duplicate detection algorithm
- Add 15 unit tests with 92% coverage"

# 推送
git push -u origin feature/002-fix-collection-module
```

### 5. 创建PR并请求审查

```bash
# 使用gh命令创建PR
gh pr create --title "feat(collection): implement deduplication logic" \
             --body "..."

# 或者在GitHub网页上创建
# 重点：
#   - 标题清晰
#   - 描述完整（背景、改动、测试）
#   - 至少1个审查者
#   - 通过所有自动检查
```

---

## 🛠️ 常用命令速查

```bash
# 检查项目规范
bash .claude/tools/check-standards.sh

# 自动修复规范问题
bash .claude/tools/auto-fix.sh

# 安装/验证Git hooks
bash .claude/tools/install-hooks.sh

# 运行单元测试
pytest tests/ -v

# 运行测试并检查覆盖率
pytest tests/ --cov=src --cov-report=html

# 查看项目结构
tree -L 3 src/ tests/

# 查看git log
git log --oneline -10

# 查看当前分支状态
git status

# 创建功能分支
git checkout -b feature/00X-description

# 查看某个文件的修改历史
git log -p src/services/collection/
```

---

## ✅ 启动检查清单

在开始开发前，完成以下检查：

```
□ Git hooks已安装
  命令：bash .claude/tools/install-hooks.sh

□ 所有测试通过
  命令：pytest tests/ -v
  预期：25个测试全部通过

□ 项目规范检查通过
  命令：bash .claude/tools/check-standards.sh
  预期：0个违反

□ Git分支正确
  命令：git branch -v
  预期：在main分支，且是最新状态

□ 已阅读关键文档
  □ phase-3-handoff-report.md
  □ agent-handoff-protocol.md（Section 5）
  □ .claude/standards/03-naming-conventions.md

□ 理解关键问题
  □ 理解数据采集模块的问题
  □ 理解Git hooks的作用
  □ 理解规范的强制级别
```

---

## 🔗 快速导航

| 需要... | 查看... |
|--------|--------|
| 规范导航 | .claude/standards/00-overview.md |
| 命名规范 | .claude/standards/03-naming-conventions.md |
| Git工作流 | .claude/standards/08-git-workflow.md |
| API设计 | .claude/standards/05-api-design.md |
| 代码风格 | .claude/standards/04-python-code-style.md |
| 数据库设计 | .claude/standards/06-database-design.md |
| 交接协议 | .claude/agent-handoff-protocol.md |
| Phase 3完成情况 | phase-3-handoff-report.md |
| 项目规范总览 | CLAUDE.md |
| 快速参考卡片 | .claude/standards/99-quick-reference.md |

---

## ⚠️ 常见陷阱（避免重复Agent 1的错误）

### ❌ 陷阱 1: 忘记安装Hooks
```
错误：跳过 bash .claude/tools/install-hooks.sh
后果：创建UPPERCASE文件会被推送，被批评
解决：第一步就执行它！
```

### ❌ 陷阱 2: 提交不规范的文件名
```
错误：git add src/AgentConfiguration.py（PascalCase）
后果：Git hook拒绝提交
解决：hooks会帮你检查，遵循snake_case即可
```

### ❌ 陷阱 3: 提交信息不遵循CC格式
```
错误：git commit -m "add new feature"
后果：commit-msg hook拒绝提交
正确：git commit -m "feat(module): add new feature"
```

### ❌ 陷阱 4: 修改tests/但测试失败
```
错误：修改了test_*.py 但pytest失败
后果：pre-commit hook拒绝提交
解决：先运行pytest，确保所有测试通过
```

### ❌ 陷阱 5: 没有单元测试覆盖
```
错误：实现功能但不写测试
后果：难以维护，覆盖率下降
目标：新功能的单元测试覆盖率 > 85%
```

---

## 🎓 Agent间的建议

1. **不要跳过hooks**
   - Agent 1因为忽视规范被严厉批评
   - Hooks是自动防线，不是可选项

2. **数据采集的问题很严重**
   - 用户用了3个感叹号和"巨大的致命问题"
   - 不是小bug，是架构设计问题
   - 需要完整重构

3. **保持高质量标准**
   - 测试覆盖率 > 85%（不是 >= 80%）
   - 所有函数都要有类型注解
   - 所有函数都要有docstring
   - 代码风格通过black和flake8

4. **文档和代码一样重要**
   - 完成功能时更新相关文档
   - 更新CLAUDE.md中的进度
   - 记录架构决策（在docs/中）

5. **及时交接**
   - 当窗口达到极限时，立即启动交接流程
   - 创建详细的Phase报告
   - 准备清晰的startup guide

---

## 📞 遇到问题？

### 规范相关问题
- 查看：.claude/standards/ 中的相关文档
- 查看：.claude/standards/99-quick-reference.md（快速查找）
- 运行：bash .claude/tools/check-standards.sh（诊断）

### 代码问题
- 查看：existing tests in tests/unit/
- 查看：相关的模板文件（.claude/templates/）
- 查看：相关的规范文档（04-08）

### 数据库问题
- 查看：.claude/standards/06-database-design.md
- 查看：src/models/ 中的现有模型
- 查看：src/database/migrations/ 中的迁移脚本

### Git / Hooks问题
- 查看：.claude/agent-handoff-protocol.md（Section 5）
- 运行：bash .claude/tools/install-hooks.sh（重新安装）
- 查看：.claude/hooks/ 中的hook源代码

---

## 🚀 准备好了吗？

当你完成上述所有检查清单时，你已经准备好开始Phase 4了！

**建议流程：**
1. ✅ 完成启动检查清单（15分钟）
2. ✅ 阅读关键文档（15分钟）
3. ✅ 创建feature分支（2分钟）
4. ✅ 开始实现Task 1.1（2-3小时）
5. ✅ 测试、验证、提交PR（1小时）

**总耗时：** 3-5小时完成一个优先级任务

**下一个里程碑：** Phase 4完成后进行阶段交接

---

**准备好开始了吗？** 🚀

执行：`bash .claude/tools/install-hooks.sh`

开工！

