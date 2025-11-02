"""Publishing channel integrations.

This package contains integrations with various publishing channels:
- WeChat Official Account (微信公众号)
- XiaoHongShu (小红书)
- Website (网站)
"""

from src.services.channels.wechat_channel import WeChatPublisher

__all__ = ["WeChatPublisher"]
