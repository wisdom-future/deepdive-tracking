# DeepDive Tracking - 项目规范与指南

**版本：** 1.0
**最后更新：** 2025-11-02
**适用：** 整个项目生命周期（MVP到production）
**强制级别：** 严格型（所有规范为MUST-HAVE）

---

## 🎯 项目概述

**项目名称：** DeepDive Tracking
**描述：** AI领域深度资讯追踪平台 - 用AI筛选AI资讯，为技术决策者提供每日精选动态与深度周报

**核心价值：**
- 每天采集300-500条AI资讯
- AI智能评分与分类（0-100分，8大类别）
- 人工审核质量控制
- 多渠道发布（微信、小红书、Web）

**关键文档：**
- 📄 [产品需求](docs/product/requirements.md) - 完整的产品定义
- 🏗️ [系统设计](docs/tech/system-design-summary.md) - 技术架构总览
- 📚 [技术架构详解](docs/tech/architecture.md) - 深度系统设计

---

## 🚀 快速开始

### 新成员入门（30分钟）

```bash
# 1. 阅读本文件 (5分钟)
# 你现在在做这个

# 2. 阅读规范概览 (5分钟)
# 👉 .claude/standards/00-overview.md

# 3. 阅读快速参考卡片 (10分钟)
# 👉 .claude/standards/99-quick-reference.md

# 4. 初始化开发环境 (5分钟)
bash .claude/tools/setup-standards.sh

# 5. 完成第一个任务
# 参考相关规范文档进行开发
```

### Agent启动流程

```
1. 读本文件（CLAUDE.md）- 了解项目和规范体系
   ↓
2. 根据任务类型读相关规范 - 参考 .claude/standards/
   ↓
3. 查看模板（如需要）- 参考 .claude/templates/
   ↓
4. 开始开发 - 遵循规范，使用自动化工具检查
```

---

## 📋 规范体系导航

所有规范存放在 `.claude/standards/` 目录下，分为以下主题：

| # | 规范文档 | 目的 | 目标读者 |
|---|---------|------|--------|
| 00 | [OVERVIEW](`.claude/standards/00-overview.md`) | 规范导航和学习路径 | 新成员、Agent |
| 01 | [项目初始化](`.claude/standards/01-project-setup.md`) | 环境配置、依赖安装 | 新成员、DevOps |
| 02 | [目录结构](`.claude/standards/02-directory-structure.md`) | 项目组织规范 | 所有开发者 |
| 03 | [命名规范](`.claude/standards/03-naming-conventions.md`) | 代码、文件、数据库命名 | 所有开发者 |
| 04 | [Python代码风格](`.claude/standards/04-python-code-style.md`) | 代码编写、最佳实践 | 后端开发者 |
| 05 | [API设计](`.claude/standards/05-api-design.md`) | RESTful设计、schema | API开发者 |
| 06 | [数据库设计](`.claude/standards/06-database-design.md`) | 表设计、迁移、索引 | DBA、后端 |
| 07 | [测试规范](`.claude/standards/07-testing-standards.md`) | 单元测试、覆盖率 | 所有开发者 |
| 08 | [Git工作流](`.claude/standards/08-git-workflow.md`) | 分支、提交、审查 | 所有开发者 |
| 09 | [文档规范](`.claude/standards/09-documentation.md`) | 代码注释、文档编写 | 所有开发者 |
| 10 | [安全规范](`.claude/standards/10-security.md`) | 密钥管理、输入验证 | 所有开发者 |
| 11 | [部署规范](`.claude/standards/11-deployment.md`) | Docker、K8s、CI/CD | DevOps、后端 |
| 99 | [快速参考](`.claude/standards/99-quick-reference.md`) | 速查表和常用命令 | 所有人 |

---

## 🎓 学习路径

### 🟢 Level 1: 快速上手（30分钟）
**适合：** 新成员第一天、临时任务

```
1. CLAUDE.md (本文件)          [5分钟]
2. 00-overview.md              [5分钟]
3. 99-quick-reference.md       [10分钟]
4. 相关规范1个                 [10分钟]
```

### 🟡 Level 2: 深度掌握（2-3小时）
**适合：** 新成员第一周、长期参与项目

```
必读：
  - 02-directory-structure.md
  - 03-naming-conventions.md
  - 04-python-code-style.md
  - 07-testing-standards.md
  - 08-git-workflow.md

可选（按需）：
  - 05-api-design.md (API开发)
  - 06-database-design.md (DB开发)
  - 09-documentation.md
  - 10-security.md
```

### 🔴 Level 3: 完全精通（1天）
**适合：** 架构师、tech lead、规范维护者

```
按顺序阅读所有规范文档（00-11）
理解每个规范的背后原因
掌握规范的演进机制
```

---

## 🔧 工具和支持

### 自动化工具

```bash
# 初始化规范环境
bash .claude/tools/setup-standards.sh

# 一键检查所有规范
bash .claude/tools/check-all.sh

# 自动修复规范问题
bash .claude/tools/auto-fix.sh

# 检查项目健康度
bash .claude/tools/health-check.sh

# 验证提交规范
bash .claude/tools/validate-commit.sh
```

### 代码模板

所有模板存放在 `.claude/templates/` 目录：

```
API端点:          .claude/templates/api/endpoint.py.template
服务类:          .claude/templates/service/service.py.template
单元测试:        .claude/templates/api/test_endpoint.py.template
数据库迁移:      .claude/templates/database/migration.py.template
功能文档:        .claude/templates/docs/feature.md.template
```

### Git Hooks

自动化规范检查和修复：

```bash
# 安装Git hooks
bash .claude/hooks/install-hooks.sh

# Hooks会在提交时自动：
# ✅ 格式化代码（black）
# ✅ 检查代码风格（flake8）
# ✅ 类型检查（mypy）
# ✅ 验证提交信息（Conventional Commits）
```

---

## 📚 关键规范摘要

### 核心原则

```
1️⃣  一致性 > 灵活性
    所有代码、文件、配置风格必须一致
    不允许个人风格，团队风格是唯一标准

2️⃣  可维护性 > 聪明代码
    代码应该易于理解
    宁可多写代码，也不要有歧义

3️⃣  安全性 > 速度
    必须经过充分测试和审查
    安全问题是阻塞项
```

### 目录结构（MUST）

```
src/                 ← 所有源代码必须在这里
tests/               ← 所有测试代码必须在这里
docs/                ← 所有文档必须在这里
.claude/             ← 规范和配置
```

### 命名规范（MUST）

```
文件名:       snake_case              (content_manager.py)
类名:         PascalCase              (class ContentManager)
函数/变量:    snake_case              (def process_content())
常量:         UPPER_CASE              (MAX_RETRY_COUNT = 3)
数据库表:     snake_case              (data_sources, raw_news)
API路由:      kebab-case小写          (/api/v1/news-items)
分支名:       feature/FEATURE-xxx-desc (feature/001-add-rss)
```

### 代码风格（MUST）

```bash
# 所有代码必须通过以下检查：
black src/           # 代码格式化 (max-line-length=88)
flake8 src/          # 风格检查
mypy src/            # 类型检查
pytest               # 测试 (覆盖率>85%)
```

### 提交规范（MUST）

```
遵循 Conventional Commits 格式：

<type>(<scope>): <subject>

<body>

<footer>

例子：
✅ feat(collection): add RSS feed parser
✅ fix(ai): handle timeout error gracefully
✅ docs: update installation guide

分支名称：
✅ feature/001-add-rss-support
✅ bugfix/fix-simhash-collision
```

### 测试覆盖率（MUST）

```
最小要求：      > 85%
核心服务：      > 95%
API层：         > 90%

运行测试：
pytest --cov=src --cov-fail-under=85
```

---

## ⚠️ 规范强制级别

| 级别 | 标记 | 说明 | 违反后果 |
|------|------|------|--------|
| **MUST** | 🔴 | 必须遵守，无例外 | 代码无法merge |
| **SHOULD** | 🟡 | 强烈建议遵守 | Code review时需说明 |
| **MAY** | 🟢 | 可选，但推荐 | 不强制，但鼓励 |

**注意：** 在本项目中，所有 SHOULD 也视为 MUST 处理（严格型）

---

## 📅 规范检查清单

### 开发前
- [ ] 创建feature分支，命名遵循规范
- [ ] 更新README或相关文档
- [ ] 创建测试文件（测试优先开发）

### 开发中
- [ ] 代码符合命名规范
- [ ] 代码通过black格式化
- [ ] 代码通过flake8检查
- [ ] 代码通过mypy类型检查
- [ ] 所有函数都有类型注解和docstring
- [ ] 写了单元测试（覆盖率>85%）
- [ ] 没有硬编码密钥或敏感信息
- [ ] 异常处理完善

### 提交前
- [ ] 本地测试全部通过
- [ ] 本地linting检查通过
- [ ] 分支名遵循规范
- [ ] 提交信息遵循Conventional Commits
- [ ] 更新了CHANGELOG.md

### Pull Request
- [ ] PR标题清晰明确
- [ ] PR描述完整（背景、改动、测试）
- [ ] 至少1个reviewer审核
- [ ] 所有自动检查通过
- [ ] Code review通过

---

## 🆘 常见问题

### Q: 规范太多了，怎么快速上手？
**A:** 先读 `.claude/standards/99-quick-reference.md`，30分钟掌握核心规范。

### Q: 如何快速检查代码是否符合规范？
**A:** 运行 `bash .claude/tools/check-all.sh`

### Q: 如何自动修复规范问题？
**A:** 运行 `bash .claude/tools/auto-fix.sh`

### Q: Git hooks总是阻止我提交怎么办？
**A:** 运行 `bash .claude/tools/auto-fix.sh`，它会自动修复大部分问题。

### Q: 我发现规范有问题怎么办？
**A:** 提出Issue并创建PR修改 `.claude/standards/` 中的相应文档。

---

## 📞 联系方式

- **规范相关问题：** 提出Issue标记为 `question/standards`
- **规范改进建议：** 提出PR修改 `.claude/standards/`
- **工具问题：** 提出Issue标记为 `bug/tools`

---

## 📖 推荐阅读顺序

### 如果你要...

**...创建新的API端点**
1. `.claude/standards/05-api-design.md`
2. `.claude/templates/api/endpoint.py.template`
3. `.claude/templates/api/test_endpoint.py.template`

**...修复一个bug**
1. `.claude/standards/08-git-workflow.md` (分支命名)
2. `.claude/standards/04-python-code-style.md` (代码风格)
3. `.claude/standards/07-testing-standards.md` (测试)

**...添加新的服务**
1. `.claude/standards/04-python-code-style.md`
2. `.claude/standards/06-database-design.md` (如涉及DB)
3. `.claude/templates/service/service.py.template`

**...修改数据库**
1. `.claude/standards/06-database-design.md`
2. `.claude/standards/02-directory-structure.md`
3. `.claude/templates/database/migration.py.template`

---

## ✅ 验收标准

代码被认为符合规范，当且仅当：

```
✅ 通过所有自动化检查 (black, flake8, mypy, pytest)
✅ 通过代码审查
✅ 遵守所有 MUST-HAVE 规范
✅ 测试覆盖率 > 85%
✅ 文档完整清晰
✅ 没有安全漏洞
```

---

## 🎯 下一步

- [ ] **新成员：** 阅读 `.claude/standards/00-overview.md`
- [ ] **开始开发：** 查看 `.claude/standards/99-quick-reference.md`
- [ ] **设置环境：** 运行 `bash .claude/tools/setup-standards.sh`
- [ ] **提交代码：** 遵循 `.claude/standards/08-git-workflow.md`

---

**项目遵循业界最佳实践，采用严格的规范体系。**
**通过自动化工具和清晰的文档，保证代码质量和团队高效协作。**

**开始第一个任务前，请务必阅读相关规范文档！** 📚

