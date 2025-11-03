"""
优先级发布工作流 E2E 测试

测试发布优先级功能：
1. 加载发布优先级配置
2. 按优先级顺序发布到 Email -> GitHub -> WeChat
3. 验证发布结果
4. 支持 dry-run 模式

使用方式:
    python scripts/tests/test_publishing_priority.py [article_limit] [--dry-run]

示例:
    python scripts/tests/test_publishing_priority.py 5
    python scripts/tests/test_publishing_priority.py 5 --dry-run
"""

import sys
import asyncio
import logging
from typing import Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0].replace('scripts', ''))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import get_settings
from src.models import Base, PublishPriority
from src.services.workflow.priority_publishing_workflow import PriorityPublishingWorkflow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_priority_publishing_test(
    article_limit: int = 5,
    dry_run: bool = False,
    wechat_config: Optional[dict] = None,
    github_config: Optional[dict] = None,
    email_config: Optional[dict] = None,
):
    """
    运行优先级发布工作流 E2E 测试

    Args:
        article_limit: 最多发布的文章数
        dry_run: 是否为试运行模式
        wechat_config: WeChat 配置
        github_config: GitHub 配置
        email_config: Email 配置
    """

    # 获取设置和创建数据库连接
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logger.info("=" * 80)
        logger.info("优先级发布工作流 E2E 测试")
        logger.info("=" * 80)

        # 检查发布优先级配置
        priority_count = session.query(PublishPriority).count()
        if priority_count == 0:
            logger.warning("❌ 还没有配置任何发布优先级")
            logger.info("请先运行初始化脚本:")
            logger.info("  python scripts/init_publish_priorities.py")
            return

        logger.info(f"✓ 已加载 {priority_count} 个发布优先级配置")
        logger.info("")

        # 显示优先级配置
        priorities = (
            session.query(PublishPriority)
            .order_by(PublishPriority.priority.desc())
            .all()
        )

        logger.info("📋 发布优先级顺序（从高到低）：")
        for idx, priority in enumerate(priorities, 1):
            status = "✅" if priority.is_enabled else "❌"
            logger.info(
                f"  {idx}. {status} {priority.channel_name.upper()} "
                f"- 优先级 {priority.priority}/10 "
                f"(最低评分: {priority.min_score})"
            )
        logger.info("")

        # 创建工作流实例
        workflow = PriorityPublishingWorkflow(db_session=session)

        # 配置发布渠道
        logger.info("🔧 配置发布渠道...")

        # 使用提供的配置或默认配置
        if email_config is None:
            email_config = {
                "smtp_host": settings.smtp_host,
                "smtp_port": settings.smtp_port,
                "smtp_user": settings.smtp_user,
                "smtp_password": settings.smtp_password,
                "from_email": settings.smtp_from_email,
                "from_name": settings.smtp_from_name,
                "email_list": settings.email_list,
            }

        if github_config is None:
            github_config = {
                "token": settings.github_token,
                "repo": settings.github_repo,
                "username": settings.github_username,
                "local_path": settings.github_local_path,
            }

        if wechat_config is None:
            wechat_config = {
                "app_id": settings.wechat_app_id,
                "app_secret": settings.wechat_app_secret,
            }

        # 配置所有渠道 - 仅配置有完整凭证的渠道
        valid_email_config = email_config if all([
            email_config.get("smtp_host"),
            email_config.get("smtp_user"),
            email_config.get("smtp_password")
        ]) else None

        valid_github_config = github_config if all([
            github_config.get("token"),
            github_config.get("repo")
        ]) else None

        valid_wechat_config = wechat_config if all([
            wechat_config.get("app_id"),
            wechat_config.get("app_secret")
        ]) else None

        workflow.configure_channels(
            email_config=valid_email_config,
            github_config=valid_github_config,
            wechat_config=valid_wechat_config,
        )

        # 检查是否有任何配置
        if not any([valid_email_config, valid_github_config, valid_wechat_config]):
            logger.warning("⚠️  没有任何发布渠道的凭证被完全配置")
            logger.info("请在 .env 文件中配置以下环境变量:")
            logger.info("  - Email: SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL")
            logger.info("  - GitHub: GITHUB_TOKEN, GITHUB_REPO")
            logger.info("  - WeChat: WECHAT_APP_ID, WECHAT_APP_SECRET")
            logger.info("")
            logger.info("自动切换到 dry-run 模式...")
            dry_run = True

        logger.info("✓ 所有渠道已配置")
        logger.info("")

        # 执行发布工作流
        logger.info("▶️  执行优先级发布工作流...")
        logger.info("")

        mode = "🔍 Dry-Run 模式 (不实际发布)" if dry_run else "📤 实际发布模式"
        logger.info(f"模式: {mode}")
        logger.info(f"文章限制: {article_limit} 篇")
        logger.info("")

        result = await workflow.execute(
            article_limit=article_limit,
            dry_run=dry_run,
        )

        # 显示结果
        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 发布结果")
        logger.info("=" * 80)

        if result.get("success"):
            logger.info("✅ 工作流执行成功")
        else:
            logger.error(f"❌ 工作流执行失败: {result.get('error', '未知错误')}")

        if result.get("channels_executed"):
            logger.info(f"\n🎯 已执行的渠道: {len(result['channels_executed'])} 个")
            for channel in result["channels_executed"]:
                channel_result = result.get("articles_by_channel", {}).get(channel, {})
                published_count = channel_result.get("published_count", 0)
                failed_count = channel_result.get("failed_count", 0)
                logger.info(
                    f"  ✓ {channel.upper()}: "
                    f"{published_count} 篇成功, {failed_count} 篇失败"
                )
        else:
            logger.warning("⚠️  没有任何渠道被执行")

        logger.info(f"\n📈 总发布数: {result.get('total_published', 0)} 篇")
        logger.info("=" * 80)

        # 显示详细信息
        if result.get("articles_by_channel"):
            logger.info("\n📝 各渠道详细结果:")
            for channel, channel_result in result["articles_by_channel"].items():
                logger.info(f"\n  【{channel.upper()}】")
                logger.info(f"    发布数: {channel_result.get('published_count', 0)}")
                logger.info(f"    失败数: {channel_result.get('failed_count', 0)}")
                if channel_result.get("message"):
                    logger.info(f"    信息: {channel_result['message']}")
                if channel_result.get("error"):
                    logger.error(f"    错误: {channel_result['error']}")

        logger.info("")
        logger.info("✅ 优先级发布工作流 E2E 测试完成")

    except Exception as e:
        logger.error(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


def main():
    """主函数，解析命令行参数"""
    article_limit = 5
    dry_run = False

    # 解析命令行参数
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--dry-run":
            dry_run = True
        elif arg.isdigit():
            article_limit = int(arg)

    logger.info(f"参数: article_limit={article_limit}, dry_run={dry_run}")

    # 运行测试
    asyncio.run(
        run_priority_publishing_test(
            article_limit=article_limit,
            dry_run=dry_run,
        )
    )


if __name__ == "__main__":
    main()
