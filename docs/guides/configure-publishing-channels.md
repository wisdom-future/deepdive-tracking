# 发布渠道配置指南

本指南说明如何配置 Email、GitHub 和 WeChat 发布渠道，以便优先级发布工作流能够正常运行。

## Email 配置

### 1. 获取 Gmail App Password

如果使用 Gmail：

1. 访问 [Google Account Security](https://myaccount.google.com/security)
2. 启用 "2-Step Verification"（两步验证）
3. 在 "App passwords" 中生成一个应用专用密码
4. 复制生成的密码

### 2. 配置环境变量

在 `.env` 文件中配置以下变量：

```bash
# Email (SMTP) Configuration
SMTP_HOST=smtp.gmail.com          # Gmail SMTP 服务器
SMTP_PORT=587                      # SMTP 端口 (TLS)
SMTP_USER=your_email@gmail.com     # 你的 Gmail 邮箱地址
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 生成的应用专用密码
SMTP_FROM_EMAIL=your_email@gmail.com  # 发送者邮箱
SMTP_FROM_NAME=DeepDive Tracking   # 发送者名称
EMAIL_LIST=["recipient@example.com","another@example.com"]  # 收件人列表
```

### 3. 测试 Email 配置

运行以下命令测试邮箱配置：

```bash
python -c "
from src.services.channels.email import EmailPublisher
from src.config import get_settings

settings = get_settings()
publisher = EmailPublisher(
    smtp_host=settings.smtp_host,
    smtp_port=settings.smtp_port,
    smtp_user=settings.smtp_user,
    smtp_password=settings.smtp_password,
    from_email=settings.smtp_from_email,
    email_list=settings.email_list
)
print('✓ Email 配置正确')
"
```

## GitHub 配置

### 1. 生成 GitHub Token

1. 访问 [GitHub Settings - Personal Access Tokens](https://github.com/settings/tokens)
2. 点击 "Generate new token"
3. 选择 "Generate new token (classic)"
4. 设置权限：
   - ✓ `public_repo` - 访问公开仓库
   - ✓ `repo` - 访问私有仓库（如果使用）
5. 复制生成的 Token

### 2. 准备 GitHub 仓库

创建一个专门用于发布内容的仓库：

```bash
# 在你的 GitHub 上创建一个仓库：
# https://github.com/your_username/deepdive-tracking

# 然后本地克隆：
git clone https://github.com/your_username/deepdive-tracking.git ./github_repo
cd ./github_repo
git config user.name "DeepDive Bot"
git config user.email "deepdive@example.com"
```

### 3. 配置环境变量

在 `.env` 文件中配置以下变量：

```bash
# GitHub Configuration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 生成的 Token
GITHUB_REPO=your_username/deepdive-tracking            # 仓库标识
GITHUB_USERNAME=your_username                          # GitHub 用户名
GITHUB_LOCAL_PATH=./github_repo                        # 本地仓库路径
```

### 4. 测试 GitHub 配置

运行以下命令测试 GitHub 配置：

```bash
python -c "
from src.services.channels.github import GitHubPublisher
from src.config import get_settings

settings = get_settings()
publisher = GitHubPublisher(
    github_token=settings.github_token,
    github_repo=settings.github_repo,
    github_username=settings.github_username,
    local_repo_path=settings.github_local_path
)
print('✓ GitHub 配置正确')
"
```

## WeChat 配置

### 1. 获取 WeChat 公众号凭证

1. 在 [WeChat Official Platform](https://mp.weixin.qq.com/) 注册公众号
2. 访问 "Settings" → "Basic Information"
3. 记录以下信息：
   - `AppID` (应用 ID)
   - `AppSecret` (应用密钥)

### 2. 配置环境变量

在 `.env` 文件中配置以下变量：

```bash
# WeChat Configuration
WECHAT_API_URL=https://api.weixin.qq.com      # WeChat API 服务器
WECHAT_APP_ID=wxc3d4bc2d698da563             # 你的 AppID
WECHAT_APP_SECRET=e9f5d2a2b2ffe5bc4e23c9904c0021b6  # 你的 AppSecret
```

### 3. 测试 WeChat 配置

运行以下命令测试 WeChat 配置：

```bash
python -c "
from src.services.channels.wechat import WeChatPublisher
from src.config import get_settings

settings = get_settings()
publisher = WeChatPublisher(
    app_id=settings.wechat_app_id,
    app_secret=settings.wechat_app_secret
)
print('✓ WeChat 配置正确')
"
```

## 完整的 .env 配置示例

```bash
# Application Settings
APP_NAME=DeepDive Tracking
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./data/db/deepdive_tracking.db

# External APIs - OpenAI
OPENAI_API_KEY=sk-proj-your_openai_key

# Publishing Channels - Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=DeepDive Tracking
EMAIL_LIST=["admin@example.com"]

# Publishing Channels - GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=your_username/deepdive-tracking
GITHUB_USERNAME=your_username
GITHUB_LOCAL_PATH=./github_repo

# Publishing Channels - WeChat Official Account
WECHAT_API_URL=https://api.weixin.qq.com
WECHAT_APP_ID=wxc3d4bc2d698da563
WECHAT_APP_SECRET=e9f5d2a2b2ffe5bc4e23c9904c0021b6
```

## 优先级发布执行

### 1. Dry-run 模式（推荐先测试）

```bash
# 不实际发送，只模拟发布过程
python scripts/run_priority_publishing_test.py 5 --dry-run
```

### 2. 实际发布

```bash
# 实际发布 3 篇文章
python scripts/run_priority_publishing_test.py 3

# 实际发布 10 篇文章
python scripts/run_priority_publishing_test.py 10
```

### 3. 查看优先级配置

```bash
# 查看所有配置和统计信息
python scripts/show_publish_priorities.py
```

## 常见问题

### Q: Email 发送失败，显示 "Authentication failed"

**解决方案：**
1. 确保使用的是 Gmail App Password，而不是账户密码
2. 检查两步验证是否已启用
3. 检查 .env 中的密码是否正确复制

### Q: GitHub 推送失败，显示 "Permission denied"

**解决方案：**
1. 确保 Token 有 `repo` 权限
2. 确保本地仓库已正确初始化
3. 验证仓库地址是否正确

### Q: WeChat 发送失败，显示 "Invalid credentials"

**解决方案：**
1. 确保 AppID 和 AppSecret 正确
2. 确保公众号已激活
3. 检查 API 是否已启用

### Q: 我想先测试而不实际发送？

**答：** 使用 `--dry-run` 模式：
```bash
python scripts/run_priority_publishing_test.py 3 --dry-run
```

### Q: 如何修改优先级顺序？

**答：** 修改数据库中 `publish_priorities` 表中的 `priority` 字段：

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import PublishPriority
from src.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)
session = Session()

# 修改优先级
email = session.query(PublishPriority).filter_by(channel="email").first()
github = session.query(PublishPriority).filter_by(channel="github").first()
wechat = session.query(PublishPriority).filter_by(channel="wechat").first()

email.priority = 10   # Email 最高优先级
github.priority = 9   # GitHub 次高优先级
wechat.priority = 5   # WeChat 最低优先级

session.commit()
print("优先级已更新")
```

## 安全建议

⚠️ **重要提示：**

1. **不要在代码中硬编码凭证** - 始终使用环境变量或 .env 文件
2. **不要提交 .env 文件到 Git** - .env 应该在 .gitignore 中
3. **定期轮换凭证** - 定期更改 Token 和密码
4. **使用最小权限原则** - 只授予必要的权限
5. **监控使用日志** - 定期检查发布日志

## 验证配置的完整脚本

```bash
#!/bin/bash
# 保存为 verify_config.sh

echo "验证发布渠道配置..."
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在"
    exit 1
fi

echo "检查环境变量..."

# Email
if grep -q "SMTP_HOST=" .env && grep -q "SMTP_USER=" .env && grep -q "SMTP_PASSWORD=" .env; then
    echo "✓ Email 配置完整"
else
    echo "⚠ Email 配置不完整"
fi

# GitHub
if grep -q "GITHUB_TOKEN=" .env && grep -q "GITHUB_REPO=" .env; then
    echo "✓ GitHub 配置完整"
else
    echo "⚠ GitHub 配置不完整"
fi

# WeChat
if grep -q "WECHAT_APP_ID=" .env && grep -q "WECHAT_APP_SECRET=" .env; then
    echo "✓ WeChat 配置完整"
else
    echo "⚠ WeChat 配置不完整"
fi

echo ""
echo "运行 dry-run 测试..."
python scripts/run_priority_publishing_test.py 1 --dry-run
```

## 下一步

1. ✅ 配置所有凭证
2. ✅ 运行 dry-run 测试验证配置
3. ✅ 初始化优先级配置：`python scripts/init_publish_priorities.py`
4. ✅ 执行实际发布：`python scripts/run_priority_publishing_test.py 3`
5. ✅ 检查邮箱和 GitHub 是否收到内容
6. ✅ 查看统计信息：`python scripts/show_publish_priorities.py`

