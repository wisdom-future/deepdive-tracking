"""
WeChat 客服消息发送器

提供客服消息 API 的完整实现，支持：
- 发送图文消息给粉丝
- 发送文本消息
- 发送图片消息
- 群发消息
- 获取发送统计

参考文档: https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Service_Center_messages.html
"""

import aiohttp
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class WeChatMessageSender:
    """WeChat 客服消息发送器"""

    API_BASE = "https://api.weixin.qq.com"
    TOKEN_CACHE_BUFFER = 60

    def __init__(self, app_id: str, app_secret: str):
        """
        初始化消息发送器

        Args:
            app_id: WeChat 公众号 App ID
            app_secret: WeChat 公众号 App Secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """获取 access_token"""
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
                    self._token_expires = datetime.now() + timedelta(seconds=7200 - self.TOKEN_CACHE_BUFFER)
                    logger.info(f"✓ 成功获取 token")
                    return self._token

        except Exception as e:
            logger.error(f"✗ 获取 token 失败: {str(e)}")
            raise

    async def send_news_message(
        self,
        media_id: str,
        is_to_all: bool = True,
        touser: Optional[str] = None,
        tag_id: Optional[int] = None
    ) -> Dict:
        """
        群发图文消息

        通过群发接口发送使用永久素材 API 上传的图文消息。

        Args:
            media_id: 图文消息的 media_id（来自永久素材 API）
            is_to_all: 是否发送给所有粉丝 (True) 或指定对象 (False)
            touser: 指定接收的粉丝 openid (以 | 分隔)
            tag_id: 指定接收的标签 ID

        Returns:
            Dict: 包含 msg_id (消息 ID) 和其他返回值

        Raises:
            Exception: 发送失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/message/mass/send?access_token={token}"

        try:
            logger.info(f"发送图文消息: media_id={media_id}, is_to_all={is_to_all}")

            payload = {
                "msgtype": "news",
                "news": {"media_id": media_id}
            }

            # 指定发送对象
            if is_to_all:
                payload["touser"] = "@all"
            elif touser:
                payload["touser"] = touser
            elif tag_id is not None:
                payload["tag"] = tag_id
            else:
                raise ValueError("必须指定 is_to_all=True 或提供 touser/tag_id")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    msg_id = result.get("msg_id")
                    logger.info(f"✓ 图文消息发送成功: msg_id={msg_id}")
                    return result

        except Exception as e:
            logger.error(f"✗ 发送图文消息失败: {str(e)}")
            raise

    async def send_text_message(
        self,
        content: str,
        is_to_all: bool = True,
        touser: Optional[str] = None,
        tag_id: Optional[int] = None
    ) -> Dict:
        """
        群发文本消息

        Args:
            content: 文本内容
            is_to_all: 是否发送给所有粉丝
            touser: 指定接收的粉丝 openid
            tag_id: 指定接收的标签 ID

        Returns:
            Dict: 包含 msg_id 和其他返回值

        Raises:
            Exception: 发送失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/message/mass/send?access_token={token}"

        try:
            logger.info(f"发送文本消息: 内容={content[:30]}...")

            payload = {
                "msgtype": "text",
                "text": {"content": content}
            }

            if is_to_all:
                payload["touser"] = "@all"
            elif touser:
                payload["touser"] = touser
            elif tag_id is not None:
                payload["tag"] = tag_id
            else:
                raise ValueError("必须指定 is_to_all=True 或提供 touser/tag_id")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    msg_id = result.get("msg_id")
                    logger.info(f"✓ 文本消息发送成功: msg_id={msg_id}")
                    return result

        except Exception as e:
            logger.error(f"✗ 发送文本消息失败: {str(e)}")
            raise

    async def send_image_message(
        self,
        media_id: str,
        is_to_all: bool = True,
        touser: Optional[str] = None,
        tag_id: Optional[int] = None
    ) -> Dict:
        """
        群发图片消息

        Args:
            media_id: 图片的 media_id
            is_to_all: 是否发送给所有粉丝
            touser: 指定接收的粉丝 openid
            tag_id: 指定接收的标签 ID

        Returns:
            Dict: 包含 msg_id 和其他返回值

        Raises:
            Exception: 发送失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/message/mass/send?access_token={token}"

        try:
            logger.info(f"发送图片消息: media_id={media_id}")

            payload = {
                "msgtype": "image",
                "image": {"media_id": media_id}
            }

            if is_to_all:
                payload["touser"] = "@all"
            elif touser:
                payload["touser"] = touser
            elif tag_id is not None:
                payload["tag"] = tag_id
            else:
                raise ValueError("必须指定 is_to_all=True 或提供 touser/tag_id")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    msg_id = result.get("msg_id")
                    logger.info(f"✓ 图片消息发送成功: msg_id={msg_id}")
                    return result

        except Exception as e:
            logger.error(f"✗ 发送图片消息失败: {str(e)}")
            raise

    async def get_send_stats(self, msg_id: str) -> Dict:
        """
        获取群发消息的发送统计

        Args:
            msg_id: 群发消息的 msg_id

        Returns:
            Dict: 包含发送统计信息

        Raises:
            Exception: 获取失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/message/get_mass_send_status?access_token={token}"

        try:
            logger.info(f"获取消息统计: msg_id={msg_id}")

            payload = {"msg_id": msg_id}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    logger.info(f"✓ 获取消息统计成功")
                    return result

        except Exception as e:
            logger.error(f"✗ 获取消息统计失败: {str(e)}")
            raise

    async def delete_mass_message(self, msg_id: str) -> bool:
        """
        删除已群发的消息

        群发消息发送成功后，仍可以删除（删除后粉丝无法再看到）。

        Args:
            msg_id: 群发消息的 msg_id

        Returns:
            bool: 是否删除成功

        Raises:
            Exception: 删除失败
        """
        token = await self._get_access_token()
        url = f"{self.API_BASE}/cgi-bin/message/mass/delete?access_token={token}"

        try:
            logger.info(f"删除群发消息: msg_id={msg_id}")

            payload = {"msg_id": msg_id}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    logger.info(f"✓ 群发消息删除成功")
                    return True

        except Exception as e:
            logger.error(f"✗ 删除群发消息失败: {str(e)}")
            raise

    async def send_template_message(
        self,
        openid: str,
        template_id: str,
        data: Dict,
        url: Optional[str] = None
    ) -> str:
        """
        发送模板消息

        这是另一种发送方式，相对于群发更灵活，但需要用户主动订阅。

        Args:
            openid: 用户 openid
            template_id: 模板 ID
            data: 模板数据
            url: 点击消息后的跳转链接

        Returns:
            str: 消息 ID

        Raises:
            Exception: 发送失败
        """
        token = await self._get_access_token()
        url_api = f"{self.API_BASE}/cgi-bin/message/template/send?access_token={token}"

        try:
            logger.info(f"发送模板消息: openid={openid}, template_id={template_id}")

            payload = {
                "touser": openid,
                "template_id": template_id,
                "data": data
            }

            if url:
                payload["url"] = url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url_api,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    result = await resp.json()

                    if "errcode" in result and result["errcode"] != 0:
                        raise Exception(f"WeChat API Error: {result.get('errmsg', 'Unknown error')}")

                    msg_id = result.get("msgid")
                    logger.info(f"✓ 模板消息发送成功: msg_id={msg_id}")
                    return msg_id

        except Exception as e:
            logger.error(f"✗ 发送模板消息失败: {str(e)}")
            raise
