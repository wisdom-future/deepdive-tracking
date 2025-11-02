#!/usr/bin/env python3
"""
真实的数据采集脚本 - 需要真实的PostgreSQL数据库运行

使用方法:
    1. 启动数据库: docker-compose up -d
    2. 运行迁移: alembic upgrade head
    3. 运行采集: python scripts/run_collection.py

这个脚本会:
    - 连接到真实的PostgreSQL数据库
    - 采集真实的AI新闻
    - 保存到数据库
    - 显示采集结果供你检查
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings
from src.models.base import Base
from src.models import DataSource, RawNews
from src.services.collection import CollectionManager


async def main():
    """主采集流程"""
    settings = get_settings()

    print("\n" + "=" * 80)
    print("DeepDive Tracking - Real Data Collection")
    print("=" * 80)

    # 1. 连接数据库
    print("\n[1] 连接到PostgreSQL数据库...")
    try:
        engine = create_engine(
            settings.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20
        )

        # 测试连接
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        print(f"    OK - Connected to {settings.database_url}")
    except Exception as e:
        print(f"    ERROR - 无法连接数据库: {e}")
        print("\n    请确保:")
        print("    1. PostgreSQL 已启动: docker-compose up -d")
        print("    2. 数据库迁移已完成: alembic upgrade head")
        print("    3. 环境变量正确设置")
        return

    # 2. 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 3. 检查数据源配置
        print("\n[2] 检查数据源配置...")
        sources = session.query(DataSource).filter(DataSource.is_enabled == True).all()

        if not sources:
            print("    WARNING - 没有启用的数据源")
            print("    正在创建默认数据源...")

            default_sources = [
                DataSource(
                    name="OpenAI Blog",
                    type="rss",
                    url="https://openai.com/blog/rss.xml",
                    priority=10,
                    is_enabled=True,
                    max_items_per_run=10
                ),
                DataSource(
                    name="Anthropic News",
                    type="rss",
                    url="https://www.anthropic.com/news/rss.xml",
                    priority=10,
                    is_enabled=True,
                    max_items_per_run=10
                ),
            ]

            for source in default_sources:
                session.add(source)
                print(f"    + {source.name}")

            session.commit()
            sources = default_sources
        else:
            print(f"    OK - Found {len(sources)} enabled sources:")
            for source in sources:
                print(f"    + {source.name} ({source.type})")

        # 4. 运行采集
        print("\n[3] 开始采集数据...")
        print(f"    时间: {datetime.now().isoformat()}")
        print("    (这可能需要30-60秒)\n")

        manager = CollectionManager(session)
        stats = await manager.collect_all()

        # 5. 显示采集结果
        print("\n[4] 采集结果统计")
        print("=" * 80)
        print(f"总采集数量: {stats['total_collected']}")
        print(f"新增数量:   {stats['total_new']}")
        print(f"重复数量:   {stats['total_duplicates']}")

        if stats['errors']:
            print(f"\n错误信息:")
            for error in stats['errors']:
                print(f"  - {error}")

        print(f"\n按数据源分布:")
        for source_name, source_stats in stats['by_source'].items():
            if isinstance(source_stats, dict):
                collected = source_stats.get('collected', 0)
                new = source_stats.get('new', 0)
                duplicates = source_stats.get('duplicates', 0)
                print(f"  {source_name}:")
                print(f"    采集: {collected}, 新增: {new}, 重复: {duplicates}")

        # 6. 显示采集到的数据样本
        print("\n[5] 采集到的数据样本 (最新10条)")
        print("=" * 80)

        recent_news = (
            session.query(RawNews)
            .order_by(RawNews.published_at.desc())
            .limit(10)
            .all()
        )

        if recent_news:
            for idx, news in enumerate(recent_news, 1):
                print(f"\n{idx}. [{news.status}] {news.title}")
                print(f"   来源: {news.source_name}")
                print(f"   URL: {news.url}")
                print(f"   发布时间: {news.published_at}")
                print(f"   采集时间: {news.fetched_at}")
                if news.content:
                    preview = (news.content[:150] + "...") if len(news.content) > 150 else news.content
                    print(f"   摘要: {preview}")
        else:
            print("未采集到任何数据")
            print("可能原因:")
            print("  - 网络连接问题")
            print("  - RSS源暂时不可用")
            print("  - RSS解析失败")

        # 7. 数据库查询指南
        print("\n[6] 如何查询数据库中的数据")
        print("=" * 80)
        print("\n使用PostgreSQL客户端连接:")
        print(f"  psql -h localhost -U deepdive -d deepdive_db\n")

        print("查询采集的新闻:")
        print("""
  -- 查看所有采集的新闻
  SELECT id, title, source_name, status, published_at
  FROM raw_news
  ORDER BY published_at DESC;

  -- 查看特定来源的新闻
  SELECT * FROM raw_news WHERE source_name = 'OpenAI Blog';

  -- 查看统计信息
  SELECT source_name, COUNT(*) as count,
         COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates
  FROM raw_news
  GROUP BY source_name;
""")

        # 8. 下一步
        print("\n[7] 下一步操作")
        print("=" * 80)
        print("现在你有了真实采集的数据:")
        print("  1. 数据已保存在PostgreSQL数据库")
        print("  2. 可以查询验证采集结果")
        print("  3. 准备进行AI评分和分类")
        print("  4. 准备发布到各渠道")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        session.close()
        print("\n" + "=" * 80)
        print("采集完成")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
