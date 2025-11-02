"""WeChat (微信) publishing channel integration."""

import logging
import json
from typing import Optional, Dict, Any
import hashlib
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class WeChatPublisher:
    """WeChat Official Account Publishing Integration.

    This class handles publishing content to WeChat Official Accounts (微信公众号)
    using the WeChat API.
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
