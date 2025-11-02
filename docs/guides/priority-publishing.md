# 优先级发布系统指南

## 概述

优先级发布系统允许按照配置的优先级顺序，将已批准的文章依次发布到多个渠道（Email、GitHub、WeChat）。每个渠道有独立的配置和过滤规则。

**发布优先级顺序（默认）：**
1. 📧 **Email** - 优先级 10（最高）
2. 🐙 **GitHub** - 优先级 9
3. 💬 **WeChat** - 优先级 8（最低）

## 核心概念

### 优先级发布流程

```
已批准的文章
    ↓
加载优先级配置 (按优先级排序)
    ↓
按优先级逐个发布到渠道
    ├─ Email (优先级 10) - 第一个发布
    │   ├─ 检查是否启用
    │   ├─ 检查发布时间
    │   ├─ 过滤文章 (评分、分类、关键词)
    │   └─ 发布并保存记录
    ├─ GitHub (优先级 9) - 第二个发布
    │   └─ ... (同上)
    └─ WeChat (优先级 8) - 第三个发布
        └─ ... (同上)
    ↓
返回发布结果统计
```

### PublishPriority 模型

存储在 `publish_priorities` 表中，每个发布渠道一条记录。

**关键字段：**

```python
channel: str                    # 渠道标识 (email/github/wechat)
channel_name: str              # 显示名称
priority: int                  # 优先级 (1-10, 越高越先发布)
is_enabled: bool               # 是否启用
auto_publish: bool             # 是否自动发布

# 发布策略
batch_size: int                # 单次批量发布的文章数
max_retries: int               # 最大重试次数
retry_delay_minutes: int       # 重试延迟 (分钟)

# 时间控制
publish_time_start: str        # 发布开始时间 (HH:MM)
publish_time_end: str          # 发布结束时间 (HH:MM)
publish_on_weekends: bool      # 是否在周末发布

# 限流配置
max_per_day: int               # 每天最多发布数 (None=无限)
max_per_hour: int              # 每小时最多发布数 (None=无限)

# 内容过滤
min_score: int                 # 最低评分阈值
allowed_categories: list       # 允许的分类 (None=全部)
blocked_keywords: list         # 阻止的关键词

# 渠道特定配置
channel_config: dict           # 渠道特定的配置 (JSON)

# 统计信息
total_published: int           # 总发布数
total_failed: int              # 总失败数
last_publish_at: datetime      # 最后发布时间
```

## 初始化

### 1. 创建数据库表

优先级配置表会自动创建。如果需要手动创建：

```bash
# 数据库迁移
python -m alembic upgrade head
```

### 2. 初始化默认配置

```bash
# 初始化默认优先级配置
python scripts/init_publish_priorities.py
```

这将创建三个默认的优先级配置：

| 渠道 | 优先级 | 状态 | 最低评分 | 描述 |
|------|--------|------|---------|------|
| Email | 10 | ✅ 启用 | 30 | 最高优先级，第一个发布 |
| GitHub | 9 | ✅ 启用 | 25 | 次高优先级，第二个发布 |
| WeChat | 8 | ✅ 启用 | 40 | 最低优先级，第三个发布 |

## 查看配置

### 查看所有优先级配置

```bash
python scripts/show_publish_priorities.py
```

输出示例：

```
================================================================================
发布优先级配置
================================================================================

[1] EMAIL - 优先级 10/10
    状态: ✅ 启用 (自动发布)
    描述: Email 优先级最高，第一个发布渠道

    📊 发布统计:
       • 总成功: 45 篇
       • 总失败: 2 篇
       • 最后发布时间: 2025-11-02 15:30:45
       • 成功率: 95.7%

    ⚙️  发布策略:
       • 批量大小: 5 篇/批
       • 最大重试: 3 次
       • 重试延迟: 5 分钟

    🕐 时间控制:
       • 发布时间: 08:00 - 22:00
       • 周末发布: 允许

    🔒 限流配置:
       • 每日限制: 50 篇/天
       • 每小时限制: 10 篇/小时

    📝 内容过滤:
       • 最低评分: 30
       • 允许分类: 全部
       • 阻止关键词: 无

[2] GITHUB - 优先级 9/10
    ... (类似)

[3] WECHAT - 优先级 8/10
    ... (类似)

总计: 3 个发布渠道已配置
================================================================================
```

## 修改配置

### Python 代码修改

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import PublishPriority

# 连接数据库
engine = create_engine("sqlite:///data/db/deepdive_tracking.db")
Session = sessionmaker(bind=engine)
session = Session()

# 查询 Email 优先级配置
email_priority = session.query(PublishPriority).filter_by(channel="email").first()

# 修改配置
email_priority.min_score = 35                    # 提高最低评分
email_priority.batch_size = 10                   # 增加批量大小
email_priority.max_per_day = 100                 # 增加每日限制
email_priority.channel_config["send_summary"] = False

session.commit()
print("✓ 配置已更新")
```

### 数据库 SQL 修改

```sql
-- 提高 Email 的最低评分阈值
UPDATE publish_priorities SET min_score = 35 WHERE channel = 'email';

-- 禁用 WeChat 发布
UPDATE publish_priorities SET is_enabled = false WHERE channel = 'wechat';

-- 设置 GitHub 只在工作日发布
UPDATE publish_priorities SET publish_on_weekends = false WHERE channel = 'github';
```

## 执行发布

### 1. 通过 E2E 测试脚本

```bash
# 测试模式 (dry-run - 不实际发布)
python scripts/run_priority_publishing_test.py 5 --dry-run

# 实际发布模式 (最多 5 篇)
python scripts/run_priority_publishing_test.py 5
```

### 2. 通过 Python 代码

```python
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.services.workflow.priority_publishing_workflow import PriorityPublishingWorkflow

# 连接数据库
engine = create_engine("sqlite:///data/db/deepdive_tracking.db")
Session = sessionmaker(bind=engine)
session = Session()

# 创建工作流
workflow = PriorityPublishingWorkflow(db_session=session)

# 配置发布渠道
workflow.configure_channels(
    email_config={
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "your_email@gmail.com",
        "smtp_password": "your_password",
        "from_email": "your_email@gmail.com",
        "email_list": ["recipient@example.com"]
    },
    github_config={
        "token": "your_github_token",
        "repo": "your_username/deepdive-tracking",
        "username": "your_username",
        "local_path": "./github_repo"
    },
    wechat_config={
        "app_id": "your_wechat_app_id",
        "app_secret": "your_wechat_app_secret"
    }
)

# 执行发布
result = asyncio.run(workflow.execute(article_limit=10, dry_run=False))

# 查看结果
print(f"成功发布到 {len(result['channels_executed'])} 个渠道")
print(f"总发布数: {result['total_published']} 篇")
```

## 过滤规则

### 按评分过滤

每个渠道可以设置最低评分阈值 `min_score`：

```python
# Email: 最低评分 30
# GitHub: 最低评分 25
# WeChat: 最低评分 40 (对内容质量要求最高)
```

### 按分类过滤

可以为每个渠道设置允许的分类：

```python
email_priority.allowed_categories = ["AI", "LLM", "Research"]  # 只发布这些分类
github_priority.allowed_categories = None  # None 表示允许所有分类
```

### 按关键词过滤

可以设置阻止的关键词：

```python
wechat_priority.blocked_keywords = ["adult", "nsfw", "sensitive"]
```

## 时间控制

### 发布时间范围

限制发布的时间段：

```python
email_priority.publish_time_start = "08:00"  # 早上 8 点
email_priority.publish_time_end = "22:00"    # 晚上 10 点
```

### 周末发布

控制是否在周末发布：

```python
email_priority.publish_on_weekends = True      # 允许周末发布
github_priority.publish_on_weekends = False    # 只在工作日发布
```

## 限流配置

### 每日限制

限制每天最多发布的文章数：

```python
email_priority.max_per_day = 50   # 每天最多 50 篇
github_priority.max_per_day = 100  # 每天最多 100 篇
wechat_priority.max_per_day = 30   # 每天最多 30 篇
```

### 每小时限制

限制每小时最多发布的文章数：

```python
email_priority.max_per_hour = 10   # 每小时最多 10 篇
github_priority.max_per_hour = None  # None 表示无限制
```

## 渠道特定配置

### Email 配置

```python
email_priority.channel_config = {
    "send_summary": True,              # 发送摘要
    "include_source_url": True,        # 包含源链接
    "batch_name_format": "DeepDive Daily - {date}"  # 批次名称格式
}
```

### GitHub 配置

```python
github_priority.channel_config = {
    "auto_create_issues": False,       # 自动创建 Issue
    "create_discussions": True,        # 创建讨论
    "labels": ["ai", "news", "deepdive"],  # 标签
    "branch_format": "news/{date}"     # 分支名称格式
}
```

### WeChat 配置

```python
wechat_priority.channel_config = {
    "show_cover_image": True,          # 显示封面图
    "enable_comments": True,           # 启用评论
    "message_type": "news"             # 消息类型
}
```

## 工作流架构

### PriorityPublishingWorkflow 类

位置：`src/services/workflow/priority_publishing_workflow.py`

**关键方法：**

1. **`configure_channels()`** - 配置发布渠道
   - 初始化 Email、GitHub、WeChat 发布器
   - 验证渠道配置有效性

2. **`execute(article_limit, dry_run)`** - 执行发布工作流
   - 加载优先级配置
   - 获取已批准的文章
   - 按优先级发布到各渠道
   - 返回发布结果统计

3. **`_load_channel_priorities()`** - 加载优先级配置
   - 从数据库查询所有启用的优先级配置
   - 按优先级降序排序

4. **`_get_approved_articles(limit)`** - 获取待发布文章
   - 查询状态为 "approved" 的 ContentReview
   - 检查是否已发布 (避免重复发布)
   - 返回文章列表

5. **`_filter_articles(articles, priority_config)`** - 过滤文章
   - 按评分过滤 (`min_score`)
   - 按分类过滤 (`allowed_categories`)
   - 按关键词过滤 (`blocked_keywords`)

6. **`_publish_to_channel()`** - 发布到单个渠道
   - 检查渠道是否启用
   - 检查发布时间限制
   - 调用相应的发布方法 (Email/GitHub/WeChat)

7. **`_publish_email()`, `_publish_github()`, `_publish_wechat()`** - 渠道特定发布
   - 调用对应的发布器
   - 保存发布记录到数据库
   - 返回发布结果

## 发布流程图

```
开始
  ↓
检查优先级配置是否存在 ─→ 否 ─→ 返回错误
  ↓ 是
获取已批准的文章 ─→ 无 ─→ 返回成功 (无文章)
  ↓ 有
遍历优先级配置 (从高到低)
  ↓
对每个渠道：
  ├─ 是否启用? ─→ 否 ─→ 跳过
  │
  ├─ 是否自动发布? ─→ 否 ─→ 跳过
  │
  ├─ 是否在发布时间范围内? ─→ 否 ─→ 跳过
  │
  ├─ 过滤文章 (评分、分类、关键词)
  │
  ├─ 是否有符合条件的文章? ─→ 否 ─→ 跳过
  │
  ├─ 发布到此渠道
  │  ├─ 调用发布器
  │  ├─ 保存发布记录
  │  └─ 更新统计信息
  │
  └─ 返回发布结果
  ↓
继续下一个渠道
  ↓
所有渠道处理完成
  ↓
返回最终结果 (统计信息、发布数量等)
  ↓
结束
```

## 常见场景

### 场景 1: 只发布到 Email 和 GitHub，不发布到 WeChat

```python
# 禁用 WeChat
wechat_priority = session.query(PublishPriority).filter_by(channel="wechat").first()
wechat_priority.is_enabled = False
session.commit()
```

### 场景 2: 只在工作日的工作时间发布

```python
for priority in session.query(PublishPriority).all():
    priority.publish_time_start = "09:00"
    priority.publish_time_end = "18:00"
    priority.publish_on_weekends = False
session.commit()
```

### 场景 3: 对每个渠道设置不同的质量要求

```python
# Email - 宽松的质量要求
email_priority.min_score = 20
email_priority.allowed_categories = None

# GitHub - 中等质量要求
github_priority.min_score = 30
github_priority.allowed_categories = ["AI", "LLM"]

# WeChat - 严格的质量要求
wechat_priority.min_score = 50
wechat_priority.allowed_categories = ["AI"]
wechat_priority.blocked_keywords = ["beta", "experimental"]

session.commit()
```

### 场景 4: 实现渠道特定的发布策略

```python
# Email - 大量发送 (批量大小大)
email_priority.batch_size = 20
email_priority.max_per_day = 200

# GitHub - 中等发送 (批量大小中等)
github_priority.batch_size = 10
github_priority.max_per_day = 50

# WeChat - 精选发送 (批量大小小)
wechat_priority.batch_size = 3
wechat_priority.max_per_day = 10

session.commit()
```

## 性能优化

### 批量大小优化

```python
# 对于流量大的渠道，增加批量大小以提高效率
email_priority.batch_size = 20  # 原来是 5

# 对于流量小的渠道，保持较小的批量大小
wechat_priority.batch_size = 3
```

### 数据库查询优化

优先级发布工作流已优化查询：

- 使用索引查询已启用的优先级配置
- 使用单一查询获取所有已批准的文章
- 使用批量操作更新统计信息

## 监控和调试

### 查看发布统计

```python
from src.models import PublishPriority

# 查询发布成功率
for priority in session.query(PublishPriority).all():
    success_rate = priority.get_success_rate()
    print(f"{priority.channel}: {success_rate:.1f}% 成功率")
```

### 查看发布日志

```bash
# 查看最近的发布操作
tail -f logs/deepdive_tracking.log | grep "发布"
```

### 调试优先级发布

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 运行工作流
result = asyncio.run(workflow.execute(article_limit=5, dry_run=True))
```

## 常见问题

### Q: 为什么某个渠道没有发布任何内容？

**可能原因：**
1. 渠道未启用 (`is_enabled = False`)
2. 不在发布时间范围内
3. 没有符合最低评分要求的文章
4. 渠道配置不完整

**排查步骤：**
```bash
python scripts/show_publish_priorities.py  # 检查配置
```

### Q: 如何实现周一到周五只发布，周末不发布？

```python
priority.publish_on_weekends = False
session.commit()
```

### Q: 如何限制每个渠道每天最多发布 10 篇？

```python
priority.max_per_day = 10
session.commit()
```

### Q: 能否为不同的分类设置不同的优先级？

目前优先级系统基于渠道维度，不支持基于分类的优先级。可以使用 `allowed_categories` 字段来限制每个渠道的分类。

## 总结

优先级发布系统提供：

✅ 灵活的多渠道发布顺序管理
✅ 每个渠道独立的配置和过滤规则
✅ 时间和限流控制
✅ 完整的统计和监控功能
✅ Dry-run 模式支持安全测试

通过合理配置优先级发布系统，可以实现：
- Email 作为第一优先级，确保重要内容及时发送
- GitHub 作为第二优先级，存档重要信息
- WeChat 作为第三优先级，精选内容分享

