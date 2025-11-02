"""
WeChat 官方账号发布渠道集成

支持：
- 永久素材 API (Material API) - 媒体上传和管理
- 客服消息 API (Customer Service API) - 消息群发
- 旧版本 news.add API (已弃用，仅供参考)

主要组件：
- WeChatPublisher: 主发布器类
- WeChatMaterialManager: 媒体管理器
- WeChatMessageSender: 消息发送器

使用示例：
    from src.services.channels.wechat import WeChatPublisher

    publisher = WeChatPublisher(app_id, app_secret)
    result = await publisher.publish_article_v2(
        title="article title",
        author="author name",
        content="article content",
        summary="summary"
    )
"""

from src.services.channels.wechat.wechat_channel import WeChatPublisher
from src.services.channels.wechat.wechat_material_manager import WeChatMaterialManager
from src.services.channels.wechat.wechat_message_sender import WeChatMessageSender

__all__ = [
    "WeChatPublisher",
    "WeChatMaterialManager",
    "WeChatMessageSender",
]
