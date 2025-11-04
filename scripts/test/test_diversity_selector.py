#!/usr/bin/env python3
"""
Test Diversity Selector - 测试多样性选择器

测试新的多样性感知选择逻辑是否正常工作
"""

import sys
import io
import json
from pathlib import Path

# 修复 Windows 编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.connection import get_session
from src.services.selection import DiversityAwareSelector


def main():
    """Test diversity selector"""
    print("\n" + "="*80)
    print("Diversity Selector Test")
    print("="*80)
    print()

    session = get_session()

    try:
        # Test with current data
        print("[1] Testing with current database...")
        selector = DiversityAwareSelector(session)

        selected, report = selector.select_top_articles(
            limit=10,
            min_raw_score=60.0,
            diversity_decay=0.85
        )

        print(f"\n[OK] Selection completed successfully!")
        print()

        # Display summary
        print("="*80)
        print("SELECTION SUMMARY")
        print("="*80)
        print()

        summary = report['summary']
        print(f"Total candidates:      {summary['total_candidates']}")
        print(f"Selected:              {summary['selected']}")
        print(f"Unique sources (all):  {summary['unique_sources_in_candidates']}")
        print(f"Unique sources (top):  {summary['unique_sources_in_selected']}")
        print(f"Diversity achieved:    {'✅ YES' if summary['diversity_achieved'] else '❌ NO'}")
        print()

        # Source distribution
        print("="*80)
        print("SOURCE DISTRIBUTION")
        print("="*80)
        print()

        source_dist = report['source_distribution']
        for source, count in sorted(source_dist.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * count
            print(f"{source:30} {bar} ({count})")
        print()

        # Quality metrics
        print("="*80)
        print("QUALITY METRICS")
        print("="*80)
        print()

        metrics = report['quality_metrics']
        print(f"Raw Score:")
        print(f"  Mean:  {metrics['raw_score_mean']:.2f}")
        print(f"  Range: {metrics['raw_score_min']:.2f} - {metrics['raw_score_max']:.2f}")
        print()

        print(f"Normalized Score:")
        print(f"  Mean:  {metrics['normalized_score_mean']:.2f}")
        print(f"  Range: {metrics['normalized_score_min']:.2f} - {metrics['normalized_score_max']:.2f}")
        print()

        # Selected articles
        print("="*80)
        print("SELECTED ARTICLES (TOP 10)")
        print("="*80)
        print()

        for idx, article_info in enumerate(report['selected_articles'], 1):
            print(f"{idx:2}. {article_info['title'][:60]}")
            print(f"    Source: {article_info['source']}")
            print(f"    Raw Score: {article_info['raw_score']:.1f}")
            print(f"    Normalized: {article_info['normalized_score']:.2f}")
            print(f"    Final: {article_info['final_score']:.2f} (diversity: {article_info['diversity_factor']:.2f})")
            print()

        # Source statistics
        print("="*80)
        print("SOURCE STATISTICS (ALL CANDIDATES)")
        print("="*80)
        print()

        source_stats = report['source_stats']
        print(f"{'Source':30} {'Count':>6} {'Mean':>8} {'Std':>8} {'Range':>15}")
        print("-" * 80)

        for source, stats in sorted(
            source_stats.items(),
            key=lambda x: x[1]['mean'],
            reverse=True
        ):
            print(
                f"{source:30} "
                f"{stats['count']:>6} "
                f"{stats['mean']:>8.2f} "
                f"{stats['std']:>8.2f} "
                f"{stats['range']:>15}"
            )
        print()

        # Save report
        report_file = project_root / "logs" / "test_diversity_selector.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"[OK] Full report saved to: {report_file}")
        print()

        # Analysis
        print("="*80)
        print("ANALYSIS")
        print("="*80)
        print()

        if summary['unique_sources_in_selected'] == 1:
            print("⚠️  WARNING: All selected articles come from a single source!")
            print("    This indicates:")
            print("    1. Not enough scored articles from other sources")
            print("    2. Need to score more articles to enable diversity")
            print()
        elif summary['unique_sources_in_selected'] < 3:
            print("⚠️  WARNING: Low source diversity")
            print(f"    Only {summary['unique_sources_in_selected']} different sources")
            print("    Recommendation: Score more articles")
            print()
        else:
            print("✅ Good source diversity achieved!")
            print(f"   {summary['unique_sources_in_selected']} different sources")
            print()

        # Check if OpenAI dominates
        openai_count = source_dist.get('OpenAI Blog', 0)
        openai_pct = (openai_count / len(selected) * 100) if selected else 0

        if openai_pct > 80:
            print(f"⚠️  WARNING: OpenAI content dominates ({openai_pct:.0f}%)")
            print("    Recommendation: Score more articles from other sources")
            print()
        elif openai_pct > 50:
            print(f"⚠️  OpenAI content is over-represented ({openai_pct:.0f}%)")
            print("    But diversity selector is working to limit it")
            print()
        else:
            print(f"✅ OpenAI content is balanced ({openai_pct:.0f}%)")
            print()

        print("="*80)
        print("TEST COMPLETED")
        print("="*80)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
