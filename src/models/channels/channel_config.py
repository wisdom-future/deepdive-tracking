"""
渠道配置模型

管理所有发布渠道（WeChat, GitHub, Email）的配置。
支持启用/禁用、动态管理。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base


class ChannelConfig(Base):
    """
    渠道配置模型

    用于存储和管理各个发布渠道的配置。
    """

    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, index=True)

    # 渠道基本信息
    channel_type = Column(String(50), nullable=False, unique=True, index=True)  # wechat, github, email
    channel_name = Column(String(100), nullable=False)  # 显示名称
    description = Column(Text)

    # 配置信息（JSON格式，每个渠道的配置不同）
    config = Column(JSON, nullable=False, default={})

    # 状态控制
    is_enabled = Column(Boolean, default=True, index=True)
    is_configured = Column(Boolean, default=False)

    # 统计信息
    total_published = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    last_publish_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChannelConfig(id={self.id}, channel_type='{self.channel_type}', enabled={self.is_enabled})>"

    def get_config(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default) if self.config else default

    def set_config(self, key: str, value):
        """设置配置值"""
        if not self.config:
            self.config = {}
        self.config[key] = value
        self.updated_at = datetime.utcnow()

    def update_config(self, config_dict: dict):
        """更新整个配置"""
        self.config = config_dict
        self.updated_at = datetime.utcnow()

    def record_publish(self, success: bool):
        """记录发布事件"""
        if success:
            self.total_published += 1
        else:
            self.total_failed += 1
        self.last_publish_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_success_rate(self) -> float:
        """获取发布成功率"""
        total = self.total_published + self.total_failed
        if total == 0:
            return 0.0
        return (self.total_published / total) * 100


class WeChatChannelConfig(Base):
    """
    WeChat渠道配置模型

    用于存储WeChat公众号相关配置。
    """

    __tablename__ = "wechat_channel_configs"

    id = Column(Integer, primary_key=True, index=True)

    # WeChat配置
    app_id = Column(String(255), nullable=False, unique=True)
    app_secret = Column(String(255), nullable=False)  # 生产环境应加密
    account_name = Column(String(100))
    account_description = Column(Text)

    # 发布策略
    publish_style = Column(String(50), default="batch")  # batch 或 single
    max_batch_size = Column(Integer, default=8)  # 单次群发最多8篇
    auto_publish = Column(Boolean, default=False)

    # 状态
    is_verified = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True, index=True)

    # 统计
    total_articles_published = Column(Integer, default=0)
    total_articles_failed = Column(Integer, default=0)
    last_publish_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<WeChatChannelConfig(id={self.id}, account_name='{self.account_name}', enabled={self.is_enabled})>"

    def record_publish(self, success: bool, count: int = 1):
        """记录发布"""
        if success:
            self.total_articles_published += count
        else:
            self.total_articles_failed += count
        self.last_publish_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_publish_stats(self) -> dict:
        """获取发布统计"""
        total = self.total_articles_published + self.total_articles_failed
        success_rate = (self.total_articles_published / total * 100) if total > 0 else 0
        return {
            "total_published": self.total_articles_published,
            "total_failed": self.total_articles_failed,
            "success_rate": success_rate,
            "last_publish_at": self.last_publish_at
        }


class GitHubChannelConfig(Base):
    """
    GitHub渠道配置模型

    用于存储GitHub相关配置。
    """

    __tablename__ = "github_channel_configs"

    id = Column(Integer, primary_key=True, index=True)

    # GitHub配置
    github_token = Column(String(255), nullable=False)  # Personal Access Token
    github_repo = Column(String(255), nullable=False, unique=True)  # username/repo
    github_username = Column(String(100), nullable=False)
    repository_name = Column(String(100))
    repository_description = Column(Text)

    # 本地路径
    local_repo_path = Column(String(500))

    # 发布策略
    auto_commit = Column(Boolean, default=True)
    auto_push = Column(Boolean, default=True)
    create_index = Column(Boolean, default=True)

    # 状态
    is_verified = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True, index=True)

    # 统计
    total_articles_published = Column(Integer, default=0)
    total_articles_failed = Column(Integer, default=0)
    last_publish_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GitHubChannelConfig(id={self.id}, repo='{self.github_repo}', enabled={self.is_enabled})>"

    def record_publish(self, success: bool, count: int = 1):
        """记录发布"""
        if success:
            self.total_articles_published += count
        else:
            self.total_articles_failed += count
        self.last_publish_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_publish_stats(self) -> dict:
        """获取发布统计"""
        total = self.total_articles_published + self.total_articles_failed
        success_rate = (self.total_articles_published / total * 100) if total > 0 else 0
        return {
            "total_published": self.total_articles_published,
            "total_failed": self.total_articles_failed,
            "success_rate": success_rate,
            "last_publish_at": self.last_publish_at
        }


class EmailChannelConfig(Base):
    """
    Email渠道配置模型

    用于存储Email发送相关配置。
    """

    __tablename__ = "email_channel_configs"

    id = Column(Integer, primary_key=True, index=True)

    # Email服务器配置
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)  # 生产环境应加密

    # 发件人信息
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(100), default="DeepDive Tracking")

    # 邮件列表（JSON格式）
    email_list = Column(JSON, default=["hello.junjie.duan@gmail.com"])

    # 邮件策略
    send_digest = Column(Boolean, default=True)  # 是否发送汇总邮件
    send_individual = Column(Boolean, default=False)  # 是否发送单篇文章邮件
    digest_schedule = Column(String(50), default="daily")  # daily, weekly

    # 状态
    is_verified = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True, index=True)

    # 统计
    total_emails_sent = Column(Integer, default=0)
    total_emails_failed = Column(Integer, default=0)
    last_send_at = Column(DateTime)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EmailChannelConfig(id={self.id}, from_email='{self.from_email}', enabled={self.is_enabled})>"

    def get_email_list(self) -> list:
        """获取邮件列表"""
        return self.email_list or ["hello.junjie.duan@gmail.com"]

    def set_email_list(self, emails: list):
        """设置邮件列表"""
        self.email_list = emails
        self.updated_at = datetime.utcnow()

    def add_email(self, email: str) -> bool:
        """添加邮箱"""
        if not self.email_list:
            self.email_list = []
        if email not in self.email_list:
            self.email_list.append(email)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_email(self, email: str) -> bool:
        """移除邮箱"""
        if not self.email_list:
            self.email_list = []
        if email in self.email_list:
            self.email_list.remove(email)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def record_send(self, success: bool, count: int = 1):
        """记录发送"""
        if success:
            self.total_emails_sent += count
        else:
            self.total_emails_failed += count
        self.last_send_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def get_send_stats(self) -> dict:
        """获取发送统计"""
        total = self.total_emails_sent + self.total_emails_failed
        success_rate = (self.total_emails_sent / total * 100) if total > 0 else 0
        return {
            "total_sent": self.total_emails_sent,
            "total_failed": self.total_emails_failed,
            "success_rate": success_rate,
            "last_send_at": self.last_send_at,
            "recipient_count": len(self.get_email_list())
        }
