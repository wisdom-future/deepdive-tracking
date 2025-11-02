# Git 工作流规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 清晰的分支策略
✅ 原子化的提交
✅ 自解释的提交信息
✅ Code Review 必须
✅ 线性历史记录
```

---

## 分支策略

### 🔴 MUST - 严格遵守

1. **主分支**
   ```
   main          - 生产环境代码，每个提交都是一个发布版本
   develop       - 开发环境代码，所有功能都在这里集成

   ✅ main 和 develop 始终保持稳定
   ❌ 不允许直接推送到 main/develop
   ```

2. **功能分支命名**
   ```
   feature/001-add-rss-parser
   feature/002-implement-ai-scoring
   feature/003-add-wechat-publishing

   格式: feature/{ticket-number}-{description}

   ✅ 命名清晰，包含ticket号
   ❌ feature/new-stuff
   ❌ feature/wip
   ```

3. **Bug修复分支**
   ```
   bugfix/fix-timeout-error
   bugfix/001-fix-simhash-collision

   格式: bugfix/{description} 或 bugfix/{ticket-number}-{description}

   ✅ 从 develop 创建，修复后合并回 develop
   ```

4. **紧急修复分支**
   ```
   hotfix/fix-critical-security-issue
   hotfix/001-critical-database-bug

   格式: hotfix/{ticket-number}-{description}

   ✅ 从 main 创建，修复后合并回 main 和 develop
   ❌ 不允许没有ticket的hotfix
   ```

5. **文档分支**
   ```
   docs/update-api-documentation
   docs/add-installation-guide

   格式: docs/{description}
   ```

6. **测试/性能分支**
   ```
   test/add-integration-tests
   perf/optimize-database-queries

   格式: test/{description} 或 perf/{description}
   ```

### 🟡 SHOULD - 强烈建议

1. **分支从 develop 创建**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/001-add-feature
   ```

2. **及时删除已合并的分支**
   ```bash
   git branch -d feature/001-add-feature
   git push origin -d feature/001-add-feature
   ```

---

## 提交规范

### 🔴 MUST - 严格遵守

遵循 **Conventional Commits** 格式。

1. **基本格式**
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```

2. **Type（类型）必须是以下之一**
   ```
   feat:      新功能
   fix:       bug修复
   refactor:  代码重构（不改变功能）
   test:      添加或修改测试
   docs:      文档更新
   chore:     杂务（依赖更新、构建脚本等）
   perf:      性能优化
   ci:        CI/CD配置更改
   style:     代码格式化（不改变功能）
   revert:    撤销之前的提交
   ```

3. **Scope（作用域）应该是**
   ```
   collection      (新闻采集)
   ai              (AI处理)
   content         (内容管理)
   publishing      (发布)
   api             (API端点)
   database        (数据库)
   cache           (缓存)
   auth            (认证)
   config          (配置)
   utils           (工具)
   ```

4. **Subject（主题）**
   - 使用祈使语：add, fix, refactor 而不是 added, fixed, refactored
   - 首字母小写
   - 不以句号结尾
   - 不超过50个字符

   ```
   ✅ feat(collection): add RSS feed parser
   ✅ fix(ai): handle timeout error gracefully
   ✅ refactor(database): optimize query performance
   ❌ feat(collection): Add RSS feed parser (首字母大写)
   ❌ fix(ai): handle timeout error. (句号)
   ❌ feat(collection): add RSS feed parser that supports both RSS 2.0 and Atom formats (太长)
   ```

5. **Body（正文，可选）**
   - 解释 "为什么" 而不是 "是什么"
   - 每行不超过72个字符
   - 用空行分隔段落

   ```
   feat(ai): add exponential backoff retry logic

   The AI service sometimes times out when processing large documents.
   Previous implementation would fail immediately on timeout.

   This change adds exponential backoff retry with max 3 attempts.
   Each retry waits 2^attempt seconds before retrying.

   Fixes #123
   Related-To: #456
   ```

6. **Footer（页脚，可选）**
   - 关闭 Issue：Closes #123, Fixes #456
   - 引用相关 Issue：Related-To #789
   - Breaking Changes：BREAKING CHANGE: description

   ```
   ✅ Closes #123
   ✅ Fixes #456
   ✅ Related-To #789
   ✅ BREAKING CHANGE: API endpoint /api/v1/old-endpoint removed
   ```

### 完整的提交信息示例

```
feat(collection): add RSS feed parser support

Implement RSS 2.0 and Atom feed parsing capabilities.
The collector can now fetch content from RSS feeds in addition to web scraping.

Changes:
- Parse RSS feeds using feedparser library
- Validate feed URLs and handle errors gracefully
- Support both RSS 2.0 and Atom 1.0 formats
- Add feed item deduplication based on GUID

Closes #123
Related-To #456
```

```
fix(ai): handle timeout error in content processing

The AI service sometimes times out when processing large documents.
This change adds exponential backoff retry logic to improve reliability.

- Add exponential backoff retry (max 3 attempts)
- Log retry attempts with duration
- Fail gracefully after max retries
- Add unit tests for retry logic

Fixes #789
```

```
refactor(database): optimize content query performance

- Add composite index on (status, created_at)
- Use pagination to avoid loading large datasets
- Reduce query count using eager loading
- Performance improvement: ~40% faster on large datasets

Performance test results:
- Before: avg 5.2s for 1M records
- After: avg 3.1s for 1M records
```

### 🟡 SHOULD - 强烈建议

1. **一个提交对应一个逻辑改动**
   ```
   ✅ commit 1: feat(api): add new endpoint
      commit 2: test(api): add tests for new endpoint
      commit 3: docs: update API documentation

   ❌ commit 1: feat(api): add endpoint, fix bug, update docs (太多不相关改动)
   ```

2. **提交信息长度**
   ```
   Subject: < 50字符
   Body: 每行 < 72字符
   ```

3. **提交前检查**
   ```bash
   git status          # 查看未暂存的改动
   git diff            # 查看具体改动
   git diff --staged   # 查看将被提交的改动
   ```

---

## Pull Request 流程

### 🔴 MUST - 严格遵守

1. **创建 PR 前**
   ```bash
   # 1. 更新本地develop
   git checkout develop
   git pull origin develop

   # 2. 从develop创建feature分支
   git checkout -b feature/001-add-feature

   # 3. 实现功能，编写测试
   # ... 开发代码 ...

   # 4. 提交代码
   git commit -m "feat(module): add feature"

   # 5. 推送到远程
   git push origin feature/001-add-feature
   ```

2. **PR 标题清晰**
   ```
   ✅ [FEATURE] Add RSS feed parser support
   ✅ [BUGFIX] Fix timeout error in AI processing
   ✅ [REFACTOR] Optimize database queries
   ✅ [DOCS] Update API documentation

   ❌ Update stuff
   ❌ Fix things
   ❌ WIP
   ```

3. **PR 描述完整**
   ```markdown
   ## Description
   清晰的功能/修复描述

   ## Related Issues
   Closes #123
   Related-To #456

   ## Changes
   - 改动1
   - 改动2
   - 改动3

   ## How to Test
   1. 步骤1
   2. 步骤2
   3. 验证结果

   ## Screenshots (if applicable)
   截图

   ## Breaking Changes (if any)
   是否有破坏性改动
   ```

4. **PR 检查清单**
   ```
   - [ ] 代码遵循编码规范
   - [ ] 所有新代码都有测试
   - [ ] 测试覆盖率 > 85%
   - [ ] 所有测试通过
   - [ ] 没有 TODO/FIXME 未解决
   - [ ] 文档已更新
   - [ ] 提交信息遵循规范
   - [ ] 分支从 develop 创建
   - [ ] 分支是最新的（与develop同步）
   ```

5. **Code Review 要求**
   ```
   ✅ 至少1个reviewer审核
   ✅ 所有评论都已解决
   ✅ 所有自动检查通过
   ✅ 无冲突且可以合并
   ```

6. **合并 PR**
   ```bash
   # 确保分支最新
   git checkout feature/001-add-feature
   git pull origin develop  # 如果有冲突，解决冲突
   git push origin feature/001-add-feature

   # 通过 GitHub UI 合并 PR
   # 选择 "Squash and merge" 或 "Create a merge commit"
   # 不允许 "Rebase and merge"
   ```

7. **合并后清理**
   ```bash
   # 删除远程分支
   git push origin -d feature/001-add-feature

   # 删除本地分支
   git branch -d feature/001-add-feature
   ```

### 🟡 SHOULD - 强烈建议

1. **及时更新 PR**
   ```bash
   # 如果develop有新提交，更新PR
   git pull origin develop
   git push origin feature/001-add-feature
   ```

2. **保持 PR 相对较小**
   ```
   理想：100-300行改动
   最大：500行改动
   如果超过500行，考虑拆分成多个PR
   ```

---

## 冲突处理

### 🔴 MUST - 严格遵守

1. **解决冲突步骤**
   ```bash
   # 1. 更新本地分支
   git pull origin develop

   # 2. 如果有冲突，编辑冲突文件
   # 删除冲突标记 <<<<<<<, =======, >>>>>>>
   # 保留需要的代码

   # 3. 标记冲突为已解决
   git add <conflicted-file>

   # 4. 提交合并提交
   git commit -m "Merge: resolve conflicts with develop"

   # 5. 推送
   git push origin feature/001-add-feature
   ```

2. **不允许的操作**
   ```
   ❌ git push --force    (强制推送，会丢失历史)
   ❌ git rebase develop  (变基，改写历史)
   ❌ git merge --no-ff    (允许，但要清晰的目的)
   ```

---

## 本地开发工作流

### 🔴 MUST - 严格遵守

1. **日常开发流程**
   ```bash
   # 创建分支
   git checkout develop
   git pull origin develop
   git checkout -b feature/001-add-feature

   # 开发和提交
   # ... 编写代码 ...
   git add src/module.py
   git commit -m "feat(module): add feature"

   # 编写测试
   # ... 编写测试 ...
   git add tests/unit/test_module.py
   git commit -m "test(module): add tests"

   # 可能的重构
   # ... 重构代码 ...
   git commit -m "refactor(module): improve code structure"

   # 推送
   git push origin feature/001-add-feature

   # 创建 PR
   ```

2. **提交前检查**
   ```bash
   # 1. 检查代码格式
   black src/ tests/

   # 2. 检查代码风格
   flake8 src/ tests/

   # 3. 类型检查
   mypy src/

   # 4. 运行测试
   pytest --cov=src --cov-fail-under=85

   # 5. 验证提交信息格式
   bash .claude/tools/validate-commit.sh
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 Git Hooks**
   ```bash
   # 安装 pre-commit hooks
   bash .claude/hooks/install-hooks.sh

   # Hooks会自动：
   # - 格式化代码 (black)
   # - 检查风格 (flake8)
   # - 类型检查 (mypy)
   # - 验证提交信息
   ```

2. **定期同步develop**
   ```bash
   # 如果长时间没合并，定期同步develop
   git pull origin develop
   ```

---

## 版本发布流程

### 🔴 MUST - 严格遵守

1. **从 develop 创建发布分支**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/v1.0.0
   ```

2. **更新版本号和 CHANGELOG**
   ```bash
   # 更新 src/__version__.py 或 setup.py
   version = "1.0.0"

   # 更新 CHANGELOG.md
   # 文档发布内容、功能、修复等
   ```

3. **发布到 main**
   ```bash
   git checkout main
   git pull origin main
   git merge --no-ff release/v1.0.0 -m "Release: v1.0.0"
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin main
   git push origin v1.0.0
   ```

4. **同步回 develop**
   ```bash
   git checkout develop
   git merge --no-ff release/v1.0.0 -m "Merge release v1.0.0 into develop"
   git push origin develop
   ```

5. **删除发布分支**
   ```bash
   git branch -d release/v1.0.0
   git push origin -d release/v1.0.0
   ```

---

## Git 配置

### 🔴 MUST - 严格遵守

1. **配置用户信息**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **配置默认编辑器**
   ```bash
   git config --global core.editor "vim"
   ```

3. **配置自动换行处理**
   ```bash
   git config --global core.safecrlf true
   ```

---

## Git 命令速查

```bash
# 查看分支
git branch                    # 本地分支
git branch -a                 # 所有分支
git branch -v                 # 带SHA的分支信息

# 创建和切换分支
git checkout -b feature/001   # 创建并切换
git switch feature/001        # 切换（现代方法）

# 查看日志
git log                       # 查看提交历史
git log --oneline             # 单行显示
git log --graph --all         # 可视化分支
git log -p                    # 显示具体改动

# 查看改动
git status                    # 工作树状态
git diff                      # 未暂存的改动
git diff --staged             # 已暂存的改动

# 提交
git add .                     # 暂存所有改动
git commit -m "message"       # 提交
git commit --amend            # 修改最后一次提交

# 推送和拉取
git push origin branch-name   # 推送分支
git pull origin develop       # 拉取并合并
git fetch origin              # 仅获取，不合并

# 合并和冲突
git merge develop             # 合并分支
git merge --abort             # 中止合并
git rebase develop            # 变基（一般不用）

# 撤销操作
git reset HEAD~1              # 撤销最后一次提交
git revert HEAD               # 创建新提交来撤销
git checkout -- file.py       # 丢弃文件改动

# 标签
git tag v1.0.0                # 创建轻量级标签
git tag -a v1.0.0 -m "msg"    # 创建注解标签
git push origin v1.0.0        # 推送标签
```

---

**记住：** Git历史是项目的叙事。好的提交信息和清晰的分支策略让整个项目易于理解和维护。

