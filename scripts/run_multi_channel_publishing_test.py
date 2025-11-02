#!/usr/bin/env python3
"""
多渠道发布端到端测试脚本

这个脚本测试完整的多渠道发布流程：
1. 验证所有渠道配置
2. 查询已批准的文章
3. 同时发布到 WeChat, GitHub, Email
4. 生成发布统计报告

使用方法:
    python scripts/run_multi_channel_publishing_test.py [channels] [num_articles]

示例:
    python scripts/run_multi_channel_publishing_test.py wechat,github,email 5
    python scripts/run_multi_channel_publishing_test.py wechat 3
    python scripts/run_multi_channel_publishing_test.py all  # 使用所有已配置的渠道
"""

import sys
import os
from pathlib import Path
import io
import asyncio
from datetime import datetime

# Set UTF-8 encoding for Windows compatibility
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import Base
from src.services.channels import ChannelManager
from src.services.workflow.multi_channel_publishing_workflow import MultiChannelPublishingWorkflow


def print_header(title):
    """Print a section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_step(num, title):
    """Print a step header."""
    print(f"\n[步骤 {num}] {title}")
    print("-" * 80)


def print_success(message):
    """Print success message."""
    print(f"  ✅ {message}")


def print_error(message):
    """Print error message."""
    print(f"  ❌ {message}")


def print_warning(message):
    """Print warning message."""
    print(f"  ⚠️  {message}")


def print_info(message):
    """Print info message."""
    print(f"  ℹ️  {message}")


def main():
    """Main function."""
    print_header("DeepDive 多渠道发布测试：WeChat + GitHub + Email")

    # Parse arguments
    channels = []
    num_articles = 5

    for arg in sys.argv[1:]:
        if arg in ["all", "wechat", "github", "email"]:
            if arg == "all":
                channels = ["wechat", "github", "email"]
            else:
                if arg not in channels:
                    channels.append(arg)
        else:
            try:
                num_articles = int(arg)
            except ValueError:
                pass

    if not channels:
        channels = ["wechat"]  # Default to WeChat only

    print(f"配置:")
    print(f"  • 发布渠道: {', '.join(channels)}")
    print(f"  • 文章数量: {num_articles}\n")

    # Initialize settings and database
    get_settings.cache_clear()
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # ===== 步骤 0: 验证配置 =====
        print_step(0, "验证渠道配置")

        channel_manager = ChannelManager(session)

        for channel_type in channels:
            try:
                config = channel_manager.get_channel_by_type(channel_type)
                if config:
                    if config.is_enabled:
                        print_success(f"{channel_type.upper()} 渠道已配置且启用")
                    else:
                        print_warning(f"{channel_type.upper()} 渠道已配置但已禁用")
                else:
                    print_warning(f"{channel_type.upper()} 渠道未配置")
            except Exception as e:
                print_warning(f"{channel_type.upper()} 配置检查失败: {str(e)}")

        print()

        # ===== 步骤 1: 显示所有渠道状态 =====
        print_step(1, "渠道状态概览")

        try:
            all_status = channel_manager.get_all_channels_status()
            for channel_type, status in all_status.items():
                enabled_str = "✓ 启用" if status['enabled'] else "✗ 禁用"
                print(f"  {channel_type.upper():8} | {status['name']:15} | {enabled_str} | 发布: {status['total_published']:3d} | 失败: {status['total_failed']:3d}")
        except Exception as e:
            print_error(f"获取渠道状态失败: {str(e)}")

        print()

        # ===== 步骤 2: 初始化工作流 =====
        print_step(2, "初始化多渠道发布工作流")

        workflow = MultiChannelPublishingWorkflow(session)

        # 配置已启用的渠道
        configured_channels = []

        if "wechat" in channels:
            try:
                if settings.wechat_app_id and settings.wechat_app_secret:
                    workflow.configure_wechat(settings.wechat_app_id, settings.wechat_app_secret)
                    configured_channels.append("wechat")
                    print_success("WeChat发布器已初始化")
                else:
                    print_warning("WeChat凭证未配置")
            except Exception as e:
                print_error(f"初始化WeChat失败: {str(e)}")

        if "github" in channels:
            try:
                if all([
                    settings.github_token,
                    settings.github_repo,
                    settings.github_username
                ]):
                    workflow.configure_github(
                        github_token=settings.github_token,
                        github_repo=settings.github_repo,
                        github_username=settings.github_username,
                        local_repo_path=settings.github_local_path or "/tmp/deepdive-github"
                    )
                    configured_channels.append("github")
                    print_success("GitHub发布器已初始化")
                else:
                    print_warning("GitHub凭证未配置")
            except Exception as e:
                print_error(f"初始化GitHub失败: {str(e)}")

        if "email" in channels:
            try:
                if all([
                    settings.smtp_host,
                    settings.smtp_user,
                    settings.smtp_password,
                    settings.smtp_from_email
                ]):
                    workflow.configure_email(
                        smtp_host=settings.smtp_host,
                        smtp_port=settings.smtp_port or 587,
                        smtp_user=settings.smtp_user,
                        smtp_password=settings.smtp_password,
                        from_email=settings.smtp_from_email,
                        from_name=settings.smtp_from_name or "DeepDive Tracking",
                        email_list=settings.email_list or ["hello.junjie.duan@gmail.com"]
                    )
                    configured_channels.append("email")
                    print_success("Email发布器已初始化")
                else:
                    print_warning("Email配置未完整")
            except Exception as e:
                print_error(f"初始化Email失败: {str(e)}")

        if not configured_channels:
            print_warning("没有可用的渠道配置")
            print_info("请在 .env 或环境变量中配置渠道凭证")
            return 1

        print()

        # ===== 步骤 3: 执行多渠道发布 =====
        print_step(3, "执行多渠道发布工作流")

        print_info(f"启动发布流程，目标渠道: {', '.join(configured_channels)}")

        result = asyncio.run(workflow.execute(
            channels=configured_channels,
            batch_size=min(3, num_articles),
            article_limit=num_articles
        ))

        # 显示整体结果
        print()
        if result.get("success"):
            print_success("多渠道发布工作流完成成功!")
        else:
            print_error("多渠道发布工作流中发生错误!")

        # 显示汇总信息
        summary = result.get("summary", {})
        print(f"\n  总体统计:")
        print(f"    • 处理文章数: {summary.get('total_articles', 0)} 篇")
        print(f"    • 发布渠道: {', '.join(summary.get('published_channels', []) or ['无'])}")

        # 显示各渠道详细结果
        if result.get("wechat"):
            print(f"\n  📱 WeChat:")
            wechat_result = result["wechat"]
            if wechat_result.get("success"):
                print(f"    ✓ 发布成功: {wechat_result.get('published_count', 0)} 篇")
            else:
                print(f"    ✗ 发布失败: {wechat_result.get('error', 'Unknown error')}")
            if wechat_result.get("failed_count", 0) > 0:
                print(f"    ⚠ 失败: {wechat_result.get('failed_count', 0)} 篇")

        if result.get("github"):
            print(f"\n  🐙 GitHub:")
            github_result = result["github"]
            if github_result.get("success"):
                print(f"    ✓ 发布成功: {github_result.get('published_count', 0)} 篇")
                print(f"    📍 Batch URL: {github_result.get('batch_url', 'N/A')}")
            else:
                print(f"    ✗ 发布失败: {github_result.get('error', 'Unknown error')}")
            if github_result.get("failed_count", 0) > 0:
                print(f"    ⚠ 失败: {github_result.get('failed_count', 0)} 篇")

        if result.get("email"):
            print(f"\n  📧 Email:")
            email_result = result["email"]
            if email_result.get("success"):
                print(f"    ✓ 发送成功: {email_result.get('sent_emails', 0)} 个邮箱")
            else:
                print(f"    ✗ 发送失败: {email_result.get('error', 'Unknown error')}")
            if email_result.get("failed_emails"):
                print(f"    ⚠ 失败邮箱: {', '.join(email_result.get('failed_emails', []))}")

        print()

        # ===== 步骤 4: 更新渠道统计 =====
        print_step(4, "更新渠道统计")

        try:
            all_stats = channel_manager.get_all_stats()

            for channel_type, stats in all_stats.items():
                print(f"\n  {channel_type.upper()}:")
                print(f"    • 配置数: {stats.get('config_count', 0)}")
                print(f"    • 启用数: {stats.get('enabled_count', 0)}")

                if channel_type == "email":
                    print(f"    • 已发送: {stats.get('total_sent', 0)}")
                    print(f"    • 失败: {stats.get('total_failed', 0)}")
                    print(f"    • 收件人总数: {stats.get('total_recipients', 0)}")
                else:
                    print(f"    • 已发布: {stats.get('total_published', 0)}")
                    print(f"    • 失败: {stats.get('total_failed', 0)}")

        except Exception as e:
            print_error(f"获取统计失败: {str(e)}")

        print()

        # ===== 完成 =====
        print_header("多渠道发布测试完成")

        if result.get("success") and len(summary.get('published_channels', [])) > 0:
            print_success(f"已成功发布到 {len(summary.get('published_channels', []))} 个渠道!\n")
            return 0
        else:
            print_warning("测试完成，但部分渠道可能失败\n")
            return 1

    except KeyboardInterrupt:
        print_error("\n测试被用户中断")
        return 130
    except Exception as e:
        print_error(f"\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
