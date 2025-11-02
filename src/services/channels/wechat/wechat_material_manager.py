"""
WeChat 永久素材管理器

提供永久素材 API 的完整实现，支持：
- 上传图片到永久素材
- 上传图文消息到永久素材
- 获取素材详情
- 获取素材列表（分页）
- 删除素材
- 获取素材统计

参考文档: https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_permanent_assets.html
"""

import aiohttp
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import io

logger = logging.getLogger(__name__)


class WeChatMaterialManager:
    """WeChat 永久素材管理器"""

    API_BASE = "https://api.weixin.qq.com"
    TOKEN_CACHE_BUFFER = 60  # 提前60秒刷新token

    def __init__(self, app_id: str, app_secret: str):
        """
        初始化素材管理器

        Args:
            app_id: WeChat 公众号 App ID
            app_secret: WeChat 公众号 App Secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """
        获取 access_token

        WeChat access_token 有效期为 7200 秒，此处缓存以减少 API 调用。
        当缓存过期或即将过期时（缓冲 60 秒）重新获取。

        Returns:
            str: 有效的 access_token

        Raises:
            Exception: 获取 token 失败
        """
        # 检查缓存是否还有效
        if self._token and datetime.now() < self._token_expires:
            return self._token

        logger.info("获取 WeChat access_token...")

        url = f"{self.API_BASE}/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.app_id,
            "secret": self.app_secret
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}: {await resp.text()}")

                    data = await resp.json()

                    if "errcode" in data:
                        raise Exception(f"WeChat API Error: {data.get('errmsg', 'Unknown error')}")

                    self._token = data["access_token"]
                    # 缓存 7200 秒减去 60 秒缓冲
                    self._token_expires = datetime.now() + timedelta(seconds=7200 - self.TOKEN_CACHE_BUFFER)
                    logger.info(f"✓ 成功获取 token，有效期至 {self._token_expires.strftime('%Y-%m-%d %H:%M:%S')}")
                    return self._token

        except Exception as e:
            logger.error(f"✗ 获取 token 失败: {str(e)}")
            raise

    async def upload_image(self, image_path: str) -> str:
        """
        上传图片到永久素材

        用于上传图文消息中的图片或其他图片素材。

        Args:
            image_path: 图片文件路径（本地文件或 URL）

        Returns:
            str: 图片在永久素材中的 media_id 或 URL

        Raises:
            Exception: 上传失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/media/uploadimg?access_token={token}"

        try:
            # 处理 URL 或本地文件
            if image_path.startswith(("http://", "https://")):
                logger.info(f"从 URL 下载图片: {image_path[:50]}...")
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_path, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            raise Exception(f"下载图片失败: HTTP {resp.status}")
                        image_data = await resp.read()
                filename = image_path.split("/")[-1] or "image.jpg"
            else:
                # 本地文件
                path = Path(image_path)
                if not path.exists():
                    raise FileNotFoundError(f"文件不存在: {image_path}")

                logger.info(f"读取本地图片: {image_path}")
                with open(image_path, "rb") as f:
                    image_data = f.read()
                filename = path.name

            logger.info(f"上传图片 ({len(image_data) / 1024:.1f}KB)...")

            # 构建 multipart 表单数据
            data = aiohttp.FormData()
            data.add_field(
                "media",
                io.BytesIO(image_data),
                filename=filename,
                content_type="image/jpeg"
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    image_url = result.get("url")
                    logger.info(f"✓ 图片上传成功: {image_url[:60]}...")
                    return image_url

        except Exception as e:
            logger.error(f"✗ 上传图片失败: {str(e)}")
            raise

    async def upload_news_material(self, articles: List[Dict]) -> str:
        """
        上传图文消息到永久素材

        上传图文消息并获得永久的 media_id，可以多次使用。

        Args:
            articles: 图文消息列表，每个元素包含：
                {
                    "title": "文章标题",
                    "author": "作者",
                    "digest": "摘要 (最多140字)",
                    "show_cover_pic": 1,  # 是否显示封面
                    "content": "文章内容 (HTML格式)",
                    "content_source_url": "原文链接",
                    "thumb_media_id": "封面图片 media_id"
                }

        Returns:
            str: 图文消息的 media_id

        Raises:
            Exception: 上传失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/add_material?access_token={token}&type=news"

        try:
            # 验证文章数据
            if not articles:
                raise ValueError("文章列表不能为空")
            if len(articles) > 8:
                raise ValueError("单个图文消息最多支持 8 个文章")

            logger.info(f"上传图文消息: {len(articles)} 篇文章")

            payload = {"articles": articles}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    # Handle both JSON and text responses
                    content_type = resp.content_type

                    if "application/json" in content_type:
                        result = await resp.json()
                    else:
                        # WeChat might return text/plain in error cases
                        text = await resp.text()
                        logger.warning(f"WeChat API returned {content_type}: {text}")
                        # Try to parse as JSON anyway
                        try:
                            result = json.loads(text)
                        except json.JSONDecodeError:
                            raise Exception(f"WeChat API returned non-JSON response: {text}")

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    media_id = result.get("media_id")
                    logger.info(f"✓ 图文消息上传成功: {media_id}")
                    return media_id

        except Exception as e:
            logger.error(f"✗ 上传图文消息失败: {str(e)}")
            raise

    async def get_material(self, media_id: str) -> Dict:
        """
        获取永久素材详情

        Args:
            media_id: 素材的 media_id

        Returns:
            Dict: 素材详情信息

        Raises:
            Exception: 获取失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/get_material?access_token={token}"

        try:
            logger.info(f"获取素材详情: {media_id}")

            payload = {"media_id": media_id}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    logger.info(f"✓ 获取素材成功")
                    return result

        except Exception as e:
            logger.error(f"✗ 获取素材失败: {str(e)}")
            raise

    async def get_materials_list(
        self,
        type: str = "news",
        offset: int = 0,
        count: int = 20
    ) -> tuple[List[Dict], int]:
        """
        获取永久素材列表（分页）

        Args:
            type: 素材类型 (news, image, video, voice)
            offset: 分页偏移 (0开始)
            count: 单次查询数量 (不超过50)

        Returns:
            tuple: (素材列表, 总数)

        Raises:
            Exception: 获取失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/batchget_material?access_token={token}"

        try:
            if count > 50:
                count = 50
            if offset < 0:
                offset = 0

            logger.info(f"获取素材列表: type={type}, offset={offset}, count={count}")

            payload = {
                "type": type,
                "offset": offset,
                "count": count
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    items = result.get("item", [])
                    item_count = result.get("item_count", 0)
                    logger.info(f"✓ 获取素材列表成功: {len(items)} 项, 总计 {item_count} 项")
                    return items, item_count

        except Exception as e:
            logger.error(f"✗ 获取素材列表失败: {str(e)}")
            raise

    async def delete_material(self, media_id: str) -> bool:
        """
        删除永久素材

        Args:
            media_id: 素材的 media_id

        Returns:
            bool: 是否删除成功

        Raises:
            Exception: 删除失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/del_material?access_token={token}"

        try:
            logger.info(f"删除素材: {media_id}")

            payload = {"media_id": media_id}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    logger.info(f"✓ 素材删除成功")
                    return True

        except Exception as e:
            logger.error(f"✗ 删除素材失败: {str(e)}")
            raise

    async def get_material_count(self) -> Dict:
        """
        获取永久素材统计

        获取各类型素材的数量和配额信息。

        Returns:
            Dict: 包含以下字段:
                - voice_count: 语音素材数
                - video_count: 视频素材数
                - image_count: 图片素材数
                - news_count: 图文素材数
                - image_quota: 图片配额
                - video_quota: 视频配额
                - voice_quota: 语音配额
                - news_quota: 图文配额

        Raises:
            Exception: 获取失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/material/get_materialcount?access_token={token}"

        try:
            logger.info("获取素材统计...")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    logger.info(f"✓ 获取素材统计成功")
                    logger.info(
                        f"  图文: {result.get('news_count')}/{result.get('news_quota')} | "
                        f"图片: {result.get('image_count')}/{result.get('image_quota')} | "
                        f"视频: {result.get('video_count')}/{result.get('video_quota')}"
                    )
                    return result

        except Exception as e:
            logger.error(f"✗ 获取素材统计失败: {str(e)}")
            raise

    async def check_quota(self) -> bool:
        """
        检查是否还有配额空间

        Returns:
            bool: True 表示还有配额
        """
        try:
            stats = await self.get_material_count()
            news_count = stats.get("news_count", 0)
            news_quota = stats.get("news_quota", 5000)
            image_count = stats.get("image_count", 0)
            image_quota = stats.get("image_quota", 100000)

            if news_count >= news_quota:
                logger.warning(f"⚠️ 图文消息配额已满: {news_count}/{news_quota}")
                return False
            if image_count >= image_quota:
                logger.warning(f"⚠️ 图片配额已满: {image_count}/{image_quota}")
                return False

            logger.info(f"✓ 配额充足")
            return True

        except Exception as e:
            logger.error(f"✗ 检查配额失败: {str(e)}")
            return False
