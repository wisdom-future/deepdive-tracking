#!/usr/bin/env python3
"""
数据源查看和管理脚本

显示当前配置的所有新闻数据源，以及可以如何修改它们。
"""

import sys
import os
from pathlib import Path
import io

# Set UTF-8 encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import DataSource


def print_header(title):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_source(idx, source):
    """Print a single data source."""
    status = "✅ 启用" if source.is_enabled else "❌ 禁用"
    source_type = source.type.upper()

    print(f"{idx}. {source.name}")
    print(f"   │")
    print(f"   ├─ 状态: {status}")
    print(f"   ├─ 类型: {source_type}")
    if source.url:
        print(f"   ├─ URL: {source.url}")
    print(f"   ├─ 优先级: {source.priority}/10 (越高越优先)")
    print(f"   ├─ 刷新间隔: 每 {source.refresh_interval} 分钟一次")
    print(f"   ├─ 单次最多采集: {source.max_items_per_run} 条新闻")

    # 显示统计信息
    if source.last_check_at:
        print(f"   ├─ 最后检查: {source.last_check_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if source.last_success_at:
        print(f"   ├─ 最后成功: {source.last_success_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if source.last_error:
        print(f"   ├─ 最后错误: {source.last_error[:60]}...")

    print(f"   ├─ 错误次数: {source.error_count}")
    print(f"   ├─ 连续失败: {source.consecutive_failures}")

    # 显示配置
    if source.description:
        print(f"   └─ 描述: {source.description}")
    else:
        print(f"   └─ 描述: (无)")


def main():
    """Main function."""
    print_header("DeepDive Tracking - 新闻数据源管理")

    # Initialize settings and database
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query all data sources
        all_sources = session.query(DataSource).all()
        enabled_sources = session.query(DataSource).filter(DataSource.is_enabled == True).all()

        print(f"数据源统计:")
        print(f"  • 总数: {len(all_sources)}")
        print(f"  • 启用: {len(enabled_sources)}")
        print(f"  • 禁用: {len(all_sources) - len(enabled_sources)}")
        print()

        if not all_sources:
            print("❌ 数据库中没有配置任何数据源\n")
            print("如需添加数据源，请运行:")
            print("  python scripts/init_review_tables.py\n")
            return 1

        # Show enabled sources
        print_header("✅ 已启用的数据源 (共 %d 个)" % len(enabled_sources))

        if enabled_sources:
            for idx, source in enumerate(enabled_sources, 1):
                print_source(idx, source)
                print()
        else:
            print("暂无启用的数据源\n")

        # Show disabled sources
        disabled_sources = [s for s in all_sources if not s.is_enabled]
        if disabled_sources:
            print_header("❌ 已禁用的数据源 (共 %d 个)" % len(disabled_sources))

            for idx, source in enumerate(disabled_sources, 1):
                print_source(idx, source)
                print()

        # Show instructions
        print_header("📖 如何使用这些数据源")

        print("1️⃣  查看数据源详细配置:")
        print("   运行此脚本会显示上述信息\n")

        print("2️⃣  启用/禁用数据源:")
        print("   可以在数据库中修改 is_enabled 字段\n")

        print("3️⃣  修改数据源参数:")
        print("   - priority: 采集优先级 (1-10)")
        print("   - refresh_interval: 刷新间隔 (分钟)")
        print("   - max_items_per_run: 单次最多采集条数\n")

        print("4️⃣  运行采集:")
        print("   python scripts/01-collection/collect_news.py\n")

        print("5️⃣  查看采集结果:")
        print("   python scripts/show-top-news.py\n")

        # Show data source types
        print_header("📝 支持的数据源类型")

        print("支持以下类型的数据源:")
        print("  • rss: RSS Feed (最常用)")
        print("  • crawler: 网页爬虫 (需配置 CSS 选择器)")
        print("  • api: API 接口 (需配置请求参数)")
        print("  • twitter: Twitter (需配置认证令牌)")
        print("  • email: 电子邮件 (需配置 IMAP 认证)\n")

        # Show current database info
        print_header("⚙️  数据库配置")

        print(f"数据库连接: {settings.database_url}")
        print(f"数据库表: raw_news, data_sources\n")

        print("数据源的字段说明:")
        print("  • name: 数据源名称")
        print("  • type: 数据源类型 (rss/crawler/api/twitter/email)")
        print("  • url: 数据源 URL 或 API 端点")
        print("  • priority: 优先级 (1-10, 10最高)")
        print("  • refresh_interval: 刷新间隔 (分钟)")
        print("  • max_items_per_run: 单次最多采集条数")
        print("  • is_enabled: 是否启用 (true/false)")
        print("  • tags: 标签 (JSON 格式，可选)")
        print("  • default_author: 默认作者 (可选)\n")

        return 0

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
