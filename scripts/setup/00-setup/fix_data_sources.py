#!/usr/bin/env python3
"""
Fix Data Sources - 修复无效的 RSS 源

问题：
  - 5 个数据源 URL 返回 HTTP 404
  - 3 个 API 源未实现收集器
  - 采集成功率仅 40%（6/15）

本脚本的目的：
  1. 更新无效的 RSS URL 为有效的替代源
  2. 禁用无法修复的源
  3. 保留已验证可用的源
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_settings
from src.models import DataSource

# URL 修复映射表
# 原格式: (原源名, 新的有效URL)
URL_FIXES = {
    "Anthropic News": "https://www.anthropic.com/news/rss",  # 尝试不带 .xml 的版本
    "Google DeepMind Blog": "https://deepmind.google/blog/rss/",  # 尝试 /blog/rss/ 路径
    "Microsoft AI Blog": "https://www.microsoft.com/en-us/ai/blog/rss.xml",  # 更新路径
    "NVIDIA AI Blog": "https://blogs.nvidia.com/feed/",  # 改用通用 feed
    "JiQiZhiXin": "https://www.jiqizhixin.com/feed",  # 尝试不带 /rss
}

# 应禁用的源（无法修复）
DISABLE_SOURCES = [
    "Real News Aggregator",  # API 未实现
    "ArXiv CS.AI",  # API 未实现
    "Papers with Code",  # API 未实现
]

def main():
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "=" * 80)
    print("修复数据源配置")
    print("=" * 80)
    print()

    try:
        # 1. 更新无效的 RSS URL
        print("[1] 更新无效的 RSS URL")
        print("-" * 80)

        fixed_count = 0
        for source_name, new_url in URL_FIXES.items():
            source = session.query(DataSource).filter(
                DataSource.name == source_name
            ).first()

            if source:
                old_url = source.url
                source.url = new_url
                session.commit()

                print(f"  [UPDATE] {source_name}")
                print(f"    OLD: {old_url}")
                print(f"    NEW: {new_url}")
                fixed_count += 1
            else:
                print(f"  [NOT FOUND] {source_name}")

        print(f"\n  总计更新: {fixed_count}/{len(URL_FIXES)}")
        print()

        # 2. 禁用无法实现的 API 源
        print("[2] 禁用未实现的 API 源")
        print("-" * 80)

        disabled_count = 0
        for source_name in DISABLE_SOURCES:
            source = session.query(DataSource).filter(
                DataSource.name == source_name
            ).first()

            if source:
                source.is_enabled = False
                session.commit()

                print(f"  [DISABLED] {source_name} (API 收集器未实现)")
                disabled_count += 1
            else:
                print(f"  [NOT FOUND] {source_name}")

        print(f"\n  总计禁用: {disabled_count}/{len(DISABLE_SOURCES)}")
        print()

        # 3. 显示修复后的统计
        print("[3] 修复后的数据源统计")
        print("-" * 80)

        all_sources = session.query(DataSource).all()
        enabled_sources = session.query(DataSource).filter(
            DataSource.is_enabled == True
        ).all()
        api_sources = session.query(DataSource).filter(
            DataSource.type == "api"
        ).all()
        rss_sources = session.query(DataSource).filter(
            DataSource.type == "rss",
            DataSource.is_enabled == True
        ).all()

        print(f"  总数据源: {len(all_sources)}")
        print(f"  已启用: {len(enabled_sources)}")
        print(f"  RSS 源: {len(rss_sources)}")
        print(f"  API 源: {len(api_sources)} (已禁用未实现的)")
        print()

        # 4. 显示已启用的源列表
        print("[4] 已启用的数据源列表")
        print("-" * 80)

        for source in sorted(enabled_sources, key=lambda s: s.name):
            status = "RSS" if source.type == "rss" else "API"
            print(f"  [{status}] {source.name:30} (优先级: {source.priority})")

        print()
        print("=" * 80)
        print("修复完成！")
        print("=" * 80)
        print()
        print("下一步：")
        print("  python scripts/01-collection/collect_news.py  # 重新采集")
        print()

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        session.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
