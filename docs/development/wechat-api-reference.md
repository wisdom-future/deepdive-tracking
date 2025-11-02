# WeChat 永久素材 API 参考指南

**日期：** 2025-11-02
**类型：** API 参考文档
**用途：** Phase 3 实现的 API 映射和调用示例

---

## 📚 API 端点列表

### 永久素材管理 API

| 功能 | 英文名称 | API 端点 | 请求方式 | 用途 |
|------|---------|---------|---------|------|
| 获取永久素材 | getMaterial | `/cgi-bin/material/get_material` | POST | 获取已上传的单个素材详情 |
| 获取永久素材总数 | getMaterialCount | `/cgi-bin/material/get_materialcount` | GET | 获取各类型素材的统计数量 |
| 获取永久素材列表 | batchGetMaterial | `/cgi-bin/material/batchget_material` | POST | 分页获取某类型素材列表 |
| 上传图文消息图片 | uploadImage | `/cgi-bin/media/uploadimg` | POST | 上传图文消息中的图片 |
| 上传永久素材 | addMaterial | `/cgi-bin/material/add_material` | POST | 上传新的永久素材（图片、视频、图文等） |
| 删除永久素材 | delMaterial | `/cgi-bin/material/del_material` | POST | 删除已上传的永久素材 |

---

## 🔧 实现映射

### 1. 上传图文消息图片

**API：** `uploadImage` → `/cgi-bin/media/uploadimg`

**用途：** 上传图文消息中使用的图片（封面、内容配图等）

**请求：**
```bash
POST https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=ACCESS_TOKEN
Content-Type: multipart/form-data

media=<IMAGE_BINARY_DATA>
```

**响应：**
```json
{
    "url": "http://mmbiz.qpic.cn/mmbiz_jpg/wD1..."
}
```

**Python 实现：**
```python
async def upload_image(self, image_path: str) -> str:
    """上传图片，返回图片 URL"""
    token = await self._get_access_token()
    url = f"{self.API_BASE}/cgi-bin/media/uploadimg?access_token={token}"

    with open(image_path, "rb") as f:
        data = aiohttp.FormData()
        data.add_field("media", f, filename="image.jpg")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                result = await resp.json()
                return result.get("url")
```

**调用场景：**
```python
# 在发布前上传封面图片
cover_image_url = await material_manager.upload_image("cover.jpg")
# 返回：http://mmbiz.qpic.cn/mmbiz_jpg/wD1...
```

---

### 2. 上传永久素材

**API：** `addMaterial` → `/cgi-bin/material/add_material`

**用途：** 上传图文消息作为永久素材，获得可长期使用的 media_id

**请求（图文消息）：**
```bash
POST https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=ACCESS_TOKEN&type=news
Content-Type: application/json

{
    "articles": [
        {
            "title": "文章标题",
            "author": "作者",
            "digest": "摘要，最多140个字符",
            "show_cover_pic": 1,
            "content": "文章内容 HTML",
            "content_source_url": "https://example.com/article",
            "thumb_media_id": "图片 media_id"
        }
    ]
}
```

**响应：**
```json
{
    "media_id": "LY1234567890",
    "item_id": 123456
}
```

**Python 实现：**
```python
async def upload_news_material(self, articles: List[Dict]) -> str:
    """上传图文消息为永久素材"""
    token = await self._get_access_token()
    url = f"{self.API_BASE}/cgi-bin/material/add_material?access_token={token}&type=news"

    payload = {"articles": articles}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            if result.get("errcode") == 0:
                return result.get("media_id")
            else:
                raise Exception(f"上传失败: {result.get('errmsg')}")
```

**调用场景：**
```python
# 发布前构建文章
articles = [{
    "title": "AI 最新动态：OpenAI 发布 GPT-5",
    "author": "DeepDive Team",
    "digest": "今天 OpenAI 官方宣布...",
    "show_cover_pic": 1,
    "content": "<h1>AI 最新动态</h1><p>OpenAI 发布了...</p>",
    "content_source_url": "https://openai.com/...",
    "thumb_media_id": "LZ_mq-LY1234567890"  # 封面图片的 media_id
}]

media_id = await manager.upload_news_material(articles)
# 返回：LY_mq-LY1234567890
```

---

### 3. 获取永久素材

**API：** `getMaterial` → `/cgi-bin/material/get_material`

**用途：** 查询已上传素材的详细信息

**请求：**
```bash
POST https://api.weixin.qq.com/cgi-bin/material/get_material?access_token=ACCESS_TOKEN
Content-Type: application/json

{
    "media_id": "LY1234567890"
}
```

**响应（图文消息）：**
```json
{
    "title": "文章标题",
    "author": "作者",
    "digest": "摘要",
    "show_cover_pic": 1,
    "content": "文章内容",
    "content_source_url": "https://example.com",
    "create_time": 1234567890,
    "update_time": 1234567899
}
```

**Python 实现：**
```python
async def get_material(self, media_id: str) -> Dict:
    """获取素材详情"""
    token = await self._get_access_token()
    url = f"{self.API_BASE}/cgi-bin/material/get_material?access_token={token}"

    payload = {"media_id": media_id}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.json()
```

**调用场景：**
```python
# 验证素材是否存在
material = await manager.get_material("LY1234567890")
if material:
    print(f"素材标题: {material['title']}")
    print(f"创建时间: {datetime.fromtimestamp(material['create_time'])}")
```

---

### 4. 获取永久素材列表

**API：** `batchGetMaterial` → `/cgi-bin/material/batchget_material`

**用途：** 分页获取某类型的素材列表（支持查询、排序）

**请求：**
```bash
POST https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token=ACCESS_TOKEN
Content-Type: application/json

{
    "type": "news",           // 素材类型：news, image, video, voice
    "offset": 0,              // 分页偏移
    "count": 20               // 一次查询的最多条数，不超过50
}
```

**响应：**
```json
{
    "item_count": 2,
    "item": [
        {
            "media_id": "LY1234567890",
            "content": {
                "title": "文章标题",
                "author": "作者"
            },
            "update_time": 1234567890
        }
    ]
}
```

**Python 实现：**
```python
async def get_materials_list(
    self,
    type: str = "news",
    offset: int = 0,
    count: int = 20
) -> List[Dict]:
    """获取素材列表"""
    token = await self._get_access_token()
    url = f"{self.API_BASE}/cgi-bin/material/batchget_material?access_token={token}"

    payload = {
        "type": type,
        "offset": offset,
        "count": count
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result.get("item", [])
```

**调用场景：**
```python
# 列出所有图文消息素材
materials = await manager.get_materials_list(type="news", offset=0, count=50)

for material in materials:
    print(f"ID: {material['media_id']}")
    print(f"标题: {material['content']['title']}")
    print(f"更新: {datetime.fromtimestamp(material['update_time'])}")
```

---

### 5. 删除永久素材

**API：** `delMaterial` → `/cgi-bin/material/del_material`

**用途：** 删除已上传的永久素材

**请求：**
```bash
POST https://api.weixin.qq.com/cgi-bin/material/del_material?access_token=ACCESS_TOKEN
Content-Type: application/json

{
    "media_id": "LY1234567890"
}
```

**响应：**
```json
{
    "errcode": 0,
    "errmsg": "ok"
}
```

**Python 实现：**
```python
async def delete_material(self, media_id: str) -> bool:
    """删除永久素材"""
    token = await self._get_access_token()
    url = f"{self.API_BASE}/cgi-bin/material/del_material?access_token={token}"

    payload = {"media_id": media_id}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result.get("errcode") == 0
```

**调用场景：**
```python
# 删除过期素材
if await manager.delete_material("LY1234567890"):
    print("删除成功")
else:
    print("删除失败")
```

---

### 6. 获取永久素材总数

**API：** `getMaterialCount` → `/cgi-bin/material/get_materialcount`

**用途：** 获取各类型素材的统计数量和配额

**请求：**
```bash
GET https://api.weixin.qq.com/cgi-bin/material/get_materialcount?access_token=ACCESS_TOKEN
```

**响应：**
```json
{
    "voice_count": 0,          // 语音素材数
    "video_count": 0,          // 视频素材数
    "image_count": 5,          // 图片素材数
    "news_count": 20,          // 图文素材数
    "image_quota": 100000,     // 图片配额
    "video_quota": 1000,       // 视频配额
    "voice_quota": 1000,       // 语音配额
    "news_quota": 5000         // 图文配额
}
```

**Python 实现：**
```python
async def get_material_count(self) -> Dict:
    """获取素材总数和配额"""
    token = await self._get_access_token()
    url = f"{self.API_BASE}/cgi-bin/material/get_materialcount?access_token={token}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
```

**调用场景：**
```python
# 检查素材配额
stats = await manager.get_material_count()

print(f"图文消息: {stats['news_count']}/{stats['news_quota']}")
print(f"图片: {stats['image_count']}/{stats['image_quota']}")

if stats['news_count'] >= stats['news_quota']:
    print("警告: 图文消息配额已满！")
```

---

## 🔄 工作流整合示例

### 完整的发布工作流

```python
async def publish_with_permanent_materials(
    manager: WeChatMaterialManager,
    article_data: Dict
) -> Dict:
    """使用永久素材 API 发布文章"""

    try:
        # Step 1: 上传封面图片
        print("1. 上传封面图片...")
        cover_image_url = await manager.upload_image(article_data['cover_path'])
        print(f"   ✓ 图片 URL: {cover_image_url}")

        # Step 2: 构建图文消息
        print("2. 构建图文消息...")
        articles = [{
            "title": article_data['title'],
            "author": article_data['author'],
            "digest": article_data['summary'][:140],
            "show_cover_pic": 1,
            "content": article_data['content'],
            "content_source_url": article_data['source_url'],
            "thumb_media_id": cover_image_url  # 使用上传的图片 URL
        }]

        # Step 3: 上传为永久素材
        print("3. 上传为永久素材...")
        media_id = await manager.upload_news_material(articles)
        print(f"   ✓ Media ID: {media_id}")

        # Step 4: 验证上传成功
        print("4. 验证上传...")
        material = await manager.get_material(media_id)
        print(f"   ✓ 素材标题: {material['title']}")

        # Step 5: 保存到数据库缓存
        print("5. 保存缓存...")
        # 这里保存到 wechat_media_cache 表
        save_media_cache(
            media_id=media_id,
            content_id=article_data['content_id'],
            type='news',
            media_url=cover_image_url
        )

        # Step 6: 通过客服消息 API 发送
        print("6. 发送消息...")
        # 这里调用消息发送 API
        result = await send_news_message(media_id)

        return {
            "success": True,
            "media_id": media_id,
            "message": "发布成功"
        }

    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

---

## 📊 API 配额和限制

| 资源 | 限制 | 说明 |
|------|------|------|
| 图片素材 | 100,000 个 | 单个图片大小 < 2MB |
| 视频素材 | 1,000 个 | 单个视频大小 < 2GB |
| 图文素材 | 5,000 个 | 单个图文最多 8 个 article |
| 语音素材 | 1,000 个 | 单个语音大小 < 5MB |
| 上传频率 | 无限制 | 但单 IP 单天调用上限 1000 次 |
| 素材有效期 | 永久 | 除非主动删除 |

---

## ✅ 测试清单

实现这些 API 时的测试清单：

```python
# tests/test_wechat_material_manager.py

def test_upload_image():
    """测试上传图片"""
    # Arrange: 准备测试图片
    # Act: 调用 upload_image()
    # Assert: 验证返回有效的图片 URL

def test_upload_news_material():
    """测试上传图文消息"""
    # Arrange: 准备文章数据
    # Act: 调用 upload_news_material()
    # Assert: 验证返回有效的 media_id

def test_get_material():
    """测试获取素材详情"""
    # Arrange: 上传一个素材
    # Act: 调用 get_material()
    # Assert: 验证返回的数据完整

def test_get_materials_list():
    """测试获取素材列表"""
    # Arrange: 上传多个素材
    # Act: 调用 get_materials_list()
    # Assert: 验证列表返回正确

def test_delete_material():
    """测试删除素材"""
    # Arrange: 上传一个素材
    # Act: 调用 delete_material()
    # Assert: 验证删除成功

def test_get_material_count():
    """测试获取配额"""
    # Act: 调用 get_material_count()
    # Assert: 验证返回统计数据
```

---

## 🚨 常见错误和解决方案

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|---------|------|--------|
| 40001 | invalid credential access_token | token 无效或过期 | 重新获取 token，检查缓存逻辑 |
| 40002 | invalid grant_type | 授权类型错误 | 使用 `client_credential` |
| 40003 | invalid openid | openid 无效 | 确认是否为已关注用户 |
| 40014 | invalid media_id | media_id 不存在 | 检查是否已删除或输入错误 |
| 40015 | invalid menu type | 菜单类型错误 | 使用支持的类型（news, image 等） |
| 41005 | media missing some required fields | 媒体缺少必要字段 | 检查 articles 结构完整性 |

---

## 📖 下一步参考

- [Phase 3 实现指南](./phase3-implementation-guide.md) - 完整的实现计划
- [WeChat 官方 API 文档](https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_permanent_assets.html)
- [错误码参考](https://developers.weixin.qq.com/doc/offiaccount/Global/error_code.html)

---

**最后更新：** 2025-11-02
**版本：** 1.0
**状态：** 参考文档
