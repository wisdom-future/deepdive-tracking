# 多渠道发布 - 快速参考

## 快速命令

```bash
# 发布到所有渠道
python scripts/run_multi_channel_publishing_test.py all 5

# 仅发布到 WeChat
python scripts/run_multi_channel_publishing_test.py wechat 3

# 发布到 WeChat 和 GitHub
python scripts/run_multi_channel_publishing_test.py wechat,github 5
```

## 环境变量配置

```env
# WeChat
WECHAT_APP_ID=xxx
WECHAT_APP_SECRET=xxx

# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=username/repo
GITHUB_USERNAME=username
GITHUB_LOCAL_PATH=/tmp/repo

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=app_password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=DeepDive Tracking
EMAIL_LIST=["email1@example.com","email2@example.com"]
```

## Python 代码示例

### 多渠道发布

```python
from src.services.workflow.multi_channel_publishing_workflow import MultiChannelPublishingWorkflow
import asyncio

workflow = MultiChannelPublishingWorkflow(session)

# 配置渠道
workflow.configure_wechat(app_id, app_secret)
workflow.configure_github(token, repo, username, path)
workflow.configure_email(host, port, user, password, from_email)

# 执行发布
result = await workflow.execute(
    channels=["wechat", "github", "email"],
    article_limit=5
)
```

### 管理渠道配置

```python
from src.services.channels import ChannelManager

manager = ChannelManager(session)

# 创建 WeChat 配置
config = manager.create_wechat_config(
    app_id="xxx",
    app_secret="xxx",
    account_name="My Account"
)

# 创建 GitHub 配置
config = manager.create_github_config(
    github_token="ghp_xxx",
    github_repo="user/repo",
    github_username="user"
)

# 创建 Email 配置
config = manager.create_email_config(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="user@gmail.com",
    smtp_password="password",
    from_email="noreply@example.com"
)
```

### 管理邮件列表

```python
manager = ChannelManager(session)

# 添加邮箱
manager.add_email_to_list(config_id=1, email="new@example.com")

# 移除邮箱
manager.remove_email_from_list(config_id=1, email="old@example.com")

# 获取邮件列表
emails = manager.get_email_list(config_id=1)

# 设置邮件列表
manager.set_email_list(
    config_id=1,
    emails=["email1@example.com", "email2@example.com"]
)
```

## 数据库查询

```python
from src.models import (
    WeChatChannelConfig,
    GitHubChannelConfig,
    EmailChannelConfig
)

# 查询 WeChat 配置
wechat = session.query(WeChatChannelConfig).filter_by(is_enabled=True).first()

# 查询 GitHub 配置
github = session.query(GitHubChannelConfig).filter_by(is_enabled=True).first()

# 查询 Email 配置
email = session.query(EmailChannelConfig).filter_by(is_enabled=True).first()

# 获取统计
print(f"WeChat: {wechat.total_articles_published} 篇")
print(f"Email 列表: {email.get_email_list()}")
```

## 常见问题

| 问题 | 解决方案 |
|------|--------|
| WeChat token 过期 | 系统自动刷新，无需手动处理 |
| GitHub 克隆失败 | 检查 token 权限和网络连接 |
| Email 认证失败 | 使用应用密码而非账户密码 |
| 文章未发布 | 检查文章是否已批准（status=approved） |

## 限制和配额

| 渠道 | 限制 |
|------|------|
| WeChat | 单次最多 8 篇文章 |
| GitHub | 单个仓库无文件数限制 |
| Email | 视服务商限制（Gmail 无限） |

## 默认邮件列表

默认邮件列表：`hello.junjie.duan@gmail.com`

可以在环境变量或代码中覆盖。

## 发布流程图

```
批准文章
  ↓
多渠道工作流
  ├→ WeChat (永久素材 + 群发)
  ├→ GitHub (HTML + Git 提交)
  └→ Email (HTML 邮件)
  ↓
保存发布记录
  ↓
生成统计报告
```
