# 多渠道发布系统 - 完整指南

## 概览

DeepDive Tracking 现在支持将文章同时发布到多个渠道：

- **WeChat (微信)**: 使用永久素材 API + 群发接口，支持批量发布
- **GitHub**: 生成美观的 HTML 页面并提交到 GitHub 仓库
- **Email**: 发送 HTML 格式邮件到邮件列表

## 系统架构

```
多渠道发布工作流
    ├── 获取已批准文章
    ├── 调用各渠道发布器
    │   ├── WeChat Publisher
    │   ├── GitHub Publisher
    │   └── Email Publisher
    ├── 保存发布记录
    └── 生成发布统计
```

## 快速开始

### 1. 环境配置

在 `.env` 文件中配置各渠道的凭证：

```env
# WeChat
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# GitHub
GITHUB_TOKEN=your_personal_access_token
GITHUB_REPO=username/repo
GITHUB_USERNAME=your_username
GITHUB_LOCAL_PATH=/path/to/local/repo

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_email_password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_FROM_NAME=DeepDive Tracking
EMAIL_LIST=["hello.junjie.duan@gmail.com", "other@example.com"]
```

### 2. 运行多渠道发布测试

```bash
# 发布到所有已配置的渠道
python scripts/run_multi_channel_publishing_test.py all 5

# 仅发布到 WeChat
python scripts/run_multi_channel_publishing_test.py wechat 3

# 发布到 WeChat 和 GitHub
python scripts/run_multi_channel_publishing_test.py wechat,github 5

# 发布到所有渠道，处理 10 篇文章
python scripts/run_multi_channel_publishing_test.py all 10
```

## 渠道详细配置

### WeChat 微信

#### 配置要求

1. **获取凭证**
   - 登录 WeChat Official Account 后台
   - 进入"设置 > 基本设置"
   - 获取 App ID 和 App Secret

2. **启用永久素材 API**
   - 确保公众号已认证
   - 检查接口权限

#### WeChat 配置示例

```python
from src.services.channels import WeChatPublisher

publisher = WeChatPublisher(
    app_id="your_app_id",
    app_secret="your_app_secret"
)

# 单篇发布
result = await publisher.publish_article(
    title="文章标题",
    content="文章内容",
    summary="摘要",
    author="作者",
    source_url="https://example.com",
    score=85,
    category="AI"
)

# 批量发布
result = await publisher.publish_batch_articles(
    articles=[...],
    is_to_all=True  # 发送给所有粉丝
)
```

#### WeChat 发布流程

1. 上传图文消息到永久素材库
2. 使用群发接口发送消息
3. 记录消息 ID 和 Media ID

#### 限制说明

- 单次群发最多 **8 篇文章**
- 群发频率有限制（取决于粉丝数）
- 图文内容有审核要求

---

### GitHub

#### 配置要求

1. **获取个人访问令牌**
   - 登录 GitHub 账户
   - 进入 Settings > Developer settings > Personal access tokens
   - 创建新令牌，选择权限：`repo`（完整控制私有仓库）

2. **创建或使用现有仓库**
   - 可以是公开或私有仓库
   - 建议创建专用仓库用于发布

#### GitHub 配置示例

```python
from src.services.channels import GitHubPublisher

publisher = GitHubPublisher(
    github_token="ghp_xxxxx",
    github_repo="username/deepdive-articles",
    github_username="your_username",
    local_repo_path="/tmp/deepdive-github"
)

# 发布单篇文章
result = await publisher.publish_article(
    title="文章标题",
    content="<h2>HTML 内容</h2>",
    summary="摘要",
    author="作者",
    source_url="https://example.com",
    score=75,
    category="Machine Learning"
)

# 批量发布
result = await publisher.publish_batch_articles(
    articles=[...],
    batch_name="20250101"  # 批次名称，用于索引
)
```

#### GitHub 发布流程

1. 克隆仓库到本地
2. 生成美化的 HTML 页面
3. 创建文章索引页面
4. 自动 Git 提交和推送
5. 生成原始文件 URL

#### HTML 输出特性

- 响应式设计（支持移动设备）
- 漂亮的渐变背景（紫色系）
- 文章评分星级显示
- 元数据卡片（作者、分类、发布时间）
- 自动生成批次索引
- 每篇文章生成独立 HTML 页面

---

### Email 邮件

#### 配置要求

1. **选择邮件服务**
   - Gmail: `smtp.gmail.com:587`（需要应用密码）
   - 企业邮箱: 根据供应商配置
   - 自建邮件服务器

2. **获取凭证**
   - SMTP 服务器地址和端口
   - 用户名和密码
   - 发件人邮箱和名称

#### Email 配置示例

```python
from src.services.channels import EmailPublisher

publisher = EmailPublisher(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your_email@gmail.com",
    smtp_password="your_app_password",
    from_email="noreply@example.com",
    from_name="DeepDive Tracking",
    email_list=["user1@example.com", "user2@example.com"]
)

# 发送单篇文章
result = await publisher.publish_article(
    title="文章标题",
    content="<h2>HTML 内容</h2>",
    summary="摘要",
    author="作者",
    source_url="https://example.com",
    score=80,
    category="AI",
    email_list=["recipient@example.com"]  # 可选，覆盖默认列表
)

# 批量发送汇总邮件
result = await publisher.publish_batch_articles(
    articles=[...],
    batch_name="2025-01-01"
)
```

#### 邮件列表管理

```python
publisher = EmailPublisher(...)

# 添加邮箱
publisher.add_email("new_user@example.com")

# 移除邮箱
publisher.remove_email("old_user@example.com")

# 获取邮件列表
emails = publisher.get_email_list()

# 设置邮件列表
publisher.set_email_list(["email1@example.com", "email2@example.com"])
```

#### 邮件格式特性

- HTML 响应式设计
- 内嵌样式（不依赖外部 CSS）
- 文章元数据展示
- 评分星级表示
- 点击按钮直达原文
- 移动设备优化

---

## 渠道配置管理

### 使用 ChannelManager

```python
from src.services.channels import ChannelManager
from sqlalchemy.orm import Session

manager = ChannelManager(session)

# 获取所有启用的渠道
enabled = manager.get_enabled_channels()

# 获取特定渠道状态
status = manager.get_channel_status("wechat")

# 启用/禁用渠道
manager.enable_channel("github")
manager.disable_channel("email")

# 管理邮件列表
manager.add_email_to_list(config_id=1, email="new@example.com")
manager.remove_email_from_list(config_id=1, email="old@example.com")
manager.set_email_list(config_id=1, emails=["email1@example.com", "email2@example.com"])

# 获取统计信息
stats = manager.get_channel_stats("email")
all_stats = manager.get_all_stats()
```

### 数据库模型

#### ChannelConfig（通用渠道配置）
```python
{
    id: int,
    channel_type: str,  # wechat, github, email
    channel_name: str,
    description: str,
    config: dict,  # 渠道特定的配置
    is_enabled: bool,
    is_configured: bool,
    total_published: int,
    total_failed: int,
    last_publish_at: datetime,
    created_at: datetime,
    updated_at: datetime
}
```

#### WeChatChannelConfig
```python
{
    app_id: str,
    app_secret: str,
    account_name: str,
    publish_style: str,  # batch or single
    max_batch_size: int,
    auto_publish: bool,
    total_articles_published: int,
    total_articles_failed: int,
    last_publish_at: datetime
}
```

#### GitHubChannelConfig
```python
{
    github_token: str,
    github_repo: str,
    github_username: str,
    local_repo_path: str,
    auto_commit: bool,
    auto_push: bool,
    create_index: bool,
    total_articles_published: int,
    total_articles_failed: int,
    last_publish_at: datetime
}
```

#### EmailChannelConfig
```python
{
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_email: str,
    from_name: str,
    email_list: list,  # JSON 格式
    send_digest: bool,
    send_individual: bool,
    digest_schedule: str,  # daily, weekly
    total_emails_sent: int,
    total_emails_failed: int,
    last_send_at: datetime
}
```

---

## 多渠道工作流

### 工作流步骤

```python
from src.services.workflow.multi_channel_publishing_workflow import MultiChannelPublishingWorkflow

workflow = MultiChannelPublishingWorkflow(session)

# 配置渠道
workflow.configure_wechat(app_id, app_secret)
workflow.configure_github(token, repo, username, local_path)
workflow.configure_email(smtp_host, smtp_port, smtp_user, smtp_password, from_email)

# 执行发布
result = await workflow.execute(
    channels=["wechat", "github", "email"],
    batch_size=5,
    article_limit=10
)

# 检查结果
if result["success"]:
    print(f"已发布到: {result['summary']['published_channels']}")
    print(f"WeChat: {result['wechat']['published_count']} 篇")
    print(f"GitHub: {result['github']['published_count']} 篇")
    print(f"Email: {result['email']['sent_emails']} 个邮箱")
```

### 返回结果格式

```python
{
    "success": bool,
    "wechat": {
        "success": bool,
        "published_count": int,
        "failed_count": int,
        "published_articles": [str],
        "failed_articles": [str]
    },
    "github": {
        "success": bool,
        "published_count": int,
        "failed_count": int,
        "batch_url": str
    },
    "email": {
        "success": bool,
        "sent_emails": int,
        "failed_emails": [str]
    },
    "summary": {
        "total_articles": int,
        "published_channels": [str]
    }
}
```

---

## 最佳实践

### 1. 错误处理

```python
try:
    result = await workflow.execute(channels=["wechat", "github"])
except Exception as e:
    logger.error(f"发布失败: {str(e)}")
    # 实现重试逻辑
```

### 2. 邮件列表管理

- 定期更新邮件列表
- 实现订阅/取消订阅功能
- 处理退信地址

### 3. GitHub 仓库管理

- 定期清理旧文件
- 维护索引页面更新
- 使用 release 标记里程碑

### 4. 限流和限制

```python
# WeChat
max_batch_size = 8  # 单次群发最多 8 篇

# GitHub
batch_size = 3  # 每批处理 3 篇，避免单次提交过大

# Email
max_recipients = 100  # 视邮件服务商限制
```

---

## 故障排查

### WeChat 发布失败

**常见原因：**
- Token 过期：需要重新获取
- 权限不足：检查公众号认证状态
- 内容不合规：内容含有敏感词

**解决方案：**
```python
# 检查 token 有效性
token_result = await publisher._get_access_token()

# 验证权限
material_count = await publisher.material_manager.get_material_count()
```

### GitHub 推送失败

**常见原因：**
- Token 权限不足：需要 `repo` 权限
- 网络问题：Git 通信超时
- 分支不存在：默认分支不是 `main`

**解决方案：**
```bash
# 验证 Git 配置
git config --list

# 检查远程仓库
git remote -v

# 手动测试推送
git push -u origin main
```

### Email 发送失败

**常见原因：**
- SMTP 认证失败：用户名/密码错误
- 端口错误：Gmail 使用 587，不是 465
- 应用密码：Gmail 需要应用专用密码，不是账户密码

**解决方案：**
```python
# 测试 SMTP 连接
import smtplib
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("email@gmail.com", "app_password")
```

---

## 监控和统计

### 获取发布统计

```python
from src.services.channels import ChannelManager

manager = ChannelManager(session)

# 获取各渠道统计
wechat_stats = manager.get_channel_stats("wechat")
github_stats = manager.get_channel_stats("github")
email_stats = manager.get_channel_stats("email")

# 显示统计
print(f"WeChat: {wechat_stats['total_published']} 篇")
print(f"GitHub: {github_stats['total_published']} 篇")
print(f"Email: {email_stats['total_sent']} 个邮箱")
```

### 发布日志

发布操作会生成详细日志，查看 logs/ 目录：
```
logs/
├── deepdive.log          # 主应用日志
├── wechat.log           # WeChat 相关日志
├── github.log           # GitHub 相关日志
└── email.log            # Email 相关日志
```

---

## API 端点（计划中）

### 管理渠道配置
```
GET    /api/v1/channels              # 获取所有渠道配置
POST   /api/v1/channels              # 创建新渠道配置
GET    /api/v1/channels/{type}       # 获取特定渠道配置
PUT    /api/v1/channels/{type}       # 更新渠道配置
DELETE /api/v1/channels/{type}       # 删除渠道配置
```

### 管理邮件列表
```
GET    /api/v1/channels/email/list   # 获取邮件列表
POST   /api/v1/channels/email/list   # 添加邮箱
DELETE /api/v1/channels/email/list   # 移除邮箱
```

### 发布操作
```
POST   /api/v1/publish               # 执行多渠道发布
GET    /api/v1/publish/history       # 获取发布历史
GET    /api/v1/publish/stats         # 获取发布统计
```

---

## 总结

多渠道发布系统提供了：

✅ **灵活的渠道支持** - 轻松添加新渠道
✅ **统一的管理界面** - ChannelManager 统一管理
✅ **数据库持久化** - 所有配置保存到数据库
✅ **完整的错误处理** - 单个渠道失败不影响其他渠道
✅ **详细的统计信息** - 追踪每个渠道的发布情况
✅ **美观的内容展示** - 每个渠道都有优化的展示形式

通过合理配置和使用，可以实现文章的一次发布、多处分发！
