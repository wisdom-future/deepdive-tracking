"""
邮件配置模型

管理邮件发送的配置和邮件列表。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from src.models.base import Base


class EmailConfig(Base):
    """
    邮件配置模型

    用于存储和管理邮件发送的配置信息。
    """

    __tablename__ = "email_configs"

    id = Column(Integer, primary_key=True, index=True)

    # 基本配置
    name = Column(String(100), nullable=False, unique=True)
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, default=587)
    smtp_user = Column(String(255), nullable=False)
    smtp_password = Column(String(255), nullable=False)  # 在生产环境应加密

    # 发件人信息
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(100), default="DeepDive Tracking")

    # 邮件列表（JSON格式）
    email_list = Column(JSON, default=["hello.junjie.duan@gmail.com"])

    # 是否启用
    is_enabled = Column(Boolean, default=True)

    # 备注
    description = Column(Text)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EmailConfig(id={self.id}, name='{self.name}', emails={len(self.email_list)})>"

    def get_email_list(self):
        """获取邮件列表"""
        return self.email_list or ["hello.junjie.duan@gmail.com"]

    def set_email_list(self, emails):
        """设置邮件列表"""
        self.email_list = emails
        self.updated_at = datetime.utcnow()

    def add_email(self, email):
        """添加邮箱到列表"""
        if not self.email_list:
            self.email_list = []
        if email not in self.email_list:
            self.email_list.append(email)
            self.updated_at = datetime.utcnow()
            return True
        return False

    def remove_email(self, email):
        """从列表移除邮箱"""
        if not self.email_list:
            self.email_list = []
        if email in self.email_list:
            self.email_list.remove(email)
            self.updated_at = datetime.utcnow()
            return True
        return False
