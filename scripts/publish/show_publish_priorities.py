"""
查看发布优先级配置

显示所有已配置的发布优先级和它们的设置。
"""

import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0].replace('scripts', ''))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from src.models import PublishPriority

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def show_publish_priorities():
    """显示发布优先级配置"""

    # 获取设置和创建数据库连接
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logger.info("=" * 100)
        logger.info("发布优先级配置")
        logger.info("=" * 100)

        # 查询所有优先级配置，按优先级排序
        priorities = (
            session.query(PublishPriority)
            .order_by(PublishPriority.priority.desc())
            .all()
        )

        if not priorities:
            logger.info("❌ 还没有配置任何发布优先级")
            logger.info("请先运行: python scripts/init_publish_priorities.py")
            return

        for idx, priority in enumerate(priorities, 1):
            status = "✅ 启用" if priority.is_enabled else "❌ 禁用"
            auto = "自动" if priority.auto_publish else "手动"

            logger.info("")
            logger.info(f"[{idx}] {priority.channel_name.upper()} - 优先级 {priority.priority}/10")
            logger.info(f"    状态: {status} ({auto}发布)")
            logger.info(f"    描述: {priority.description or '(无描述)'}")
            logger.info("")
            logger.info(f"    📊 发布统计:")
            logger.info(f"       • 总成功: {priority.total_published} 篇")
            logger.info(f"       • 总失败: {priority.total_failed} 篇")
            if priority.last_publish_at:
                logger.info(
                    f"       • 最后发布时间: {priority.last_publish_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                logger.info(f"       • 最后发布时间: 从未发布")
            success_rate = priority.get_success_rate()
            logger.info(f"       • 成功率: {success_rate:.1f}%")
            logger.info("")

            logger.info(f"    ⚙️  发布策略:")
            logger.info(f"       • 批量大小: {priority.batch_size} 篇/批")
            logger.info(f"       • 最大重试: {priority.max_retries} 次")
            logger.info(f"       • 重试延迟: {priority.retry_delay_minutes} 分钟")
            logger.info("")

            logger.info(f"    🕐 时间控制:")
            logger.info(f"       • 发布时间: {priority.publish_time_start} - {priority.publish_time_end}")
            weekends = "允许" if priority.publish_on_weekends else "不允许"
            logger.info(f"       • 周末发布: {weekends}")
            logger.info("")

            logger.info(f"    🔒 限流配置:")
            daily = f"{priority.max_per_day} 篇/天" if priority.max_per_day else "无限制"
            hourly = f"{priority.max_per_hour} 篇/小时" if priority.max_per_hour else "无限制"
            logger.info(f"       • 每日限制: {daily}")
            logger.info(f"       • 每小时限制: {hourly}")
            logger.info("")

            logger.info(f"    📝 内容过滤:")
            logger.info(f"       • 最低评分: {priority.min_score}")
            if priority.allowed_categories:
                categories = ", ".join(priority.allowed_categories)
                logger.info(f"       • 允许分类: {categories}")
            else:
                logger.info(f"       • 允许分类: 全部")
            if priority.blocked_keywords:
                keywords = ", ".join(priority.blocked_keywords)
                logger.info(f"       • 阻止关键词: {keywords}")
            else:
                logger.info(f"       • 阻止关键词: 无")
            logger.info("")

            if priority.channel_config:
                logger.info(f"    🎯 渠道特定配置:")
                for key, value in priority.channel_config.items():
                    logger.info(f"       • {key}: {value}")
                logger.info("")

        logger.info("=" * 100)
        logger.info(f"总计: {len(priorities)} 个发布渠道已配置")
        logger.info("=" * 100)

    except Exception as e:
        logger.error(f"✗ 查询失败: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    show_publish_priorities()
