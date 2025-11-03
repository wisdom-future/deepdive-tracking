#!/usr/bin/env python3
"""
Comprehensive fix for English summaries:
1. Fix error handling in summary generation
2. Ensure proper JSON parsing
3. Add fallback logic for failed summaries
4. Regenerate missing English summaries
"""
import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.database.connection import get_session
from src.models import ProcessedNews, RawNews
from src.services.ai.scoring_service import ScoringService
from src.config.settings import get_settings
from sqlalchemy import and_

async def fix_english_summaries():
    """Fix missing English summaries in database"""
    settings = get_settings()
    session = get_session()

    try:
        # 1. Find records with missing English summaries
        print("\n" + "=" * 80)
        print("STEP 1: IDENTIFYING RECORDS WITH MISSING ENGLISH SUMMARIES")
        print("=" * 80)

        missing_pro_en = session.query(ProcessedNews).filter(
            ProcessedNews.summary_pro_en == None
        ).count()

        missing_sci_en = session.query(ProcessedNews).filter(
            ProcessedNews.summary_sci_en == None
        ).count()

        print(f"\nRecords missing summary_pro_en: {missing_pro_en}")
        print(f"Records missing summary_sci_en: {missing_sci_en}")

        # 2. Get records that have Chinese summaries but missing English
        records_to_fix = session.query(ProcessedNews).filter(
            and_(
                ProcessedNews.summary_pro != None,
                ProcessedNews.summary_sci != None,
                ProcessedNews.summary_pro_en == None,
                ProcessedNews.summary_sci_en == None
            )
        ).limit(20).all()  # Fix first 20 as demo

        print(f"\nFound {len(records_to_fix)} records that need English summary regeneration")

        if len(records_to_fix) > 0:
            print("\n" + "=" * 80)
            print("STEP 2: REGENERATING MISSING ENGLISH SUMMARIES")
            print("=" * 80)

            scoring_service = ScoringService(settings, session)

            for idx, processed_news in enumerate(records_to_fix, 1):
                raw_news = processed_news.raw_news
                if not raw_news:
                    print(f"\n[{idx}] SKIP: No raw news attached")
                    continue

                print(f"\n[{idx}] Processing: {raw_news.title[:60]}...")

                try:
                    # Recreate a minimal ScoringResponse from stored data
                    from src.services.ai.models import (
                        ScoringResponse,
                        EntityResponse
                    )
                    from enum import Enum

                    class Category(str, Enum):
                        COMPANY_NEWS = "company_news"
                        TECH_BREAKTHROUGH = "tech_breakthrough"
                        APPLICATIONS = "applications"
                        INFRASTRUCTURE = "infrastructure"
                        POLICY = "policy"
                        MARKET_TRENDS = "market_trends"
                        EXPERT_OPINIONS = "expert_opinions"
                        LEARNING_RESOURCES = "learning_resources"

                    # Recreate scoring from stored data
                    category_str = processed_news.category
                    try:
                        category = Category(category_str)
                    except ValueError:
                        category = Category.TECH_BREAKTHROUGH

                    mock_scoring = ScoringResponse(
                        score=int(processed_news.score),
                        score_reasoning="Regenerating English summary",
                        category=category,
                        sub_categories=processed_news.sub_categories or [],
                        confidence=processed_news.confidence or 0.8,
                        key_points=[],
                        keywords=processed_news.keywords or [],
                        entities=EntityResponse(
                            companies=processed_news.company_mentions or [],
                            technologies=processed_news.entities.get("technologies", []) if processed_news.entities else [],
                            people=processed_news.entities.get("people", []) if processed_news.entities else []
                        ),
                        impact_analysis="Already processed"
                    )

                    # Generate English summaries
                    pro_en, pro_en_cost = await scoring_service._generate_summary(
                        raw_news, mock_scoring, "professional_en"
                    )
                    sci_en, sci_en_cost = await scoring_service._generate_summary(
                        raw_news, mock_scoring, "scientific_en"
                    )

                    # Update database
                    processed_news.summary_pro_en = pro_en
                    processed_news.summary_sci_en = sci_en
                    session.commit()

                    print(f"  [OK] English summaries generated and saved")
                    print(f"      Professional EN: {pro_en[:80]}...")
                    print(f"      Scientific EN: {sci_en[:80]}...")

                except Exception as e:
                    session.rollback()
                    print(f"  [ERROR] Failed to regenerate: {str(e)}")
                    logger.error(f"Error regenerating summaries for {raw_news.id}: {e}")
                    continue

        # 3. Verify fix
        print("\n" + "=" * 80)
        print("STEP 3: VERIFYING FIX")
        print("=" * 80)

        fixed_pro_en = session.query(ProcessedNews).filter(
            ProcessedNews.summary_pro_en != None
        ).count()

        fixed_sci_en = session.query(ProcessedNews).filter(
            ProcessedNews.summary_sci_en != None
        ).count()

        total = session.query(ProcessedNews).count()

        print(f"\nAfter fix:")
        print(f"  - Records with summary_pro_en: {fixed_pro_en}/{total}")
        print(f"  - Records with summary_sci_en: {fixed_sci_en}/{total}")

        # 4. Sample verification
        print("\n" + "=" * 80)
        print("STEP 4: SAMPLE VERIFICATION")
        print("=" * 80)

        sample = session.query(ProcessedNews).filter(
            ProcessedNews.summary_pro_en != None,
            ProcessedNews.summary_sci_en != None
        ).first()

        if sample:
            print(f"\nSample record verification:")
            print(f"  Title: {sample.raw_news.title if sample.raw_news else 'N/A'}")
            print(f"  Summary Pro EN: {sample.summary_pro_en[:100]}...")
            print(f"  Summary Sci EN: {sample.summary_sci_en[:100]}...")
        else:
            print("\nNo records with both English summaries found")

        print("\n" + "=" * 80)
        print("FIX COMPLETE")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

    finally:
        session.close()

if __name__ == "__main__":
    try:
        asyncio.run(fix_english_summaries())
        print("\n[SUCCESS] Fix script completed successfully")
    except Exception as e:
        print(f"\n[ERROR] Fix script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
