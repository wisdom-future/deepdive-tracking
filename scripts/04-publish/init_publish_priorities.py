"""
初始化发布优先级配置

设置默认的发布优先级：
- Email: 优先级 10 (最高)
- GitHub: 优先级 9
- WeChat: 优先级 8 (最低)
"""

import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0].replace('scripts', ''))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from src.models import Base, PublishPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_publish_priorities():
    """初始化发布优先级配置"""

    # 获取设置和创建数据库连接
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logger.info("=" * 80)
        logger.info("初始化发布优先级配置")
        logger.info("=" * 80)

        # 检查是否已经存在优先级配置
        existing_count = session.query(PublishPriority).count()
        if existing_count > 0:
            logger.info(f"✓ 已存在 {existing_count} 条优先级配置")
            logger.info("清除现有配置...")
            session.query(PublishPriority).delete()
            session.commit()

        # Email - 优先级 10 (最高)
        email_priority = PublishPriority(
            channel="email",
            channel_name="Email",
            priority=10,
            is_enabled=True,
            auto_publish=True,
            batch_size=5,
            max_retries=3,
            retry_delay_minutes=5,
            publish_time_start="08:00",
            publish_time_end="22:00",
            publish_on_weekends=True,
            max_per_day=50,
            max_per_hour=10,
            min_score=30,
            allowed_categories=None,  # 允许所有分类
            blocked_keywords=[],
            channel_config={
                "send_summary": True,
                "include_source_url": True,
                "batch_name_format": "DeepDive Daily - {date}"
            },
            total_published=0,
            total_failed=0,
            description="Email 优先级最高，第一个发布渠道"
        )

        # GitHub - 优先级 9
        github_priority = PublishPriority(
            channel="github",
            channel_name="GitHub",
            priority=9,
            is_enabled=True,
            auto_publish=True,
            batch_size=10,
            max_retries=3,
            retry_delay_minutes=5,
            publish_time_start="08:00",
            publish_time_end="22:00",
            publish_on_weekends=False,  # 工作日发布
            max_per_day=100,
            max_per_hour=None,
            min_score=25,
            allowed_categories=None,
            blocked_keywords=[],
            channel_config={
                "auto_create_issues": False,
                "create_discussions": True,
                "labels": ["ai", "news", "deepdive"],
                "branch_format": "news/{date}"
            },
            total_published=0,
            total_failed=0,
            description="GitHub 优先级次高，第二个发布渠道"
        )

        # WeChat - 优先级 8 (最低)
        wechat_priority = PublishPriority(
            channel="wechat",
            channel_name="WeChat",
            priority=8,
            is_enabled=True,
            auto_publish=True,
            batch_size=5,
            max_retries=2,
            retry_delay_minutes=10,
            publish_time_start="09:00",
            publish_time_end="21:00",
            publish_on_weekends=True,
            max_per_day=30,
            max_per_hour=5,
            min_score=40,  # 微信要求更高的评分
            allowed_categories=None,
            blocked_keywords=["nsfw", "adult"],
            channel_config={
                "show_cover_image": True,
                "enable_comments": True,
                "message_type": "news"
            },
            total_published=0,
            total_failed=0,
            description="WeChat 优先级最低，第三个发布渠道"
        )

        # 添加到数据库
        session.add(email_priority)
        session.add(github_priority)
        session.add(wechat_priority)
        session.commit()

        logger.info("✓ 优先级配置已初始化")
        logger.info("")
        logger.info("发布优先级顺序（从高到低）：")
        logger.info("  1️⃣  Email (优先级 10) - 最高优先级，第一个发布")
        logger.info("  2️⃣  GitHub (优先级 9) - 次高优先级，第二个发布")
        logger.info("  3️⃣  WeChat (优先级 8) - 最低优先级，第三个发布")
        logger.info("")
        logger.info("每个渠道的配置已设置，可通过以下方式查看：")
        logger.info("  python scripts/show_publish_priorities.py")
        logger.info("")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"✗ 初始化失败: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_publish_priorities()
