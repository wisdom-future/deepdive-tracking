#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenAI API 诊断脚本

检查：
1. API 密钥是否正确配置
2. API 密钥格式是否有效
3. API 连接是否正常
4. 账户余额是否充足
"""

import sys
import os
from pathlib import Path
import io

# 设置标准输出编码为 UTF-8 (Windows 兼容)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Settings


def diagnose():
    """诊断 OpenAI API 配置"""

    print("\n" + "="*70)
    print("🔍 OpenAI API Diagnosis Tool")
    print("="*70)

    # 1. 检查配置
    print("\n1️⃣  Checking Configuration...")
    try:
        settings = Settings()
        print("✅ Settings loaded successfully")
    except Exception as e:
        print(f"❌ Error loading settings: {str(e)}")
        return

    # 2. 检查 API 密钥
    print("\n2️⃣  Checking API Key...")
    api_key = settings.openai_api_key

    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        print("   Solution: Add OPENAI_API_KEY to .env file")
        return

    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")

    # 3. 检查密钥格式
    print("\n3️⃣  Checking Key Format...")
    if api_key.startswith("sk-"):
        print("✅ Key format looks valid (starts with 'sk-')")
    else:
        print(f"⚠️  Key format unusual: {api_key[:5]}...")

    if len(api_key) < 20:
        print(f"⚠️  Key seems too short ({len(api_key)} chars)")
    else:
        print(f"✅ Key length: {len(api_key)} chars")

    # 4. 检查模型配置
    print("\n4️⃣  Checking Model Configuration...")
    model = settings.openai_model
    print(f"✅ Model: {model}")

    # 5. 尝试 API 连接
    print("\n5️⃣  Testing API Connection...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        print("✅ OpenAI client initialized")
        print("   Note: This doesn't verify actual connectivity or balance")
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {str(e)}")
        return

    # 6. 尝试简单的 API 调用
    print("\n6️⃣  Testing Simple API Call...")
    print("⏳ Making a test call to OpenAI API...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'OK'"}
            ],
            max_tokens=10,
        )

        reply = response.choices[0].message.content
        print(f"✅ API Call Successful!")
        print(f"   Response: {reply}")
        print(f"   Used {response.usage.prompt_tokens} prompt tokens")
        print(f"   Used {response.usage.completion_tokens} completion tokens")

        # 计算成本
        cost = (response.usage.prompt_tokens * 0.000005 +
                response.usage.completion_tokens * 0.000015)
        print(f"   Estimated cost: ${cost:.6f}")

        print("\n✅ API is working correctly!")
        print("   You can now run: python scripts/test-real-api.py")

    except Exception as e:
        error_msg = str(e)
        print(f"❌ API Call Failed!")
        print(f"   Error: {error_msg}")

        # 诊断具体错误
        print(f"\n🔧 Troubleshooting:")

        if "401" in error_msg or "Unauthorized" in error_msg:
            print("   • Invalid API key")
            print("   • Solution: Check .env file for correct OPENAI_API_KEY")
            print("   • Get new key: https://platform.openai.com/account/api-keys")

        elif "429" in error_msg or "rate_limit" in error_msg:
            print("   • Rate limit exceeded (too many requests)")
            print("   • Solution: Wait a moment and try again")

        elif "quota" in error_msg or "insufficient" in error_msg:
            print("   • Account quota exceeded or insufficient balance")
            print("   • Solution: Check account balance")
            print("   • Add funds: https://platform.openai.com/account/billing/overview")

        elif "Connection" in error_msg:
            print("   • Network connection issue")
            print("   • Solution: Check internet connection")
            print("   • Check OpenAI status: https://status.openai.com/")

        else:
            print(f"   • Unknown error: {error_msg}")

    # 7. 显示配置摘要
    print("\n" + "="*70)
    print("📋 Configuration Summary")
    print("="*70)
    print(f"Environment: {settings.app_env}")
    print(f"Model: {model}")
    print(f"Debug: {settings.debug}")
    print(f"Log Level: {settings.log_level}")

    print("\n" + "="*70)
    print("✅ Diagnosis Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        diagnose()
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
