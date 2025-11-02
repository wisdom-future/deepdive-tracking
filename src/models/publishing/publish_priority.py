"""
发布优先级配置模型

管理各个渠道的发布优先级，允许动态调整发布策略。
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from datetime import datetime
from src.models.base import Base


class PublishPriority(Base):
    """
    发布优先级配置模型

    用于管理各个发布渠道的优先级顺序和发布策略。
    """

    __tablename__ = "publish_priorities"

    id = Column(Integer, primary_key=True, index=True)

    # 渠道配置
    channel = Column(String(50), nullable=False, unique=True, index=True)  # wechat, github, email
    channel_name = Column(String(100), nullable=False)  # 显示名称

    # 优先级配置
    priority = Column(Integer, default=5, index=True)  # 1-10, 越高优先级越高
    is_enabled = Column(Boolean, default=True)  # 是否启用此渠道

    # 发布策略
    auto_publish = Column(Boolean, default=True)  # 是否自动发布
    batch_size = Column(Integer, default=5)  # 批量发布的文章数
    max_retries = Column(Integer, default=3)  # 最大重试次数
    retry_delay_minutes = Column(Integer, default=5)  # 重试延迟（分钟）

    # 时间控制
    publish_time_start = Column(String(5), default="08:00")  # 发布开始时间 (HH:MM)
    publish_time_end = Column(String(5), default="22:00")  # 发布结束时间 (HH:MM)
    publish_on_weekends = Column(Boolean, default=True)  # 周末是否发布

    # 限流配置
    max_per_day = Column(Integer)  # 每天最多发布数 (None=无限)
    max_per_hour = Column(Integer)  # 每小时最多发布数 (None=无限)

    # 内容过滤
    min_score = Column(Integer, default=30)  # 最低评分阈值
    allowed_categories = Column(JSON, default=None)  # 允许的分类 (None=全部)
    blocked_keywords = Column(JSON, default=[])  # 阻止的关键词

    # 渠道特定配置
    channel_config = Column(JSON, default={})  # 渠道特定的配置

    # 统计信息
    total_published = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)
    last_publish_at = Column(DateTime)

    # 元数据
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PublishPriority(channel='{self.channel}', priority={self.priority}, enabled={self.is_enabled})>"

    def is_time_to_publish(self) -> bool:
        """检查当前时间是否允许发布"""
        from datetime import datetime as dt, time

        now = dt.now()

        # 检查周末
        if now.weekday() >= 5 and not self.publish_on_weekends:  # 周六和周日
            return False

        # 检查时间范围
        current_time = now.time()
        start = time.fromisoformat(self.publish_time_start)
        end = time.fromisoformat(self.publish_time_end)

        if not (start <= current_time <= end):
            return False

        return True

    def get_channel_config(self, key: str, default=None):
        """获取渠道特定配置"""
        if not self.channel_config:
            return default
        return self.channel_config.get(key, default)

    def set_channel_config(self, key: str, value):
        """设置渠道特定配置"""
        if not self.channel_config:
            self.channel_config = {}
        self.channel_config[key] = value
        self.updated_at = datetime.utcnow()

    def get_success_rate(self) -> float:
        """获取发布成功率"""
        total = self.total_published + self.total_failed
        if total == 0:
            return 0.0
        return (self.total_published / total) * 100
