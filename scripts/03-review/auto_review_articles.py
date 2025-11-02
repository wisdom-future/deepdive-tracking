#!/usr/bin/env python3
"""
Automatic Review Service - 自动审核已评分文章

功能：
  - 自动审核评分>=50分的文章（可配置）
  - 批量处理待审核的文章
  - 显示审核统计和处理结果
"""

import sys
from pathlib import Path
import io
from datetime import datetime

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import ProcessedNews, ContentReview, RawNews
from src.services.workflow.auto_review_workflow import AutoReviewWorkflow

def main():
    """Main test function"""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "="*80)
    print("DeepDive Tracking - Auto Review Articles")
    print("="*80)
    print()

    try:
        # [1] 查询待评分的文章
        print("[1] 查询待审核的文章...")
        pending_reviews = session.query(ContentReview).filter(
            ContentReview.status.in_(["pending", "needs_edit"])
        ).all()

        if not pending_reviews:
            print("    没有待审核的文章")
            # Try to create reviews for unreviewed articles
            print("\n[1.5] 为已评分的文章创建审核记录...")
            processed_articles = session.query(ProcessedNews).filter(
                ~ProcessedNews.id.in_(
                    session.query(ContentReview.processed_news_id).all()
                )
            ).limit(10).all()

            if processed_articles:
                print(f"    找到 {len(processed_articles)} 条无审核记录的已评分文章")
            else:
                print("    没有需要审核的文章")
                return 0

        print(f"    找到 {len(pending_reviews)} 条待审核的文章")
        print()

        # [2] 初始化工作流
        print("[2] 初始化自动审核工作流...")
        workflow = AutoReviewWorkflow(session)
        print("    OK - 工作流就绪")
        print()

        # [3] 执行自动审核工作流
        print("[3] 执行自动审核工作流...")
        print("    配置: score_threshold=50, max_reviews=100")
        print()

        start_time = datetime.utcnow()
        result = workflow.execute(
            score_threshold=50,
            max_reviews=100
        )
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        print()

        # [4] 显示自动审核结果
        print("[4] 工作流执行结果")
        print("="*80)
        if result['success']:
            print(f"  ✅ 执行成功")
            print(f"  自动批准: {result['approved_count']}")
            print(f"  跳过处理: {result['skipped_count']}")
            print(f"  处理时间: {duration:.2f}秒")
        else:
            print(f"  ❌ 执行失败")
            print(f"  错误: {result.get('error', 'Unknown error')}")
            return 1
        print()

        # [5] 获取审核统计
        print("[5] 审核统计")
        print("="*80)
        stats = result['stats']
        print(f"  总审核数: {stats['total']}")
        print(f"  待审核: {stats['pending']}")
        print(f"  已批准: {stats['approved']}")
        print(f"  已拒绝: {stats['rejected']}")
        print(f"  自动批准: {stats['auto_approved']}")
        print(f"  批准率: {stats['approval_rate']:.1f}%")
        print()

        # [6] 显示已批准的文章样本
        print("[6] 已批准的文章样本 (最近5条)")
        print("="*80)
        approved_reviews = session.query(ContentReview).filter(
            ContentReview.status == "approved"
        ).order_by(ContentReview.reviewed_at.desc()).limit(5).all()

        for idx, review in enumerate(approved_reviews, 1):
            processed_news = session.query(ProcessedNews).filter(
                ProcessedNews.id == review.processed_news_id
            ).first()

            if processed_news:
                # Get raw news for title
                raw_news = session.query(RawNews).filter(
                    RawNews.id == processed_news.raw_news_id
                ).first()

                title = raw_news.title[:60] if raw_news else "Unknown"
                print(f"  [{idx}] {title}...")
                print(f"      审核ID: {review.id}, 分数: {processed_news.score}, 审核人: {review.reviewed_by}")
                if review.reviewer_tags:
                    print(f"      标签: {', '.join(review.reviewer_tags)}")
        print()

        print("="*80)
        print("自动审核完成!")
        print("="*80)
        print()

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
