"""
渠道管理服务

提供统一的接口来管理所有发布渠道的配置。
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from src.models import (
    ChannelConfig,
    WeChatChannelConfig,
    GitHubChannelConfig,
    EmailChannelConfig
)

logger = logging.getLogger(__name__)


class ChannelManager:
    """渠道管理服务"""

    def __init__(self, db_session: Session):
        """
        初始化渠道管理器

        Args:
            db_session: SQLAlchemy 数据库会话
        """
        self.db_session = db_session
        self.logger = logger

    # ============ 通用渠道配置管理 ============

    def get_all_channels(self) -> List[ChannelConfig]:
        """获取所有渠道配置"""
        return self.db_session.query(ChannelConfig).all()

    def get_enabled_channels(self) -> List[ChannelConfig]:
        """获取所有启用的渠道"""
        return self.db_session.query(ChannelConfig).filter(
            ChannelConfig.is_enabled == True
        ).all()

    def get_channel_by_type(self, channel_type: str) -> Optional[ChannelConfig]:
        """按类型获取渠道配置"""
        return self.db_session.query(ChannelConfig).filter(
            ChannelConfig.channel_type == channel_type
        ).first()

    def enable_channel(self, channel_type: str) -> ChannelConfig:
        """启用渠道"""
        channel = self.get_channel_by_type(channel_type)
        if not channel:
            raise ValueError(f"Channel {channel_type} not found")
        channel.is_enabled = True
        self.db_session.commit()
        self.logger.info(f"✓ 渠道已启用: {channel_type}")
        return channel

    def disable_channel(self, channel_type: str) -> ChannelConfig:
        """禁用渠道"""
        channel = self.get_channel_by_type(channel_type)
        if not channel:
            raise ValueError(f"Channel {channel_type} not found")
        channel.is_enabled = False
        self.db_session.commit()
        self.logger.info(f"✓ 渠道已禁用: {channel_type}")
        return channel

    def get_channel_status(self, channel_type: str) -> Dict[str, Any]:
        """获取渠道状态"""
        channel = self.get_channel_by_type(channel_type)
        if not channel:
            raise ValueError(f"Channel {channel_type} not found")

        return {
            "type": channel.channel_type,
            "name": channel.channel_name,
            "enabled": channel.is_enabled,
            "configured": channel.is_configured,
            "total_published": channel.total_published,
            "total_failed": channel.total_failed,
            "success_rate": channel.get_success_rate(),
            "last_publish_at": channel.last_publish_at
        }

    def get_all_channels_status(self) -> Dict[str, Any]:
        """获取所有渠道状态"""
        channels = self.get_all_channels()
        status = {}
        for channel in channels:
            status[channel.channel_type] = {
                "name": channel.channel_name,
                "enabled": channel.is_enabled,
                "configured": channel.is_configured,
                "total_published": channel.total_published,
                "total_failed": channel.total_failed,
                "success_rate": channel.get_success_rate(),
                "last_publish_at": channel.last_publish_at
            }
        return status

    # ============ WeChat渠道管理 ============

    def get_wechat_configs(self) -> List[WeChatChannelConfig]:
        """获取所有WeChat配置"""
        return self.db_session.query(WeChatChannelConfig).all()

    def get_enabled_wechat_configs(self) -> List[WeChatChannelConfig]:
        """获取所有启用的WeChat配置"""
        return self.db_session.query(WeChatChannelConfig).filter(
            WeChatChannelConfig.is_enabled == True
        ).all()

    def create_wechat_config(
        self,
        app_id: str,
        app_secret: str,
        account_name: str,
        account_description: Optional[str] = None,
        publish_style: str = "batch",
        max_batch_size: int = 8,
        auto_publish: bool = False
    ) -> WeChatChannelConfig:
        """创建WeChat配置"""
        # 检查是否已存在
        existing = self.db_session.query(WeChatChannelConfig).filter(
            WeChatChannelConfig.app_id == app_id
        ).first()
        if existing:
            raise ValueError(f"WeChat config with app_id {app_id} already exists")

        config = WeChatChannelConfig(
            app_id=app_id,
            app_secret=app_secret,
            account_name=account_name,
            account_description=account_description,
            publish_style=publish_style,
            max_batch_size=max_batch_size,
            auto_publish=auto_publish
        )

        self.db_session.add(config)
        self.db_session.commit()
        self.logger.info(f"✓ WeChat配置已创建: {account_name}")
        return config

    def update_wechat_config(self, config_id: int, **kwargs) -> WeChatChannelConfig:
        """更新WeChat配置"""
        config = self.db_session.query(WeChatChannelConfig).filter(
            WeChatChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"WeChat config {config_id} not found")

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.db_session.commit()
        self.logger.info(f"✓ WeChat配置已更新: {config.account_name}")
        return config

    # ============ GitHub渠道管理 ============

    def get_github_configs(self) -> List[GitHubChannelConfig]:
        """获取所有GitHub配置"""
        return self.db_session.query(GitHubChannelConfig).all()

    def get_enabled_github_configs(self) -> List[GitHubChannelConfig]:
        """获取所有启用的GitHub配置"""
        return self.db_session.query(GitHubChannelConfig).filter(
            GitHubChannelConfig.is_enabled == True
        ).all()

    def create_github_config(
        self,
        github_token: str,
        github_repo: str,
        github_username: str,
        repository_name: Optional[str] = None,
        repository_description: Optional[str] = None,
        local_repo_path: Optional[str] = None,
        auto_commit: bool = True,
        auto_push: bool = True,
        create_index: bool = True
    ) -> GitHubChannelConfig:
        """创建GitHub配置"""
        # 检查是否已存在
        existing = self.db_session.query(GitHubChannelConfig).filter(
            GitHubChannelConfig.github_repo == github_repo
        ).first()
        if existing:
            raise ValueError(f"GitHub config for repo {github_repo} already exists")

        config = GitHubChannelConfig(
            github_token=github_token,
            github_repo=github_repo,
            github_username=github_username,
            repository_name=repository_name or github_repo.split('/')[-1],
            repository_description=repository_description,
            local_repo_path=local_repo_path,
            auto_commit=auto_commit,
            auto_push=auto_push,
            create_index=create_index
        )

        self.db_session.add(config)
        self.db_session.commit()
        self.logger.info(f"✓ GitHub配置已创建: {github_repo}")
        return config

    def update_github_config(self, config_id: int, **kwargs) -> GitHubChannelConfig:
        """更新GitHub配置"""
        config = self.db_session.query(GitHubChannelConfig).filter(
            GitHubChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"GitHub config {config_id} not found")

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.db_session.commit()
        self.logger.info(f"✓ GitHub配置已更新: {config.github_repo}")
        return config

    # ============ Email渠道管理 ============

    def get_email_configs(self) -> List[EmailChannelConfig]:
        """获取所有Email配置"""
        return self.db_session.query(EmailChannelConfig).all()

    def get_enabled_email_configs(self) -> List[EmailChannelConfig]:
        """获取所有启用的Email配置"""
        return self.db_session.query(EmailChannelConfig).filter(
            EmailChannelConfig.is_enabled == True
        ).all()

    def create_email_config(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: str = "DeepDive Tracking",
        email_list: Optional[List[str]] = None,
        send_digest: bool = True,
        send_individual: bool = False,
        digest_schedule: str = "daily"
    ) -> EmailChannelConfig:
        """创建Email配置"""
        config = EmailChannelConfig(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=from_name,
            email_list=email_list or ["hello.junjie.duan@gmail.com"],
            send_digest=send_digest,
            send_individual=send_individual,
            digest_schedule=digest_schedule
        )

        self.db_session.add(config)
        self.db_session.commit()
        self.logger.info(f"✓ Email配置已创建: {from_email}")
        return config

    def update_email_config(self, config_id: int, **kwargs) -> EmailChannelConfig:
        """更新Email配置"""
        config = self.db_session.query(EmailChannelConfig).filter(
            EmailChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"Email config {config_id} not found")

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.db_session.commit()
        self.logger.info(f"✓ Email配置已更新: {config.from_email}")
        return config

    def add_email_to_list(self, config_id: int, email: str) -> bool:
        """添加邮箱到列表"""
        config = self.db_session.query(EmailChannelConfig).filter(
            EmailChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"Email config {config_id} not found")

        if config.add_email(email):
            self.db_session.commit()
            self.logger.info(f"✓ 邮箱已添加: {email}")
            return True
        return False

    def remove_email_from_list(self, config_id: int, email: str) -> bool:
        """从列表移除邮箱"""
        config = self.db_session.query(EmailChannelConfig).filter(
            EmailChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"Email config {config_id} not found")

        if config.remove_email(email):
            self.db_session.commit()
            self.logger.info(f"✓ 邮箱已移除: {email}")
            return True
        return False

    def get_email_list(self, config_id: int) -> List[str]:
        """获取邮件列表"""
        config = self.db_session.query(EmailChannelConfig).filter(
            EmailChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"Email config {config_id} not found")
        return config.get_email_list()

    def set_email_list(self, config_id: int, emails: List[str]):
        """设置邮件列表"""
        config = self.db_session.query(EmailChannelConfig).filter(
            EmailChannelConfig.id == config_id
        ).first()
        if not config:
            raise ValueError(f"Email config {config_id} not found")
        config.set_email_list(emails)
        self.db_session.commit()
        self.logger.info(f"✓ 邮件列表已更新: {len(emails)} 个邮箱")

    # ============ 统计和报告 ============

    def get_channel_stats(self, channel_type: str) -> Dict[str, Any]:
        """获取渠道统计"""
        if channel_type == "wechat":
            configs = self.get_wechat_configs()
            return {
                "channel": "WeChat",
                "config_count": len(configs),
                "enabled_count": len([c for c in configs if c.is_enabled]),
                "total_published": sum(c.total_articles_published for c in configs),
                "total_failed": sum(c.total_articles_failed for c in configs)
            }
        elif channel_type == "github":
            configs = self.get_github_configs()
            return {
                "channel": "GitHub",
                "config_count": len(configs),
                "enabled_count": len([c for c in configs if c.is_enabled]),
                "total_published": sum(c.total_articles_published for c in configs),
                "total_failed": sum(c.total_articles_failed for c in configs)
            }
        elif channel_type == "email":
            configs = self.get_email_configs()
            return {
                "channel": "Email",
                "config_count": len(configs),
                "enabled_count": len([c for c in configs if c.is_enabled]),
                "total_sent": sum(c.total_emails_sent for c in configs),
                "total_failed": sum(c.total_emails_failed for c in configs),
                "total_recipients": sum(len(c.get_email_list()) for c in configs)
            }
        else:
            raise ValueError(f"Unknown channel type: {channel_type}")

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有渠道的统计"""
        return {
            "wechat": self.get_channel_stats("wechat"),
            "github": self.get_channel_stats("github"),
            "email": self.get_channel_stats("email")
        }
