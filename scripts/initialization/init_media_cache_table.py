#!/usr/bin/env python3
"""
初始化 WeChat 媒体缓存表

这个脚本创建 wechat_media_cache 表来存储通过永久素材 API 上传的媒体信息。

Usage:
    python scripts/06-initialization/init_media_cache_table.py
"""

import sys
from pathlib import Path

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import Base, WeChatMediaCache


def init_table():
    """初始化媒体缓存表"""

    print("\n" + "="*80)
    print("  WeChat 媒体缓存表初始化")
    print("="*80 + "\n")

    # 获取配置
    get_settings.cache_clear()
    settings = get_settings()

    print(f"数据库: {settings.database_url}\n")

    # 创建引擎
    engine = create_engine(settings.database_url, echo=False)

    # 检查表是否存在
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "wechat_media_cache" in tables:
        print("✓ wechat_media_cache 表已存在\n")

        # 显示表信息
        columns = inspector.get_columns("wechat_media_cache")
        print("表结构:")
        for col in columns:
            print(f"  - {col['name']:<20} {str(col['type']):<20}")
        print()
        return True

    print("创建 wechat_media_cache 表...\n")

    try:
        # 创建表
        Base.metadata.create_all(
            bind=engine,
            tables=[WeChatMediaCache.__table__]
        )

        print("✓ 表创建成功\n")

        # 显示表信息
        inspector = inspect(engine)
        columns = inspector.get_columns("wechat_media_cache")
        print("表结构:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']:<20} {str(col['type']):<20} {nullable}")
        print()

        # 显示索引
        indexes = inspector.get_indexes("wechat_media_cache")
        if indexes:
            print("索引:")
            for idx in indexes:
                print(f"  - {idx['name']:<30} 字段: {', '.join(idx['column_names'])}")
            print()

        print("✓ 初始化完成\n")
        return True

    except Exception as e:
        print(f"✗ 创建表失败: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_table()
    sys.exit(0 if success else 1)
