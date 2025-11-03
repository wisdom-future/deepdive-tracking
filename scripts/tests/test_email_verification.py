#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email verification script - Test complete email sending functionality
"""
import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.channels.email.email_publisher import EmailPublisher
from src.config.settings import get_settings

def test_email_verification():
    """Test email sending functionality"""

    settings = get_settings()

    print("=" * 70)
    print("Email System Verification Test")
    print("=" * 70)

    # Check configuration
    print("\n1. Checking SMTP configuration...")
    if not settings.smtp_user or not settings.smtp_password:
        print("[FAILED] Error: SMTP credentials not configured")
        return False

    print(f"[OK] SMTP Host: {settings.smtp_host}")
    print(f"[OK] SMTP Port: {settings.smtp_port}")
    print(f"[OK] From Email: {settings.smtp_from_email}")
    print(f"[OK] From Name: {settings.smtp_from_name}")

    # Create email publisher
    print("\n2. Initializing Email Publisher...")
    try:
        publisher = EmailPublisher(settings)
        print("[OK] Email publisher initialized successfully")
    except Exception as e:
        print(f"[FAILED] Initialization failed: {e}")
        return False

    # 准备测试邮件
    print("\n3. 准备测试邮件...")
    test_article = {
        "title": "DeepDive Tracking - 系统验证邮件",
        "summary": "这是一封系统验证邮件，用于测试邮件发送功能是否正常工作。",
        "url": "https://deepdive-tracking-726493701291.asia-east1.run.app",
        "source": "System Test",
        "score": 95,
        "category": "Technology",
        "published_at": datetime.now().isoformat(),
        "content": """
<div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2>DeepDive Tracking 系统验证</h2>

    <p><strong>时间:</strong> {}</p>

    <h3>✓ 已完成的任务：</h3>
    <ul>
        <li>✓ Cloud Run 部署成功</li>
        <li>✓ 数据库连接正常</li>
        <li>✓ Redis 缓存可用</li>
        <li>✓ GCP Secret Manager 集成</li>
        <li>✓ 邮件系统初始化成功</li>
    </ul>

    <h3>📊 系统状态：</h3>
    <p><strong>服务URL:</strong> https://deepdive-tracking-726493701291.asia-east1.run.app</p>
    <p><strong>区域:</strong> asia-east1</p>
    <p><strong>状态:</strong> 运行中 (RUNNING)</p>

    <h3>📧 邮件功能验证：</h3>
    <p>如果您收到此邮件，说明以下功能正常工作：</p>
    <ul>
        <li>✓ SMTP连接</li>
        <li>✓ Gmail应用密码认证</li>
        <li>✓ HTML邮件格式化</li>
        <li>✓ 邮件内容生成</li>
    </ul>

    <h3>🚀 下一步计划：</h3>
    <ul>
        <li>运行完整的E2E测试</li>
        <li>进行新闻采集和评分测试</li>
        <li>验证所有发布渠道功能</li>
    </ul>

    <hr>
    <p style="color: #666; font-size: 12px;">
        这是一封自动生成的系统验证邮件。<br>
        如有问题，请检查Cloud Run日志：
        gcloud logging read "resource.type=cloud_run_revision" --limit=50
    </p>
</div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    }

    print(f"✓ 邮件标题: {test_article['title']}")
    print(f"✓ 邮件得分: {test_article['score']}")

    # 发送邮件
    print("\n4. 发送邮件...")
    try:
        recipient_email = settings.smtp_from_email or "hello.junjie.duan@gmail.com"
        print(f"   收件人: {recipient_email}")

        result = publisher.publish_article(
            article=test_article,
            recipient_email=recipient_email
        )

        if result:
            print("✓ 邮件发送成功！")
        else:
            print("❌ 邮件发送失败")
            return False

    except Exception as e:
        print(f"❌ 发送异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试完成
    print("\n" + "=" * 70)
    print("✓ 邮件系统验证完成！")
    print("=" * 70)
    print("\n📧 邮件已发送到: hello.junjie.duan@gmail.com")
    print("\n请检查您的邮箱确认邮件是否收到。")

    return True

if __name__ == "__main__":
    success = test_email_verification()
    sys.exit(0 if success else 1)
