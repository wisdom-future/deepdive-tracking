"""
WeChat 媒体缓存模型

用于存储通过 WeChat 永久素材 API 上传的媒体信息。
这样可以避免重复上传相同的媒体，提高发布效率。

Fields:
- id: 主键
- media_id: WeChat 永久素材的 media_id (唯一)
- content_id: 关联的已发布内容 ID
- type: 媒体类型 (image, news, video, voice)
- media_url: 媒体的 URL 或本地路径
- file_hash: 文件 MD5 哈希（用于去重）
- upload_time: 上传时间
- expire_time: 过期时间（如果有）
- is_deleted: 是否已删除
- created_at: 创建时间
- updated_at: 更新时间
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base


class WeChatMediaCache(Base):
    """WeChat 媒体缓存表"""

    __tablename__ = "wechat_media_cache"

    id = Column(Integer, primary_key=True, index=True)

    # WeChat 媒体信息
    media_id = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(String(20), nullable=False, default="image")  # image, news, video, voice
    media_url = Column(Text, nullable=True)

    # 关联信息
    content_id = Column(Integer, ForeignKey("published_content.id"), nullable=True, index=True)

    # 去重相关
    file_hash = Column(String(32), nullable=True, index=True)  # MD5 hash of original file

    # 时间信息
    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    expire_time = Column(DateTime, nullable=True)  # WeChat 永久素材不过期，但字段留作扩展

    # 状态
    is_deleted = Column(Boolean, default=False, nullable=False)

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<WeChatMediaCache("
            f"id={self.id}, "
            f"media_id={self.media_id}, "
            f"type={self.type}, "
            f"is_deleted={self.is_deleted}"
            f")>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "media_id": self.media_id,
            "type": self.type,
            "media_url": self.media_url,
            "content_id": self.content_id,
            "file_hash": self.file_hash,
            "upload_time": self.upload_time.isoformat() if self.upload_time else None,
            "expire_time": self.expire_time.isoformat() if self.expire_time else None,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
