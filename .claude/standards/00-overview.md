# 规范体系概览与导航

**版本：** 1.0
**目标读者：** 新成员、Agent
**阅读时间：** 5分钟
**必读：** YES

---

## 🎯 本文档目的

本文档为 DeepDive Tracking 规范体系的导航手册，帮助你快速了解：
- 规范体系的全貌
- 每个规范文档的作用
- 推荐的学习路径
- 如何快速找到你需要的规范

---

## 📚 规范体系全景

```
DeepDive Tracking 规范体系
│
├─ 基础规范（必读）
│  ├─ 02-directory-structure.md      目录组织
│  ├─ 03-naming-conventions.md       命名规范
│  └─ 08-git-workflow.md             Git工作流
│
├─ 开发规范
│  ├─ 04-python-code-style.md        Python代码
│  ├─ 07-testing-standards.md        测试规范
│  └─ 09-documentation.md            文档规范
│
├─ 高级规范
│  ├─ 05-api-design.md               API设计
│  ├─ 06-database-design.md          数据库设计
│  ├─ 10-security.md                 安全规范
│  └─ 11-deployment.md               部署规范
│
├─ 工具和模板
│  ├─ .claude/tools/                 自动化工具
│  ├─ .claude/templates/             代码模板
│  └─ .claude/hooks/                 Git hooks
│
└─ 快速参考
   └─ 99-quick-reference.md          速查表
```

---

## 📖 规范文档详解

### 🔵 基础规范（第一天必读）

#### 02-directory-structure.md
**内容：** 项目目录组织规范
**重点：** `src/`, `tests/`, `docs/` 等目录结构
**必读：** YES
**何时需要：** 创建新文件、新目录时

#### 03-naming-conventions.md
**内容：** 所有层级的命名规范
**包括：** 文件、类、函数、变量、数据库、API路由等
**必读：** YES
**何时需要：** 命名任何代码元素时

#### 08-git-workflow.md
**内容：** Git工作流、分支策略、提交规范
**重点：** Conventional Commits、分支命名、PR流程
**必读：** YES
**何时需要：** 提交代码、创建PR时

---

### 🟠 开发规范（第一周深度学习）

#### 04-python-code-style.md
**内容：** Python代码编写规范
**包括：** 代码格式、类型注解、文档字符串、异常处理等
**目标读者：** 后端开发者
**何时需要：** 编写Python代码时

#### 07-testing-standards.md
**内容：** 单元测试、集成测试、覆盖率要求
**重点：** 测试金字塔、测试用例编写、覆盖率>85%
**目标读者：** 所有开发者
**何时需要：** 编写测试时

#### 09-documentation.md
**内容：** 代码注释、文档编写规范
**包括：** docstring、README、API文档等
**目标读者：** 所有开发者
**何时需要：** 编写注释或文档时

---

### 🔴 高级规范（按需深度学习）

#### 05-api-design.md
**内容：** API设计、RESTful规范、schema定义
**目标读者：** API开发者
**何时需要：** 创建新的API端点时

#### 06-database-design.md
**内容：** 数据库表设计、migration、索引等
**目标读者：** DBA、数据库开发者
**何时需要：** 修改数据库schema时

#### 10-security.md
**内容：** 安全最佳实践、密钥管理、输入验证等
**目标读者：** 所有开发者
**何时需要：** 处理敏感信息或用户输入时

#### 11-deployment.md
**内容：** Docker、Kubernetes、CI/CD部署
**目标读者：** DevOps、后端开发者
**何时需要：** 部署或配置CI/CD时

---

## 🎓 学习路径

### 🟢 快速上手（30分钟）
**适合：** 临时任务、快速bug修复

1. 本文档 (5分钟)
2. 03-naming-conventions.md (5分钟)
3. 99-quick-reference.md (15分钟)
4. 相关具体规范 (5分钟，按需)

### 🟡 深度学习（2-3小时）
**适合：** 新成员第一周

**第一天：**
- 03-naming-conventions.md
- 04-python-code-style.md
- 08-git-workflow.md

**第二天：**
- 02-directory-structure.md
- 07-testing-standards.md

**第三天：**
- 09-documentation.md
- 05-api-design.md（如需要）

### 🔴 完全精通（1天）
**适合：** tech lead、架构师、规范维护者

按顺序阅读所有规范文档（00-11）

---

## 🛠️ 工具和模板

### 自动化工具

所有工具存放在 `.claude/tools/` 目录：

```bash
setup-standards.sh    初始化环境
check-all.sh          一键检查所有规范
auto-fix.sh           自动修复规范问题
health-check.sh       项目健康检查
validate-commit.sh    验证提交规范
```

### 代码模板

所有模板存放在 `.claude/templates/` 目录，可快速生成符合规范的代码：

```
api/endpoint.py.template          API端点
service/service.py.template       服务类
api/test_endpoint.py.template     测试代码
database/migration.py.template    数据库迁移
docs/feature.md.template          功能文档
```

### Git Hooks

自动化规范检查和修复，安装后在每次提交时执行：

```bash
bash .claude/hooks/install-hooks.sh
```

---

## 📋 按任务类型查找规范

### 我要...

**...创建新的API端点**
- 🔗 05-api-design.md (设计规范)
- 📝 03-naming-conventions.md (API路由命名)
- 🧪 07-testing-standards.md (测试)

**...修复一个bug**
- 🌳 08-git-workflow.md (创建bugfix分支)
- 💻 04-python-code-style.md (代码风格)
- 🧪 07-testing-standards.md (编写测试)

**...添加新的服务类**
- 📁 02-directory-structure.md (文件位置)
- 💻 04-python-code-style.md (代码编写)
- 🧪 07-testing-standards.md (单元测试)

**...修改数据库**
- 🗄️ 06-database-design.md (表设计、migration)
- 📝 03-naming-conventions.md (表和列命名)

**...编写文档**
- 📚 09-documentation.md (文档规范)
- 📝 03-naming-conventions.md (变量名、函数名)

**...发布代码**
- 🌳 08-git-workflow.md (提交、PR、merge)
- 🚀 11-deployment.md (部署流程)

**...处理敏感信息**
- 🔒 10-security.md (密钥管理、加密)

---

## ✅ 规范检查清单

在提交代码前，快速检查：

```
基础检查：
□ 文件名命名正确
□ 代码通过black格式化
□ 代码通过flake8检查
□ 代码通过mypy类型检查

功能检查：
□ 有相应的测试
□ 测试覆盖率>85%
□ 有完整的docstring
□ 没有硬编码密钥

Git检查：
□ 分支名遵循规范
□ 提交信息遵循Conventional Commits
□ PR描述完整

文档检查：
□ 更新了相关文档
□ 更新了CHANGELOG.md
```

---

## 🚀 快速开始

### 第一次使用？

1. **初始化环境**
   ```bash
   bash .claude/tools/setup-standards.sh
   ```

2. **检查项目健康度**
   ```bash
   bash .claude/tools/health-check.sh
   ```

3. **开始开发**
   - 参考相关规范文档
   - 使用模板快速创建代码
   - 提交前运行 `bash .claude/tools/check-all.sh`

### 遇到问题？

1. **快速查找规范**
   - 查看本文档的"按任务类型查找规范"部分
   - 或查看 `.claude/standards/99-quick-reference.md`

2. **自动修复问题**
   ```bash
   bash .claude/tools/auto-fix.sh
   ```

3. **获取帮助**
   - 阅读相关规范文档
   - 查看示例代码

---

## 📞 我该找谁？

| 问题类型 | 查看文档 |
|---------|--------|
| 命名、文件位置等 | 02, 03 |
| 代码风格、格式等 | 04 |
| API接口设计 | 05 |
| 数据库表设计 | 06 |
| 测试编写 | 07 |
| Git工作流、提交 | 08 |
| 注释、文档 | 09 |
| 密钥、安全 | 10 |
| Docker、部署 | 11 |
| 快速查找 | 99 |

---

## 🎯 下一步

- **新成员：** 阅读基础规范（02, 03, 08）
- **开始任务：** 查看 99-quick-reference.md
- **遇到问题：** 按任务类型查找相关规范
- **报告问题：** 提出Issue或PR

---

**记住：** 规范存在是为了让团队更高效协作，质量更高。
**每次遵守规范都是在为整个项目加分！** ✨

