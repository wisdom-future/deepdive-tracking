"""Publishing channel integrations.

This package contains integrations with various publishing channels:
- WeChat Official Account (微信公众号) - Fully implemented
- XiaoHongShu (小红书) - Planned for Phase 4
- Website (网站) - Planned for Phase 4
- Email (邮件) - Planned for Phase 4

Architecture:
    channels/
    ├── wechat/              # WeChat Official Account implementation
    │   ├── __init__.py
    │   ├── wechat_channel.py        # Main publisher (V1+V2 APIs)
    │   ├── wechat_material_manager.py   # Permanent material management
    │   └── wechat_message_sender.py     # Mass messaging
    ├── xiaohongshu/         # XiaoHongShu (placeholder)
    ├── web/                 # Website direct publishing (placeholder)
    └── __init__.py          # This file

Each channel can be developed and tested independently.
"""

from src.services.channels.wechat import WeChatPublisher

__all__ = ["WeChatPublisher"]
