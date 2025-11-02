"""WeChat (微信) publishing channel integration.

支持两种发布方式：
1. 永久素材 API (推荐)：使用官方支持的永久素材和客服消息 API
2. 旧版本 (已弃用)：使用 news.add API (WeChat 已停止支持)

参考文档:
- 永久素材 API: https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/
- 群发接口: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/
"""

import logging
import json
from typing import Optional, Dict, Any
import hashlib
import time
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class WeChatPublisher:
    """WeChat Official Account Publishing Integration.

    This class handles publishing content to WeChat Official Accounts (微信公众号)
    using the WeChat API.

    支持新旧两套 API：
    - V2 (推荐): 使用永久素材 API + 群发接口
    - V1 (已弃用): 使用 news.add API
    """

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        api_base_url: str = "https://api.weixin.qq.com"
    ):
        """Initialize WeChat publisher.

        Args:
            app_id: WeChat Official Account App ID
            app_secret: WeChat Official Account App Secret
            api_base_url: WeChat API base URL
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.api_base_url = api_base_url
        self.access_token = None
        self.access_token_expires_at = None
        self.logger = logger

        # 延迟导入以支持异步
        self._material_manager = None
        self._message_sender = None

    @property
    def material_manager(self):
        """Lazy load material manager"""
        if self._material_manager is None:
            from .wechat_material_manager import WeChatMaterialManager
            self._material_manager = WeChatMaterialManager(self.app_id, self.app_secret)
        return self._material_manager

    @property
    def message_sender(self):
        """Lazy load message sender"""
        if self._message_sender is None:
            from .wechat_message_sender import WeChatMessageSender
            self._message_sender = WeChatMessageSender(self.app_id, self.app_secret)
        return self._message_sender

    def _get_access_token(self) -> str:
        """Get WeChat API access token.

        WeChat access tokens expire every 7200 seconds, so we cache them
        and refresh when needed.

        Returns:
            Access token string

        Raises:
            RuntimeError: If unable to get access token
        """
        # Check if we have a valid cached token
        if self.access_token and self.access_token_expires_at:
            if time.time() < self.access_token_expires_at:
                return self.access_token

        # Get new token
        try:
            import requests
            url = f"{self.api_base_url}/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if "errcode" in data:
                raise RuntimeError(f"WeChat API error: {data.get('errmsg', 'Unknown')}")

            self.access_token = data["access_token"]
            # Cache token for 2 hours (leave 1 minute buffer before expiry)
            self.access_token_expires_at = time.time() + data.get("expires_in", 7200) - 60

            self.logger.info("Successfully obtained WeChat access token")
            return self.access_token

        except Exception as e:
            self.logger.error(f"Failed to get WeChat access token: {e}")
            raise RuntimeError(f"Failed to get WeChat access token: {e}")

    def publish_article(
        self,
        title: str,
        author: str,
        content: str,
        summary: str,
        cover_image_url: Optional[str] = None,
        source_url: Optional[str] = None,
        show_cover: bool = True
    ) -> Dict[str, Any]:
        """Publish an article to WeChat Official Account.

        This creates a news article in the WeChat Official Account.
        The article can include text, images, and links.

        Args:
            title: Article title
            author: Author name
            content: Article content (HTML formatted)
            summary: Article summary/description
            cover_image_url: Cover image URL
            source_url: Original source URL
            show_cover: Whether to show cover image

        Returns:
            Dictionary with publication result:
            {
                "success": bool,
                "media_id": str (if successful),
                "message_id": str (if successful),
                "error": str (if failed)
            }
        """
        try:
            import requests

            access_token = self._get_access_token()

            # Prepare news content
            news_item = {
                "title": title,
                "author": author,
                "digest": summary,
                "show_cover_pic": 1 if show_cover else 0,
                "content": content,
                "content_source_url": source_url or ""
            }

            if cover_image_url:
                thumb_media_id = self._upload_image(cover_image_url, access_token)
                if thumb_media_id:
                    news_item["thumb_media_id"] = thumb_media_id

            # Upload news material
            upload_url = f"{self.api_base_url}/cgi-bin/material/add_news"
            params = {"access_token": access_token, "type": "news"}

            payload = {
                "articles": [news_item]
            }

            response = requests.post(
                upload_url,
                params=params,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if "errcode" in data and data["errcode"] != 0:
                error_msg = data.get("errmsg", "Unknown error")
                self.logger.error(f"WeChat publish error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

            media_id = data.get("media_id")
            self.logger.info(f"Successfully published article to WeChat (media_id: {media_id})")

            return {
                "success": True,
                "media_id": media_id,
                "message_id": media_id
            }

        except Exception as e:
            self.logger.error(f"Error publishing to WeChat: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _upload_image(
        self,
        image_url: str,
        access_token: str
    ) -> Optional[str]:
        """Upload image to WeChat and get media ID.

        Args:
            image_url: URL of the image to upload
            access_token: WeChat API access token

        Returns:
            Media ID of the uploaded image, or None if upload failed
        """
        try:
            import requests
            import io

            # Download image from URL
            img_response = requests.get(image_url, timeout=10)
            img_response.raise_for_status()

            # Upload to WeChat
            upload_url = f"{self.api_base_url}/cgi-bin/material/add_material"
            params = {
                "access_token": access_token,
                "type": "image"
            }

            files = {
                "media": ("image.jpg", io.BytesIO(img_response.content), "image/jpeg")
            }

            response = requests.post(
                upload_url,
                params=params,
                files=files,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if "errcode" in data and data["errcode"] != 0:
                self.logger.warning(f"WeChat image upload error: {data.get('errmsg')}")
                return None

            media_id = data.get("media_id")
            self.logger.info(f"Successfully uploaded image (media_id: {media_id})")

            return media_id

        except Exception as e:
            self.logger.error(f"Error uploading image to WeChat: {e}")
            return None

    def send_message(
        self,
        user_id: str,
        message_type: str = "text",
        content: Optional[str] = None,
        media_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a WeChat user.

        Args:
            user_id: WeChat user ID (openid)
            message_type: Type of message (text, image, news)
            content: Message content (for text messages)
            media_id: Media ID (for image/news messages)

        Returns:
            Dictionary with send result
        """
        try:
            import requests

            access_token = self._get_access_token()

            # Prepare message payload
            if message_type == "text":
                message = {
                    "touser": user_id,
                    "msgtype": "text",
                    "text": {"content": content}
                }
            elif message_type == "image":
                message = {
                    "touser": user_id,
                    "msgtype": "image",
                    "image": {"media_id": media_id}
                }
            elif message_type == "news":
                message = {
                    "touser": user_id,
                    "msgtype": "mpnews",
                    "mpnews": {"media_id": media_id}
                }
            else:
                raise ValueError(f"Unsupported message type: {message_type}")

            # Send message
            send_url = f"{self.api_base_url}/cgi-bin/message/custom/send"
            params = {"access_token": access_token}

            response = requests.post(
                send_url,
                params=params,
                json=message,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get("errcode") != 0:
                error_msg = data.get("errmsg", "Unknown error")
                self.logger.error(f"WeChat message send error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

            self.logger.info(f"Successfully sent message to {user_id}")
            return {
                "success": True,
                "message_id": data.get("msgid")
            }

        except Exception as e:
            self.logger.error(f"Error sending WeChat message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_followers_count(self) -> int:
        """Get the number of followers of the official account.

        Returns:
            Number of followers
        """
        try:
            import requests

            access_token = self._get_access_token()

            # Get user statistics
            url = f"{self.api_base_url}/cgi-bin/user/get"
            params = {
                "access_token": access_token,
                "openid": ""
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            total_followers = data.get("total", 0)

            self.logger.info(f"WeChat followers count: {total_followers}")
            return total_followers

        except Exception as e:
            self.logger.error(f"Error getting WeChat followers count: {e}")
            return 0

    async def publish_article_v2(
        self,
        title: str,
        author: str,
        content: str,
        summary: str,
        cover_image_url: Optional[str] = None,
        source_url: Optional[str] = None,
        show_cover: bool = True,
        is_to_all: bool = True
    ) -> Dict[str, Any]:
        """使用永久素材 API 和群发接口发布文章（推荐方法）

        这是新的推荐发布方式，使用 WeChat 官方支持的永久素材 API。
        优点：
        - WeChat 官方完全支持
        - 素材可永久保存和重复使用
        - 支持更多消息功能
        - 集成了群发统计

        Args:
            title: 文章标题
            author: 作者
            content: 文章内容 (HTML格式)
            summary: 文章摘要
            cover_image_url: 封面图片 URL
            source_url: 原文链接
            show_cover: 是否显示封面
            is_to_all: 是否发送给所有粉丝

        Returns:
            {
                "success": bool,
                "media_id": str,  # 永久素材 ID
                "msg_id": str,    # 群发消息 ID
                "error": str      # 错误信息
            }
        """
        try:
            self.logger.info(f"[V2 API] 发布文章: {title[:30]}...")

            # Step 1: 上传封面图片到永久素材
            image_url = None
            if cover_image_url:
                self.logger.info("Step 1: 上传封面图片...")
                image_url = await self.material_manager.upload_image(cover_image_url)

            # Step 2: 构建图文消息数据
            self.logger.info("Step 2: 构建图文消息...")
            articles = [{
                "title": title,
                "author": author,
                "digest": summary[:140] if summary else content[:140],
                "show_cover_pic": 1 if show_cover else 0,
                "content": content,
                "content_source_url": source_url or ""
            }]

            # 如果上传了图片，添加到数据中
            if image_url:
                articles[0]["thumb_media_id"] = image_url

            # Step 3: 上传图文消息为永久素材
            self.logger.info("Step 3: 上传为永久素材...")
            media_id = await self.material_manager.upload_news_material(articles)

            # Step 4: 通过群发接口发送消息
            self.logger.info("Step 4: 通过群发接口发送...")
            result = await self.message_sender.send_news_message(
                media_id=media_id,
                is_to_all=is_to_all
            )

            if result.get("errcode", 0) != 0:
                raise Exception(f"发送失败: {result.get('errmsg', 'Unknown error')}")

            msg_id = result.get("msg_id")
            self.logger.info(f"✓ 文章发布成功: media_id={media_id}, msg_id={msg_id}")

            return {
                "success": True,
                "media_id": media_id,
                "msg_id": msg_id,
                "message": "Article published successfully using V2 API"
            }

        except Exception as e:
            self.logger.error(f"✗ 发布失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to publish article using V2 API: {str(e)}"
            }

    async def publish_batch_articles(
        self,
        articles: list[Dict[str, Any]],
        is_to_all: bool = True
    ) -> Dict[str, Any]:
        """批量发布多篇文章

        一次发送可包含最多 8 篇文章的图文消息。

        Args:
            articles: 文章列表，每篇包含 title, author, content, summary 等
            is_to_all: 是否发送给所有粉丝

        Returns:
            {
                "success": bool,
                "published_count": int,
                "failed_count": int,
                "media_id": str,
                "msg_id": str,
                "errors": [...]
            }
        """
        try:
            self.logger.info(f"批量发布 {len(articles)} 篇文章...")

            if not articles:
                raise ValueError("文章列表不能为空")

            if len(articles) > 8:
                self.logger.warning(f"文章数超过 8 篇限制，只发布前 8 篇")
                articles = articles[:8]

            # 上传所有文章的封面图片
            articles_data = []
            for idx, article in enumerate(articles, 1):
                self.logger.info(f"  准备文章 {idx}/{len(articles)}: {article['title'][:30]}...")

                article_data = {
                    "title": article["title"],
                    "author": article.get("author", "DeepDive"),
                    "digest": article.get("summary", article.get("content", ""))[:140],
                    "show_cover_pic": 1,
                    "content": article["content"],
                    "content_source_url": article.get("source_url", "")
                }

                # 上传封面图片
                if article.get("cover_image_url"):
                    image_url = await self.material_manager.upload_image(
                        article["cover_image_url"]
                    )
                    if image_url:
                        article_data["thumb_media_id"] = image_url

                articles_data.append(article_data)

            # 上传为永久素材
            self.logger.info("上传为永久素材...")
            media_id = await self.material_manager.upload_news_material(articles_data)

            # 群发
            self.logger.info("群发消息...")
            result = await self.message_sender.send_news_message(
                media_id=media_id,
                is_to_all=is_to_all
            )

            if result.get("errcode", 0) != 0:
                raise Exception(f"群发失败: {result.get('errmsg', 'Unknown error')}")

            msg_id = result.get("msg_id")
            self.logger.info(f"✓ 批量发布成功: {len(articles)} 篇, media_id={media_id}")

            return {
                "success": True,
                "published_count": len(articles),
                "failed_count": 0,
                "media_id": media_id,
                "msg_id": msg_id
            }

        except Exception as e:
            self.logger.error(f"✗ 批量发布失败: {str(e)}")
            return {
                "success": False,
                "published_count": 0,
                "failed_count": len(articles),
                "error": str(e)
            }

    def verify_message_signature(
        self,
        signature: str,
        timestamp: str,
        nonce: str,
        token: str
    ) -> bool:
        """Verify WeChat server message signature.

        This is used to verify that incoming messages are from WeChat.

        Args:
            signature: Signature from WeChat
            timestamp: Timestamp from WeChat
            nonce: Nonce from WeChat
            token: Your token configured in WeChat admin

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Sort parameters
            params = sorted([token, timestamp, nonce])
            # Concatenate
            concat_str = ''.join(params)
            # SHA1 hash
            generated_signature = hashlib.sha1(concat_str.encode()).hexdigest()
            # Compare
            return generated_signature == signature
        except Exception as e:
            self.logger.error(f"Error verifying WeChat signature: {e}")
            return False
