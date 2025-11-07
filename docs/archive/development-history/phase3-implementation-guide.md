# Phase 3 实现指南：多渠道发布与 WeChat API 升级

**版本：** 1.0
**日期：** 2025-11-02
**状态：** 规划阶段
**作者：** DeepDive Tracking Team

---

## 📋 概述

Phase 3 的核心目标是：
1. **升级 WeChat 发布方案** - 从已弃用的 `news.add` 迁移到现代 API
2. **扩展发布渠道** - 支持多个内容分发平台
3. **完善发布流程** - 改进媒体管理、错误处理、状态跟踪

**时间线：** 4-6周
**优先级：** 高（直接影响产品可用性）

---

## 🎯 Phase 3 的四个主要任务

### 1️⃣ WeChat 官方账号 API 升级（高优先级）

#### 当前状态 ✗
- 使用已弃用的 `news.add` API（图文消息接口）
- 返回错误：`This API has been unsupported`
- 数据库中所有发布状态为 `draft`

#### 升级方案

**方案 A：客服消息 API**（推荐 ✅）
- **API 端点：** `/cgi-bin/message/mass/send`
- **优点：**
  - 官方完全支持，不存在弃用风险
  - 可直接发送给已关注粉丝
  - 支持文本、图片、视频、图文等多种消息类型
  - 提供消息统计和反馈
- **缺点：**
  - 需要粉丝已关注公众号
  - 有发送频率限制（48小时内不超过4条图文）

**方案 B：模板消息 API**（备选）
- **API 端点：** `/cgi-bin/message/template/send`
- **优点：**
  - 官方全力支持
  - 用户体验更好（可设置跳转链接）
  - 可发送给非关注用户
- **缺点：**
  - 需要用户主动订阅模板消息
  - 功能相对受限

**方案 C：永久素材 API**（辅助）
- **用途：** 媒体资源管理（图片、视频等）
- **可用端点：**
  ```
  上传永久素材      /cgi-bin/material/add_material
  获取永久素材      /cgi-bin/material/get_material
  获取素材列表      /cgi-bin/material/batchget_material
  删除永久素材      /cgi-bin/material/del_material
  获取素材总数      /cgi-bin/material/get_materialcount
  上传图文消息图片  /cgi-bin/media/uploadimg
  ```
- **优点：**
  - 可存储可复用的媒体资源
  - 支持图文消息的富媒体内容
  - 有素材管理后台

---

### 2️⃣ 实现永久素材管理系统

#### 新增服务类

**文件：** `src/services/channels/wechat_material_manager.py`

```python
class WeChatMaterialManager:
    """WeChat 永久素材管理器"""

    def upload_image(self, image_path: str) -> str:
        """上传图片，返回 media_id"""
        # POST /cgi-bin/media/uploadimg

    def upload_news_material(self, articles: List[Dict]) -> str:
        """上传图文消息，返回 media_id"""
        # POST /cgi-bin/material/add_material

    def get_material(self, media_id: str) -> Dict:
        """获取素材详情"""
        # POST /cgi-bin/material/get_material

    def get_materials_list(self, type: str, offset: int = 0) -> List[Dict]:
        """获取素材列表"""
        # POST /cgi-bin/material/batchget_material

    def delete_material(self, media_id: str) -> bool:
        """删除素材"""
        # POST /cgi-bin/material/del_material

    def get_material_count(self) -> Dict:
        """获取素材统计"""
        # GET /cgi-bin/material/get_materialcount
```

#### 数据库扩展

**新增表：** `wechat_media_cache`
```sql
CREATE TABLE wechat_media_cache (
    id INTEGER PRIMARY KEY,
    media_id VARCHAR(100) UNIQUE NOT NULL,
    content_id INTEGER NOT NULL,
    type VARCHAR(20),           -- image, news, video, etc.
    media_url TEXT,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expire_time TIMESTAMP,      -- 素材有效期
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (content_id) REFERENCES published_content(id)
);

CREATE INDEX idx_media_content ON wechat_media_cache(content_id);
CREATE INDEX idx_media_type ON wechat_media_cache(type);
```

---

### 3️⃣ 实现多渠道发布支持

#### 支持的渠道架构

```
PublishingService
├── WeChatPublisher
│   ├── NewsPublisher (客服消息 API)
│   └── MaterialManager (永久素材)
├── XiaoHongShuPublisher (小红书)
├── WebPublisher (网站直接发布)
└── EmailPublisher (邮件通知)
```

#### WeChat 消息发布新实现

**文件：** `src/services/channels/wechat_news_publisher.py`

```python
class WeChatNewsPublisher:
    """WeChat 客服消息 API 发布器"""

    async def send_news_message(
        self,
        media_id: str,
        touser: str = None  # 特定用户，不指定则发送给所有粉丝
    ) -> Dict:
        """发送图文消息"""
        payload = {
            "touser": touser or "@all",
            "msgtype": "news",
            "news": {"media_id": media_id}
        }
        return await self._post_message(payload)

    async def send_text_message(self, content: str, touser: str = None) -> Dict:
        """发送文本消息"""

    async def get_send_stats(self, msg_id: str) -> Dict:
        """获取发送统计"""
        # GET /cgi-bin/message/get_mass_send_status
```

---

### 4️⃣ 小红书频道集成（可选）

#### 架构设计

**文件：** `src/services/channels/xiaohongshu_publisher.py`

```python
class XiaoHongShuPublisher:
    """小红书 (XiaoHongShu) 发布器"""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    async def publish_note(
        self,
        title: str,
        content: str,
        images: List[str],
        tags: List[str]
    ) -> Dict:
        """发布小红书笔记"""

    async def get_note_stats(self, note_id: str) -> Dict:
        """获取笔记数据"""
```

---

## 🛠️ 实现细节

### Step 1: 升级 WeChat API 集成（Week 1-2）

#### 1.1 更新 WeChatPublisher

**修改：** `src/services/channels/wechat_channel.py`

```python
class WeChatPublisher:
    """升级的 WeChat 发布器 - 支持多种 API"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.material_manager = WeChatMaterialManager(app_id, app_secret)
        self.message_sender = WeChatMessageSender(app_id, app_secret)

    async def publish_article_v2(
        self,
        title: str,
        content: str,
        author: str,
        cover_image_url: str = None,
        source_url: str = None
    ) -> Dict:
        """新的发布方法：使用永久素材 + 客服消息 API"""

        # Step 1: 上传封面图片到永久素材
        if cover_image_url:
            image_media_id = await self.material_manager.upload_image(cover_image_url)

        # Step 2: 构建图文消息
        articles = [{
            "title": title,
            "author": author,
            "digest": content[:100],
            "show_cover_pic": 1,
            "content": content,
            "content_source_url": source_url,
            "thumb_media_id": image_media_id
        }]

        # Step 3: 上传为永久素材
        media_id = await self.material_manager.upload_news_material(articles)

        # Step 4: 通过客服消息 API 发送
        result = await self.message_sender.send_news_message(media_id)

        return {
            "success": result.get("errcode") == 0,
            "media_id": media_id,
            "msg_id": result.get("msg_id"),
            "created_at": result.get("type"),
            "error": result.get("errmsg")
        }
```

#### 1.2 创建永久素材管理器

**新文件：** `src/services/channels/wechat_material_manager.py`

```python
from typing import List, Dict, Optional
import aiohttp
from datetime import datetime, timedelta

class WeChatMaterialManager:
    """WeChat 永久素材管理器"""

    API_BASE = "https://api.weixin.qq.com"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token = None
        self._token_expires = None

    async def _get_access_token(self) -> str:
        """获取 access_token"""
        if self._token and datetime.now() < self._token_expires:
            return self._token

        url = f"{self.API_BASE}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                self._token = data["access_token"]
                # 缓存 7200 秒减去 60 秒缓冲
                self._token_expires = datetime.now() + timedelta(seconds=7140)
                return self._token

    async def upload_image(self, image_url_or_path: str) -> str:
        """上传图片到永久素材"""
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/media/uploadimg?access_token={token}"

        # 处理 URL 或本地文件
        if image_url_or_path.startswith("http"):
            # 从 URL 下载图片
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url_or_path) as resp:
                    image_data = await resp.read()
        else:
            # 本地文件
            with open(image_url_or_path, "rb") as f:
                image_data = f.read()

        # 上传
        data = aiohttp.FormData()
        data.add_field("media", image_data, filename="image.jpg")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                result = await resp.json()
                return result.get("url")  # 返回图片 URL

    async def upload_news_material(self, articles: List[Dict]) -> str:
        """上传图文消息为永久素材"""
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/add_material?access_token={token}&type=news"

        payload = {
            "articles": articles
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                if result.get("errcode") == 0:
                    return result.get("media_id")
                else:
                    raise Exception(f"上传失败: {result.get('errmsg')}")

    async def get_material(self, media_id: str) -> Dict:
        """获取素材详情"""
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/get_material?access_token={token}"

        payload = {"media_id": media_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return await resp.json()

    async def delete_material(self, media_id: str) -> bool:
        """删除永久素材"""
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/del_material?access_token={token}"

        payload = {"media_id": media_id}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                return result.get("errcode") == 0

    async def get_material_count(self) -> Dict:
        """获取素材总数"""
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/get_materialcount?access_token={token}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()
```

---

### Step 2: 数据库迁移（Week 1）

**新文件：** `src/migrations/009_add_wechat_media_cache.py`

```python
def upgrade():
    op.create_table(
        'wechat_media_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.String(100), nullable=False, unique=True),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(20)),
        sa.Column('media_url', sa.Text()),
        sa.Column('upload_time', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expire_time', sa.DateTime()),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['content_id'], ['published_content.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_media_content', 'wechat_media_cache', ['content_id'])
    op.create_index('idx_media_type', 'wechat_media_cache', ['type'])

def downgrade():
    op.drop_table('wechat_media_cache')
```

---

### Step 3: 工作流更新（Week 2）

**修改：** `src/services/workflow/wechat_workflow.py`

```python
class WeChatPublishingWorkflow:
    """更新的 WeChat 发布工作流 - 使用新 API"""

    async def execute_v2(self):
        """使用新 API 执行发布"""

        approved_articles = self._get_approved_articles()
        results = {
            "success": True,
            "published_count": 0,
            "failed_count": 0,
            "articles": []
        }

        for article in approved_articles:
            try:
                # 调用新的发布方法
                result = await self.publisher.publish_article_v2(
                    title=article['title'],
                    content=article['content'],
                    author=article['author'],
                    cover_image_url=article.get('cover_url'),
                    source_url=article.get('source_url')
                )

                if result['success']:
                    results['published_count'] += 1
                    results['articles'].append({
                        'title': article['title'],
                        'media_id': result['media_id'],
                        'msg_id': result['msg_id']
                    })
                    # 保存到数据库
                    self._save_media_cache(article['id'], result['media_id'])
                else:
                    results['failed_count'] += 1

            except Exception as e:
                results['failed_count'] += 1
                self.logger.error(f"发布失败: {str(e)}")

        return results
```

---

## 📊 实现时间表

| 周次 | 任务 | 工作量 | 交付物 |
|------|------|--------|--------|
| Week 1 | 永久素材 API 集成 + DB 迁移 | 40h | `WeChatMaterialManager`, 数据库表 |
| Week 2 | 客服消息 API 实现 + 工作流升级 | 30h | 升级的发布工作流 |
| Week 3 | 测试与 bugfix | 25h | 端到端测试通过 |
| Week 4 | 小红书集成（可选） | 35h | `XiaoHongShuPublisher` |
| Week 5-6 | 其他渠道 + 优化 | 40h | 多渠道发布系统 |

---

## ✅ 验收标准

### 功能验收

- [ ] WeChat 永久素材 API 可成功上传图片
- [ ] WeChat 图文消息可成功创建为永久素材
- [ ] 客服消息 API 可成功发送永久素材给粉丝
- [ ] 媒体缓存表正确记录上传信息
- [ ] 发布工作流使用新 API 正常运行
- [ ] 发布状态从 `draft` 更新为 `published`
- [ ] WeChat 官方后台可看到已发布内容

### 性能标准

- [ ] 单篇文章发布时间 < 5 秒（包括媒体上传）
- [ ] 批量发布 100 篇 < 5 分钟
- [ ] 缓存命中率 > 80%

### 测试覆盖率

- [ ] 单元测试覆盖率 > 85%
- [ ] API 集成测试 100% 通过
- [ ] 端到端工作流测试通过

---

## 🚀 快速开始命令

```bash
# 1. 检出新分支
git checkout -b feature/phase3-wechat-upgrade

# 2. 创建永久素材管理器
touch src/services/channels/wechat_material_manager.py

# 3. 数据库迁移
alembic revision --autogenerate -m "Add WeChat media cache table"
alembic upgrade head

# 4. 运行测试
pytest tests/ -v --cov=src --cov-fail-under=85

# 5. 验证新工作流
python scripts/05-verification/verify_phase3.py
```

---

## 📝 参考资源

### WeChat API 官方文档
- [客服消息 API](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html)
- [永久素材 API](https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_permanent_assets.html)
- [消息群发接口](https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html)

### 相关文件
- [WeChat API 限制说明](../WECHAT_API_LIMITATION.md)
- [Phase 2 完成报告](./phase2-auto-review-wechat-summary.md)
- [系统架构设计](../tech/architecture.md)

---

## ⚠️ 风险和缓解

| 风险 | 影响 | 缓解方案 |
|------|------|--------|
| 媒体 ID 过期 | 发布失败 | 实现自动清理过期素材，添加有效期检查 |
| API 配额限制 | 服务中断 | 监控 API 调用次数，实现队列管理 |
| 粉丝限制 | 无法发送 | 支持多渠道降级，邮件通知等 |
| 媒体损坏 | 发布失败 | 验证媒体完整性，重试机制 |

---

## 🎯 下一步行动

1. **立即行动** (本周)
   - [ ] Review 本文档
   - [ ] 创建 feature 分支
   - [ ] 启动永久素材 API 集成开发

2. **短期行动** (1-2周)
   - [ ] 完成 WeChat API 升级
   - [ ] 通过所有测试
   - [ ] 小规模验证测试

3. **中期行动** (3-4周)
   - [ ] 完整的端到端测试
   - [ ] 性能优化
   - [ ] 小红书集成（可选）

4. **交付准备** (5-6周)
   - [ ] 文档完成
   - [ ] 用户指南
   - [ ] 生产部署准备

---

**最后更新：** 2025-11-02
**负责人：** DeepDive Tracking Team
**状态：** 待执行
