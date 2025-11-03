#!/usr/bin/env python3
"""
Test Review Service - 测试内容审核服务

功能：
  - 创建内容审核记录
  - 测试审核工作流 (批准、拒绝、请求编辑)
  - 显示审核统计
"""

import sys
from pathlib import Path
import io

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import ProcessedNews
from src.services.review_service import ReviewService

def main():
    """Main test function"""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "=" * 80)
    print("Test Review Service")
    print("=" * 80)
    print()

    try:
        # [1] 获取已评分的文章
        print("[1] 查询已评分的文章...")
        processed_articles = session.query(ProcessedNews).filter(
            ProcessedNews.id > 0
        ).limit(5).all()

        if not processed_articles:
            print("    没有已评分的文章")
            return 0

        print(f"    找到 {len(processed_articles)} 条已评分的文章")
        print()

        # [2] 初始化审核服务
        print("[2] 初始化审核服务...")
        review_service = ReviewService(session)
        print("    OK - 服务就绪")
        print()

        # [3] 创建审核记录
        print("[3] 创建审核记录...")
        reviews = []
        for idx, article in enumerate(processed_articles, 1):
            try:
                review = review_service.create_review(article.id)
                reviews.append(review)
                print(f"    [{idx}] 为文章 {article.id} 创建审核记录 {review.id}")
            except Exception as e:
                print(f"    [{idx}] 错误: {str(e)[:60]}")

        print()

        # [4] 测试审核工作流
        print("[4] 测试审核工作流...")
        print()

        if len(reviews) >= 1:
            print("    [A] 批准第一条审核")
            review = review_service.approve_review(
                reviews[0].id,
                reviewer_name="test_reviewer",
                reviewer_confidence=0.95,
                reviewer_tags=["quality_high"]
            )
            print(f"        状态: {review.status}")
            print(f"        审核人: {review.reviewed_by}")
            print()

        if len(reviews) >= 2:
            print("    [B] 拒绝第二条审核")
            review = review_service.reject_review(
                reviews[1].id,
                reviewer_name="test_reviewer",
                review_notes="Content quality too low",
                reason="quality"
            )
            print(f"        状态: {review.status}")
            print(f"        原因: {review.reviewer_tags}")
            print()

        if len(reviews) >= 3:
            print("    [C] 请求编辑第三条审核")
            review = review_service.request_edit(
                reviews[2].id,
                editor_notes="Please improve the summary",
                editor_name="test_editor"
            )
            print(f"        状态: {review.status}")
            print(f"        编辑说明: {review.editor_notes}")
            print()

        if len(reviews) >= 4:
            print("    [D] 提交编辑第四条审核")
            review = review_service.submit_edits(
                reviews[3].id,
                title_edited="Improved Title",
                summary_pro_edited="Improved professional summary",
                editor_name="test_editor"
            )
            print(f"        状态: {review.status}")
            print(f"        编辑标题: {review.title_edited}")
            print()

        # [5] 获取审核统计
        print("[5] 审核统计")
        print("=" * 80)
        stats = review_service.get_review_stats()
        print(f"  总审核数: {stats['total']}")
        print(f"  待审核: {stats['pending']}")
        print(f"  已批准: {stats['approved']}")
        print(f"  已拒绝: {stats['rejected']}")
        print(f"  批准率: {stats['approval_rate']:.1f}%")
        print()

        # [6] 获取待审核的审核
        print("[6] 待审核的内容")
        print("=" * 80)
        pending_reviews = review_service.get_pending_reviews(limit=5)
        print(f"  找到 {len(pending_reviews)} 条待审核的内容")
        for review in pending_reviews[:3]:
            print(f"    - 审核ID: {review.id}, 状态: {review.status}")
        print()

        print("=" * 80)
        print("审核服务测试完成!")
        print("=" * 80)
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
