# Claude Code Agent 交接协议

**版本:** 1.0
**发布日期:** 2025-11-02
**适用范围:** 所有多Agent协作任务

---

## 📋 概述

本协议规定了Claude Code Agent在处理长期或复杂任务时的交接标准和流程，确保任务的连续性、知识的完整转移、和工作的可追踪性。

---

## 🎯 核心原则

### 1. **提前交接**
- Agent必须在Token窗口达到**70%**容量时启动交接流程
- 不应等到窗口极限才交接（避免仓促和不完整）
- 给予充足时间完成交接文档

### 2. **完整性**
- 交接文档必须包含所有必要信息
- 下一个Agent应能独立继续工作，无需回头查阅
- 包含所有上下文、决策和已知问题

### 3. **可追踪性**
- 所有交接必须生成正式文档
- 文档存放在专门的`.claude/handoff/`目录
- 包含交接时间戳和参与方信息

### 4. **质量保证**
- 所有代码必须通过测试和linting
- 未完成的任务必须清晰标记
- 包含验收清单和已知问题

---

## 📂 交接文档结构

### 目录位置
```
.claude/handoff/
├── PHASE-1-COMPLETION-REPORT.md
├── PHASE-2-COMPLETION-REPORT.md
├── PHASE-3-IN-PROGRESS.md
├── ACTIVE-ISSUES.md
├── DECISIONS-LOG.md
└── NEXT-AGENT-INSTRUCTIONS.md
```

### 必需文件类型

#### 1. **Phase Completion Report** (阶段完成报告)
**触发条件:** 当一个完整阶段结束时
**文件名:** `PHASE-N-COMPLETION-REPORT.md`

**必需内容:**
- 执行摘要
- 完成的所有任务列表
- 每个Task的详细说明
- 代码统计（行数、文件数等）
- 测试覆盖率
- 验收清单
- 已知限制

**示例:**
```markdown
# Phase 2 完成交接报告

## 📋 执行摘要
简述本阶段成就

## 🎯 完成的任务
- Task 2.1: ... ✅
- Task 2.2: ... ✅
- Task 2.3: ... ✅

## 📊 统计数据
- 创建文件: 12个
- 代码行数: 2,000+
- 测试覆盖率: 94%

## ✅ 验收清单
- [x] 代码通过linting
- [x] 所有测试通过
- [x] 文档完整

## 📞 支持信息
...
```

#### 2. **In-Progress Report** (进行中报告)
**触发条件:** 当需要中途交接时
**文件名:** `PHASE-N-IN-PROGRESS.md`

**必需内容:**
- 当前进度百分比
- 已完成的子任务
- 正在进行的任务及完成度
- 剩余任务列表
- 遇到的阻塞及解决方案
- 临时决策
- 下一个Agent可立即执行的步骤

#### 3. **Active Issues** (活跃问题)
**触发条件:** 总是维护
**文件名:** `ACTIVE-ISSUES.md`

**必需内容:**
- 已知Bug列表
- 待优化的代码部分
- 依赖项版本问题
- 环境配置问题
- 优先级和影响评估

#### 4. **Decisions Log** (决策日志)
**触发条件:** 当做出重要架构/设计决策时
**文件名:** `DECISIONS-LOG.md`

**必需内容:**
- 决策背景
- 评估的选项
- 最终选择及理由
- 做出决策的日期和Agent
- 可能的后续影响

#### 5. **Next Agent Instructions** (下一个Agent指令)
**触发条件:** 每个交接时
**文件名:** `NEXT-AGENT-INSTRUCTIONS.md`

**必需内容:**
- 立即可执行的步骤
- 环境设置指南
- 关键命令参考
- 文件位置导航
- 快速启动检查清单

---

## 🔄 交接流程

### 步骤1: 识别交接触发点（Token 70%）
```python
# 当消息已消耗Token达到总容量的70%时
token_used = current_token_count
token_limit = max_token_count
if token_used / token_limit >= 0.70:
    # 启动交接流程
    trigger_handoff()
```

### 步骤2: 确保代码质量（15分钟）
- [ ] 运行所有测试 `pytest`
- [ ] 检查代码风格 `black`, `flake8`, `mypy`
- [ ] 最后一次git commit
- [ ] 验证分支状态 `git status`

### 步骤3: 生成交接文档（10分钟）
- [ ] 创建Phase Completion/In-Progress Report
- [ ] 更新Active Issues
- [ ] 添加Decisions到日志
- [ ] 生成Next Agent Instructions
- [ ] 检查文档完整性

### 步骤4: 提交交接（5分钟）
- [ ] Git add交接文档
- [ ] 创建提交: `docs(handoff): prepare phase N transition`
- [ ] Push到远程分支
- [ ] 验证文档在GitHub可访问

### 步骤5: 最后通知（2分钟）
```
## 🔄 自动启动交接 - Phase N 进度报告

✅ 已完成
- Task N.1: ... ✓
- Task N.2: ... ✓

⏳ 进行中
- Task N.3: 75% 完成

📝 待继续
- Task N.4: 需要执行

🎯 下一个Agent应执行
1. 检查 .claude/handoff/NEXT-AGENT-INSTRUCTIONS.md
2. 运行 pytest 验证当前代码
3. 从Task N.3继续工作

状态: ⏳ 接近token极限，自动交接。
```

---

## 📝 交接文档模板

### Phase Completion Report 模板

```markdown
# Phase N 完成交接报告

**报告日期:** YYYY-MM-DD
**完成状态:** ✅ 已完成 / ⏳ 进行中
**分支:** feature/xxx
**最新提交:** COMMIT_HASH - commit message

## 📋 执行摘要
[简述本阶段目标和成就]

## 🎯 完成的任务
### Task N.1: [描述]
- ✅ 子任务1
- ✅ 子任务2

### Task N.2: [描述]
- ✅ 子任务1

## 📊 统计数据
| 指标 | 数值 |
|------|------|
| 创建文件 | X个 |
| 代码行数 | Y行 |
| 测试数 | Z个 |
| 覆盖率 | W% |

## ✅ 验收清单
- [x] 代码通过linting
- [x] 所有测试通过
- [x] 文档完整
- [x] 可以合并到主分支

## 🚀 下一步
- [ ] 合并到主分支
- [ ] Task N.3: 开始工作

## 📞 支持信息
[关键决策、已知问题、调试建议]
```

### In-Progress Report 模板

```markdown
# Phase N 进行中报告

**生成时间:** YYYY-MM-DD HH:MM UTC+8
**预期完成:** YYYY-MM-DD
**当前进度:** X% (N/M tasks)

## ✅ 已完成
- Task N.1 ✓
- Task N.2 ✓

## ⏳ 进行中
- Task N.3: 75% 完成
  - 完成部分: ...
  - 剩余工作: ...

## 📋 待执行
- Task N.4
- Task N.5

## 🎯 下一个Agent立即执行
1. 继续完成Task N.3的[具体部分]
2. 运行 `pytest tests/xxx`
3. 提交当前进度

## ⚠️ 已知阻塞
- [描述问题和解决方案]

## 🔧 临时决策
- [描述任何临时决策和后续改进计划]
```

---

## 🚀 下一个Agent的快速启动

### 1. 阅读文档（5分钟）
```bash
# 必读
cat .claude/handoff/NEXT-AGENT-INSTRUCTIONS.md

# 参考
cat .claude/handoff/PHASE-N-COMPLETION-REPORT.md
cat .claude/DECISIONS-LOG.md
```

### 2. 验证环境（2分钟）
```bash
# 检查分支
git branch

# 运行测试
pytest tests/unit -v

# 检查风格
black --check src/
flake8 src/
```

### 3. 继续工作（即时）
```bash
# 从交接文档中找到具体的下一步任务
# 按照 NEXT-AGENT-INSTRUCTIONS.md 中的步骤执行
```

---

## 📊 Token 使用指南

### Token 预算分配（典型100k任务）
```
70,000 (70%)  ← 交接触发点
│
├─ 0-50,000    主要工作 (50%)
├─ 50,000-70,000 收尾工作 (20%)
│
└─ 70,000-100,000 交接文档和Buffer (30%)
  ├─ 生成交接文档 (10%)
  ├─ 代码质量检查 (10%)
  └─ 通知消息 (10%)
```

### 优化技巧
- 使用Task工具进行复杂查询（减少token）
- 提前计划交接点
- 压缩冗余信息
- 使用清单而不是详细说明

---

## ✅ 检查清单

### Agent在交接前应完成
- [ ] 所有代码通过linting (black, flake8, mypy)
- [ ] 所有测试通过
- [ ] 没有遗留的TODO或FIXME
- [ ] Git分支clean（无未提交更改）
- [ ] 最新提交包含有意义的消息
- [ ] 所有交接文档已完成
- [ ] 文档已push到远程

### 下一个Agent应在启动前检查
- [ ] 已读NEXT-AGENT-INSTRUCTIONS.md
- [ ] 已读PHASE-COMPLETION-REPORT.md
- [ ] 本地repo已sync (`git pull`)
- [ ] 可以运行 `pytest` 成功
- [ ] 理解当前的代码结构和设计决策

---

## 🎯 最佳实践

### DO ✅
- ✅ 定期git commit（每个logical unit）
- ✅ 在交接文档中包含命令和脚本
- ✅ 为下一个Agent写清晰的step-by-step指南
- ✅ 记录所有关键决策
- ✅ 包含调试技巧和常见问题
- ✅ 提前70%时启动交接

### DON'T ❌
- ❌ 在交接前最后时刻匆忙提交
- ❌ 留下未完成的代码或文档
- ❌ 隐藏已知问题
- ❌ 假设下一个Agent了解上下文
- ❌ 只写"见git log"作为文档
- ❌ 等到100% token才交接

---

## 📞 支持和改进

### 问题报告
如果交接文档不清楚或缺少信息：
1. 提出Issue标记为 `question/handoff`
2. 提供具体的缺失信息
3. 建议改进

### 改进建议
1. 基于实际经验改进此协议
2. 提PR修改此文件
3. 参与Agent工作流的持续优化

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2025-11-02 | 初始版本 |

---

**最后更新:** 2025-11-02
**维护者:** Project AI
**下一次审查:** 2025-12-02

