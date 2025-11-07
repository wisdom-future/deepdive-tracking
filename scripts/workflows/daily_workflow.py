#!/usr/bin/env python3
"""
Daily Workflow Orchestration - 每日自动化工作流
执行顺序：数据采集 → AI评分 → 邮件发送 → GitHub发布
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_daily_workflow():
    """执行完整的每日工作流"""

    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("DEEPDIVE TRACKING - DAILY WORKFLOW STARTED")
    logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    results = {
        "start_time": start_time,
        "steps": [],
        "success": True
    }

    # Step 1: 数据采集
    logger.info("\n[STEP 1/4] Data Collection - 数据采集")
    logger.info("-" * 80)

    try:
        from src.services.collection.collection_manager import CollectionManager
        from src.database.connection import get_session

        session = get_session()
        manager = CollectionManager(session)

        collection_result = await manager.collect_all()

        logger.info(f"✅ Collection completed:")
        logger.info(f"   - Total collected: {collection_result['total_collected']}")
        logger.info(f"   - New items: {collection_result['total_new']}")
        logger.info(f"   - Duplicates: {collection_result['total_duplicates']}")

        results["steps"].append({
            "step": "collection",
            "success": True,
            "data": collection_result
        })

        session.close()

    except Exception as e:
        logger.error(f"❌ Collection failed: {e}", exc_info=True)
        results["steps"].append({
            "step": "collection",
            "success": False,
            "error": str(e)
        })
        results["success"] = False

    # Step 2: AI评分处理
    logger.info("\n[STEP 2/4] AI Scoring - AI评分处理")
    logger.info("-" * 80)

    try:
        # Import AI scoring module
        from scripts.ai.score_news import main as score_news

        scoring_result = await score_news()

        logger.info(f"✅ AI Scoring completed:")
        logger.info(f"   - Processed: {scoring_result.get('processed', 0)}")
        logger.info(f"   - High scores (>80): {scoring_result.get('high_scores', 0)}")

        results["steps"].append({
            "step": "scoring",
            "success": True,
            "data": scoring_result
        })

    except Exception as e:
        logger.error(f"❌ AI Scoring failed: {e}", exc_info=True)
        results["steps"].append({
            "step": "scoring",
            "success": False,
            "error": str(e)
        })
        # 即使评分失败，也继续发送（可能有历史数据）

    # Step 3: 邮件发送
    logger.info("\n[STEP 3/4] Email Publishing - 邮件发送")
    logger.info("-" * 80)

    try:
        from scripts.publish.send_top_news_email import main as send_email

        email_result = await send_email()

        if email_result:
            logger.info(f"✅ Email sent successfully")
            results["steps"].append({
                "step": "email",
                "success": True
            })
        else:
            logger.warning(f"⚠️ Email sending returned False")
            results["steps"].append({
                "step": "email",
                "success": False,
                "error": "Email function returned False"
            })

    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}", exc_info=True)
        results["steps"].append({
            "step": "email",
            "success": False,
            "error": str(e)
        })
        results["success"] = False

    # Step 4: GitHub发布
    logger.info("\n[STEP 4/4] GitHub Publishing - GitHub发布")
    logger.info("-" * 80)

    try:
        from scripts.publish.send_top_ai_news_to_github import main as publish_github

        github_result = await publish_github()

        if github_result:
            logger.info(f"✅ GitHub publishing completed")
            results["steps"].append({
                "step": "github",
                "success": True
            })
        else:
            logger.warning(f"⚠️ GitHub publishing returned False")
            results["steps"].append({
                "step": "github",
                "success": False,
                "error": "GitHub function returned False"
            })

    except Exception as e:
        logger.error(f"❌ GitHub publishing failed: {e}", exc_info=True)
        results["steps"].append({
            "step": "github",
            "success": False,
            "error": str(e)
        })
        # GitHub失败不影响整体成功状态

    # 总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("DAILY WORKFLOW COMPLETED")
    logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Overall Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")
    logger.info("=" * 80)

    # 打印步骤总结
    logger.info("\nSteps Summary:")
    for step in results["steps"]:
        status = "✅" if step["success"] else "❌"
        logger.info(f"  {status} {step['step']}")

    return results


if __name__ == "__main__":
    try:
        result = asyncio.run(run_daily_workflow())

        # 返回非零退出码如果失败
        sys.exit(0 if result["success"] else 1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ Workflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
