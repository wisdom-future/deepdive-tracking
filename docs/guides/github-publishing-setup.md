# GitHub Publishing Setup Guide

**目的**: 为 DeepDive Tracking 配置 GitHub 发布功能
**作者**: DeepDive Team
**最后更新**: 2025-11-02

---

## 📋 概述

本指南说明如何配置 GitHub 发布功能，使得 `send_top_ai_news_to_github.py` 脚本能够自动发布 AI 新闻到 GitHub 仓库。

### 发布流程
```
AI 新闻 (数据库)
    ↓
通过 AI 关键词过滤 (25+ 关键词)
    ↓
生成 HTML 文章页面
    ↓
创建索引页面
    ↓
提交到 GitHub 仓库
    ↓
推送到远程
```

---

## 🔑 第一步：创建 GitHub 个人访问令牌 (PAT)

### 步骤 1.1: 前往 GitHub 设置
1. 登录到 GitHub: https://github.com
2. 点击右上角头像 → **Settings**
3. 左边栏选择 **Developer settings**
4. 点击 **Personal access tokens** → **Tokens (classic)**

### 步骤 1.2: 生成新的令牌
1. 点击 **Generate new token (classic)**
2. 输入令牌名称（例如：`deepdive-tracking-bot`）
3. **Expiration** 选择 **90 days** 或 **No expiration**（推荐 90 天定期更新）

### 步骤 1.3: 选择权限范围 (Scopes)

仅选择以下必要的权限：

```
✅ repo (Full control of private repositories)
   └─ repo:status
   └─ repo_deployment
   └─ public_repo
   └─ repo:invite
   └─ security_events

✅ workflow (Update GitHub Action workflows)

✅ admin:org_hook (Manage organization hooks)
```

**最小权限方案**（推荐）：
- 仅选择 `repo` （完整仓库访问）

### 步骤 1.4: 生成和复制令牌
1. 点击 **Generate token**
2. **⚠️ 重要**: 立即复制令牌值（只显示一次！）
3. 保存在安全的地方（稍后需要）

**令牌格式**: `ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (40+ 个字符)

---

## 📁 第二步：创建 GitHub 仓库

### 步骤 2.1: 创建新仓库
1. 访问 https://github.com/new
2. **Repository name**: `ai-news-articles`（可自定义）
3. **Description**: `Auto-published AI news articles` （可选）
4. **Visibility**:
   - `Public` - 任何人都可以查看
   - `Private` - 仅你可以查看
5. **Initialize repository**:
   - ✅ Add a README file
   - ✅ Add .gitignore (选择 Python)
   - ✅ Choose a license (MIT)

### 步骤 2.2: 获取仓库信息
创建后，记下：
- **仓库完整路径**: `your-username/ai-news-articles`
- **GitHub 用户名**: `your-username`

例如：`wisdom-future/ai-news-articles`

---

## 🔧 第三步：配置 .env 文件

### 步骤 3.1: 编辑 .env 文件

打开项目根目录的 `.env` 文件，添加或更新以下配置：

```env
# GitHub 配置
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GITHUB_REPO=your-username/ai-news-articles
GITHUB_USERNAME=your-username
GITHUB_LOCAL_PATH=./github_repo

# 其他配置保持不变...
```

### 步骤 3.2: 配置详解

| 配置项 | 描述 | 例子 |
|--------|------|------|
| `GITHUB_TOKEN` | 个人访问令牌 (PAT) | `ghp_XXXXXXXXXXXXXXXXXXXXXXXX` |
| `GITHUB_REPO` | 仓库完整路径（用户名/仓库名） | `wisdom-future/ai-news-articles` |
| `GITHUB_USERNAME` | GitHub 用户名 | `wisdom-future` |
| `GITHUB_LOCAL_PATH` | 本地克隆仓库的路径 | `./github_repo` 或 `/tmp/github_repo` |

### 步骤 3.3: 验证 .env 文件

```bash
# 检查配置是否正确
cat .env | grep GITHUB_

# 输出应该显示：
# GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXX
# GITHUB_REPO=your-username/ai-news-articles
# GITHUB_USERNAME=your-username
# GITHUB_LOCAL_PATH=./github_repo
```

---

## 🧪 第四步：测试 GitHub 发布

### 步骤 4.1: 运行验证脚本

```bash
# 验证 GitHub 配置
python scripts/publish/send_top_ai_news_to_github.py

# 预期输出：
# ===============================================================================
# TOP AI NEWS TO GITHUB - Publishing AI Articles
# ===============================================================================
#
# 1. Checking GitHub configuration...
# [OK] GitHub configured
#     Repo: your-username/ai-news-articles
#     Username: your-username
#
# 2. Initializing GitHub Publisher...
# [OK] GitHub publisher initialized successfully
#
# 3. Fetching and filtering AI-related news...
# [OK] Found 10 AI-related news items (out of 18 total)
#     1. Article Title One (Score: 95)
#     2. Article Title Two (Score: 92)
#     ...
#
# 4. Publishing TOP AI News to GitHub...
# [OK] GitHub publishing configuration verified
#     Ready to publish 10 articles
#
# ===============================================================================
# TOP AI NEWS TO GITHUB READY!
# ===============================================================================
```

### 步骤 4.2: 检查发布结果

如果脚本成功运行，检查你的 GitHub 仓库：

1. 访问 https://github.com/your-username/ai-news-articles
2. 应该看到：
   - `index.html` - 所有 AI 新闻的索引页面
   - `articles/` 文件夹 - 包含每篇文章的 HTML 文件
   - 自动提交的历史记录

### 步骤 4.3: 故障排查

**问题 1: 令牌无效**
```
Error: Bad credentials
```
**解决方案**:
- 检查 `GITHUB_TOKEN` 是否正确复制
- 确认令牌没有过期
- 重新生成新的令牌

**问题 2: 仓库不存在**
```
Error: Repository not found
```
**解决方案**:
- 检查 `GITHUB_REPO` 格式是否正确（应该是 `username/repo-name`）
- 确认仓库确实存在于你的 GitHub 账户

**问题 3: 权限不足**
```
Error: Resource not accessible by integration
```
**解决方案**:
- 确认令牌有 `repo` 权限范围
- 如果仓库是私有的，确认令牌有访问权限

**问题 4: 找不到 AI 新闻**
```
No AI-related news found in the database
```
**解决方案**:
- 先运行新闻采集: `python scripts/collection/collect_news.py`
- 然后评分新闻: `python scripts/evaluation/score_collected_news.py`
- 再运行发布脚本

---

## 🚀 第五步：自动化发布 (可选)

### 选项 A: 使用 Cron Job (Linux/Mac)

编辑 crontab：
```bash
crontab -e
```

添加定时任务（每天凌晨 1 点）：
```bash
0 1 * * * cd /path/to/deepdive-tracking && python scripts/publish/send_top_ai_news_to_github.py
```

### 选项 B: 使用 Windows 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 名称: `DeepDive GitHub Publishing`
4. 触发器: 每日凌晨 1 点
5. 操作: 运行程序
   - 程序: `python`
   - 参数: `scripts/publish/send_top_ai_news_to_github.py`
   - 开始于: `/path/to/deepdive-tracking`

### 选项 C: 使用 GitHub Actions (推荐)

在主仓库创建 `.github/workflows/publish-to-github.yml`：

```yaml
name: Publish AI News to GitHub

on:
  schedule:
    - cron: '0 1 * * *'  # 每天凌晨 1 点 UTC
  workflow_dispatch:      # 支持手动触发

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Publish to GitHub
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO: ${{ secrets.GITHUB_REPO }}
          GITHUB_USERNAME: ${{ secrets.GITHUB_USERNAME }}
        run: python scripts/publish/send_top_ai_news_to_github.py
```

---

## 📊 监控和维护

### 监控发布状态
```bash
# 查看最近的发布
git log --oneline | grep "Auto-published" | head -10

# 检查发布文件统计
find github_repo/articles -name "*.html" | wc -l
```

### 定期更新令牌

由于安全考虑，建议每 90 天更新一次令牌：

1. 生成新令牌（按照第一步）
2. 更新 `.env` 文件
3. 删除旧令牌（在 GitHub 设置中）

### 清理旧文章 (可选)

如果要定期清理旧文章，可以在发布脚本中添加：

```python
# 删除超过 30 天的文章
import os
from datetime import datetime, timedelta

articles_dir = 'github_repo/articles'
cutoff_date = datetime.now() - timedelta(days=30)

for filename in os.listdir(articles_dir):
    filepath = os.path.join(articles_dir, filename)
    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
    if mtime < cutoff_date:
        os.remove(filepath)
```

---

## 🔐 安全最佳实践

### ✅ 推荐做法

1. **使用环境变量**: 不要在代码中硬编码令牌
2. **定期轮换令牌**: 每 90 天更新一次
3. **限制权限**: 只授予必要的权限范围
4. **分别的仓库**: 使用专用仓库存储发布的新闻
5. **监控日志**: 定期检查发布日志和错误

### ❌ 不要做的事

- ❌ 将令牌提交到 Git
- ❌ 在公开的地方分享令牌
- ❌ 使用超级权限令牌
- ❌ 永久有效的令牌

---

## 📞 常见问题 (FAQ)

### Q: 可以用同一个令牌发布到多个仓库吗？
**A:** 可以，只需更改 `GITHUB_REPO` 配置即可。

### Q: 发布失败了会发生什么？
**A:** 脚本会在日志中记录错误并返回失败状态。建议设置邮件告警。

### Q: 如何看到所有发布的历史？
**A:** 访问仓库的 Commits 选项卡，查看所有自动提交。

### Q: 可以自定义 HTML 模板吗？
**A:** 可以，修改 `src/services/channels/github/github_publisher.py` 中的模板。

### Q: 发布的新闻可以删除吗？
**A:** 可以，在仓库中手动删除文件，然后提交删除操作。

---

## 📚 相关文件

- 发布脚本: `scripts/publish/send_top_ai_news_to_github.py`
- GitHub 发布器: `src/services/channels/github/github_publisher.py`
- 脚本结构文档: `scripts/scripts-structure.md`
- 邮件发布指南: `docs/guides/email-publishing-setup.md`

---

## 🎯 下一步

完成配置后，您可以：

1. **测试发布**: 运行发布脚本确认工作正常
2. **设置自动化**: 配置定时任务或 GitHub Actions
3. **监控性能**: 定期检查发布日志
4. **优化模板**: 根据需要自定义 HTML 样式

---

**需要帮助?** 检查脚本输出的错误信息或查看故障排查部分。

**最后更新**: 2025-11-02
