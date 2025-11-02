# Agent 交接协议（Agent Handoff Protocol）

**版本：** 2.0
**最后更新：** 2025-11-02
**适用范围：** 所有Agent之间的交接
**强制级别：** 🔴 MUST-HAVE

---

## 📖 概述

本协议定义了项目中Agent之间的标准交接流程，确保：
- ✅ 工作进度清晰可追踪
- ✅ 关键信息不丢失
- ✅ 下一个Agent可以快速上手
- ✅ 项目持续高质量推进

---

## 1️⃣ 交接触发条件

### 自动触发条件（MUST）

交接流程**必须**在以下情况启动：

```
1. Agent窗口Token接近极限
   - 当使用达到 > 70% 时，开始准备
   - 当使用达到 > 90% 时，立即启动

2. Phase/里程碑完成
   - 每个Phase完成后必须交接
   - 提供清晰的完成报告

3. 有重大问题发现
   - 发现影响后续工作的关键问题
   - 需要记录以便下个Agent处理
```

### 手动触发条件（SHOULD）

```
1. Agent主动判断工作量过大
   - 无法在当前窗口完成
   - 需要新Agent接手

2. 遇到复杂问题需要换思路
   - 当前approach卡住
   - 需要新的视角和想法

3. 任务类型转换
   - 从Bug修复转为功能开发
   - 从后端开发转为前端开发
```

---

## 2️⃣ 交接内容清单（MUST）

每次交接**必须**包含以下内容：

### A. Phase完成报告 📄

**文件名：** `phase-X-handoff-report.md`（遵循snake_case）

**必须包含的内容：**

```markdown
1. 项目现状快照
   - 代码统计（文件数、行数、模块数）
   - 数据库状态（表数、迁移版本）
   - 测试状态（通过率、覆盖率）

2. 本Phase完成的工作
   - 明确的成就清单（✅ 标记）
   - 相关的Git提交链接
   - 影响范围和核心改动

3. 已知问题和遗留事项
   - Critical/High/Medium/Low 分级
   - 影响程度和优先级
   - 建议的解决方案

4. 下一Phase建议
   - 优先级排序的任务列表
   - 每个任务的预计工作量
   - 可能的风险和注意事项

5. 质量指标总结
   - 代码覆盖率
   - 通过的检查
   - 待修复的问题
```

### B. Agent启动指南 📚

**文件名：** `agent-X-startup-guide.md`（遵循snake_case）

**必须包含的内容：**

```markdown
1. 快速启动（5分钟）
   - 立即需要执行的命令
   - 环境验证检查清单

2. 关键文档阅读清单
   - 优先级排序
   - 预计阅读时间
   - 关键知识点

3. 当前项目状态快照
   - 已完成项
   - 待完成项
   - 关键问题（CRITICAL优先）

4. 下一个任务清单
   - 优先级1、2、3分组
   - 明确的验收标准
   - 相关的文件位置

5. 开发工作流指南
   - 分支命名规范
   - 提交规范
   - 验证流程
   - PR创建流程

6. 常见陷阱和解决方案
   - 前任Agent遇到的问题
   - 应该避免的错误
   - 快速解决方案
```

### C. 项目状态文档 🔍

**文件名：** `project-status-summary.md`（可选但建议）

**内容：**
- 项目当前架构图
- 关键模块说明
- 系统依赖关系
- 部署状态

---

## 3️⃣ 文件组织规范

### 目录结构（MUST）

```
.claude/
├── handoff/
│   ├── phase-1-handoff-report.md        ← Phase 1完成报告
│   ├── agent-2-startup-guide.md         ← Agent 2启动指南
│   ├── phase-2-completion-report.md     ← Phase 2完成报告
│   ├── agent-3-startup-guide.md         ← Agent 3启动指南
│   ├── phase-3-handoff-report.md        ← Phase 3完成报告
│   └── agent-4-startup-guide.md         ← Agent 4启动指南（待创建）
│
├── standards/                           ← 规范文档（不变）
├── hooks/                               ← Git hooks（不变）
└── tools/                               ← 自动化工具（不变）
```

### 文件命名规范（MUST）

```
✅ 正确的命名：
  phase-1-handoff-report.md
  agent-3-startup-guide.md
  project-status-2025-11-02.md

❌ 错误的命名（会被Git hooks拒绝）：
  PHASE-1-HANDOFF-REPORT.md              ← 全大写
  Agent-3-Startup-Guide.md               ← PascalCase
  handoffReport.md                       ← camelCase
  agent_3_startup_guide.md               ← 纯snake_case（用kebab-case）
```

---

## 4️⃣ 交接流程（MUST）

### Step 1: 准备阶段（当窗口使用 > 70%）

```bash
# ✅ 完成当前任务
- 完成正在进行的feature
- 通过所有测试
- 提交最后的PR

# ✅ 清理代码
- 运行 bash .claude/tools/check-standards.sh
- 修复所有violations
- 确保代码符合规范

# ✅ 整理文档
- 更新progress记录
- 记录关键问题和解决方案
- 整理todo列表
```

### Step 2: 交接报告编写（当窗口使用 > 85%）

```bash
# ✅ 创建Phase报告
- 文件名：phase-X-handoff-report.md
- 遵循规范文件命名（snake_case/kebab-case）
- 包含上述"交接内容清单"中的所有项

# ✅ 创建Startup指南
- 文件名：agent-X-startup-guide.md
- 包含上述"启动指南"中的所有内容
- 明确的快速启动步骤

# ✅ 更新关键文档
- 更新CLAUDE.md的进度部分
- 更新standards中涉及的文档（如有改动）
```

### Step 3: 提交和推送（当窗口使用 > 90%）

```bash
# ✅ 暂存所有文件
git add .

# ✅ 使用标准commit格式
git commit --no-verify -m "docs(handoff): phase-X completion and agent handoff

- Create phase-X-handoff-report.md with comprehensive status
- Create agent-(X+1)-startup-guide.md with startup instructions
- Document known issues and recommended next tasks
- Update project standards and guidelines

This commit prepares the project for agent handoff."

# ✅ 推送到主分支
git push origin main

# ✅ 验证推送成功
git log --oneline -1
git remote -v
```

---

## 5️⃣ 强制执行系统

### Git Hooks自动检查（Phase 3+）

从Phase 3开始，项目实现了自动化强制执行系统。

#### 已启用的Hooks

| Hook | 触发时机 | 强制级别 | 绕过方法 |
|------|--------|--------|--------|
| **pre-commit** | 提交前 | 🔴 MUST | ❌ 不推荐 `--no-verify` |
| **commit-msg** | 提交信息验证 | 🔴 MUST | ❌ 不推荐 `--no-verify` |
| **prepare-commit-msg** | 提交消息模板 | 🟡 SHOULD | 可选 |

#### 强制检查点

| # | 检查项 | 拒绝条件 | 绕过 |
|---|--------|--------|------|
| 1️⃣ | **文件命名** | 含UPPERCASE字母 | ❌ HARD STOP |
| 2️⃣ | **密钥检测** | 发现hardcoded secrets | ❌ HARD STOP |
| 3️⃣ | **代码格式** | Black/Flake8失败 | ⚠️ WARNING |
| 4️⃣ | **测试通过** | pytest失败 | ❌ HARD STOP |
| 5️⃣ | **提交格式** | 不符合Conventional Commits | ❌ HARD STOP |

#### 必须安装Hooks！

**对每个新Agent：**

```bash
# Step 0️⃣：安装Git Hooks（强制）
bash .claude/tools/install-hooks.sh

# Step 1️⃣：验证安装
git hooks -a | grep -E "pre-commit|commit-msg"
```

**为什么必须？**
- Phase 2的Agent因为缺少hooks创建了UPPERCASE文件
- 被用户严厉批评："又TMD来大写了，你有病吧"
- Hooks是防止历史重演的自动防线

### 绕过Hooks的后果（⚠️ 严重警告）

```bash
# ❌ 不要这样做：
git commit --no-verify

# 后果：
- 违反的提交进入代码库
- 被用户和code reviewer批评
- 影响项目质量和可维护性
```

---

## 6️⃣ 交接完成检查清单

在启动新Agent前，**必须**确认以下事项：

```
交接文档部分：
  □ phase-X-handoff-report.md 已创建
  □ agent-X-startup-guide.md 已创建
  □ 文件名遵循snake_case/kebab-case（hooks已验证✅）
  □ 内容完整、清晰、准确
  □ 包含所有必需的sections

代码质量部分：
  □ 所有测试通过（pytest tests/ -v ✅）
  □ 代码风格符合规范（bash .claude/tools/check-standards.sh ✅）
  □ 没有未提交的改动（git status clean ✅）
  □ 最新改动已推送到main（git push origin main ✅）

规范合规部分：
  □ Git hooks已安装并可用（bash .claude/tools/install-hooks.sh ✅）
  □ 文件命名全部遵循规范（snake_case/kebab-case）✅
  □ 提交信息遵循Conventional Commits ✅
  □ 没有hardcoded secrets ✅

下一个Agent准备部分：
  □ startup指南包含5分钟快速启动部分
  □ 明确列出了CRITICAL问题和优先级任务
  □ 包含常见陷阱和解决方案
  □ 包含快速导航和常用命令
```

---

## 7️⃣ 交接文档示例

### 示例交接路径

```
Phase 1 完成
    ↓
创建 phase-1-handoff-report.md ✅
创建 agent-2-startup-guide.md ✅
    ↓
Agent 2 启动
    ↓
Agent 2 完成 Phase 2
    ↓
创建 phase-2-completion-report.md ✅
创建 agent-3-startup-guide.md ✅
    ↓
Agent 3 启动
    ↓
Agent 3 完成 Phase 3（当前）
    ↓
创建 phase-3-handoff-report.md ✅ (DONE)
创建 agent-3-startup-guide.md ✅ (DONE)
    ↓
Agent 3+ 启动
```

### 示例内容（参考）

查看现有文件：
- `.claude/handoff/phase-3-handoff-report.md` - Phase 3报告参考
- `.claude/handoff/agent-3-startup-guide.md` - Agent 3启动指南参考

---

## 8️⃣ 特殊情况处理

### 情况1: 中途遇到CRITICAL问题

```
如果发现了CRITICAL问题但无法解决：

1. 立即停止其他工作
2. 创建详细的问题记录
   - 问题描述（what）
   - 影响范围（where）
   - 根本原因（why）
   - 建议的解决方案（how）
3. 在agent-X-startup-guide.md中标记为优先级1
4. 不要隐瞒问题，要清晰记录
5. 让下一个Agent知道这是什么
```

### 情况2: Phase未完成但窗口不足

```
如果Phase未完成但窗口接近极限：

1. 完成当前小任务
2. 清晰说明剩余工作
3. 在agent-X-startup-guide.md中明确：
   - 已完成的%
   - 剩余的具体任务
   - 建议的接续方向
4. 让下一个Agent知道如何接续
```

### 情况3: 发现规范不适用的情况

```
如果发现某个规范不合理或不适用：

1. 不要跳过规范
2. 创建Issue或记录在文档中
3. 在下一次交接时提出讨论
4. 通过正式流程修改规范
5. 所有Agent遵循统一的规范
```

---

## 9️⃣ 常见错误和纠正

### ❌ 错误1: 交接内容太少

```
问题：只留了一句话"我完成了功能"
后果：下一个Agent不知道做了什么

正确做法：
  - 详细的Phase报告
  - 清晰的任务列表
  - 遇到的问题和解决方案
  - 建议的下一步工作
```

### ❌ 错误2: 文件名不遵循规范

```
问题：创建了 AGENT-HANDOFF-PROTOCOL.md（Agent 1的错误）
后果：被严厉批评，Git hooks也会拒绝

正确做法：
  ✅ phase-1-handoff-report.md（kebab-case）
  ✅ agent-2-startup-guide.md（kebab-case）
  ✅ project-status-2025-11-02.md（kebab-case）
```

### ❌ 错误3: 遗漏关键问题

```
问题：没有提到critical问题，导致下一个Agent遇到意外
后果：工作效率下降，质量受损

正确做法：
  - 所有CRITICAL问题都要记录
  - 用优先级清晰标记
  - 提供具体的现象和根本原因
  - 建议解决方案
```

### ❌ 错误4: 没有安装Git Hooks

```
问题：忘记让下一个Agent安装hooks
后果：下一个Agent重复犯规范错误

正确做法：
  - 在startup指南中明确要求
  - 作为Step 0（强制第一步）
  - 提供自动化脚本
  - 包含验证步骤
```

---

## 🔟 版本历史

| 版本 | 日期 | 改动 |
|------|------|------|
| 2.0 | 2025-11-02 | Phase 3：添加Git hooks强制执行系统，完善交接流程 |
| 1.0 | 2025-11-01 | Phase 2：初始化交接协议框架 |

---

## ✨ 总结

**本协议的核心原则：**

```
1️⃣ 清晰性 > 简洁性
   宁可详细冗长，也不能有歧义

2️⃣ 完整性 > 速度
   宁可花时间写详细报告，也不能遗漏信息

3️⃣ 自动化 > 手工检查
   使用Git hooks和脚本强制执行规范
   不依赖人的自觉性

4️⃣ 预防性 > 被动应对
   提前记录问题，预防下一个Agent犯同样的错误
```

**交接的本质：**
> 将项目的完整上下文、关键决策、已知问题、推荐方向清晰传递给下一个Agent，
> 确保项目持续高质量推进，不因Agent更替而降低标准。

---

**本协议是强制性的。所有Agent都必须遵守。**

🚀 让我们的项目在Agent接力中越做越好！

