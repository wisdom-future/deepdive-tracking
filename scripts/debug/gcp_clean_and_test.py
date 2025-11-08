#!/usr/bin/env python3
"""
GCP端到端测试脚本
1. 清理数据库
2. 执行数据采集
3. 执行AI评分
4. 发送邮件
"""
import requests
import time
import json
import subprocess

# GCP Cloud Run URL
BASE_URL = "https://deepdive-tracking-726493701291.asia-east1.run.app"

def get_auth_token():
    """获取GCP认证token"""
    result = subprocess.run(
        ["gcloud", "auth", "print-identity-token"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def call_api(endpoint, method="POST", data=None):
    """调用Cloud Run API"""
    token = get_auth_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*80}")
    print(f"调用API: {method} {endpoint}")
    print(f"{'='*80}")

    if method == "POST":
        response = requests.post(url, headers=headers, json=data or {}, timeout=300)
    else:
        response = requests.get(url, headers=headers, timeout=300)

    print(f"状态码: {response.status_code}")

    try:
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
        return result
    except:
        print(f"响应文本: {response.text[:500]}")
        return None

def main():
    print("\n" + "="*80)
    print("DeepDive Tracking - GCP端到端测试")
    print("="*80)

    # Step 1: 清理数据库（通过Python脚本）
    print("\n[步骤1] 清理数据库...")
    subprocess.run([
        "gcloud", "run", "jobs", "execute", "deepdive-clean-db",
        "--region=asia-east1",
        "--project=deepdive-engine",
        "--wait"
    ])

    # Step 2: 数据采集
    print("\n[步骤2] 执行数据采集...")
    result = call_api("/publish/collect")

    if not result or result.get("status") != "success":
        print("❌ 数据采集失败")
        return 1

    collected = result.get("total_collected", 0)
    print(f"✅ 采集完成: {collected} 条新闻")

    # 等待数据处理
    time.sleep(5)

    # Step 3: AI评分
    print("\n[步骤3] 执行AI评分...")
    result = call_api("/publish/score")

    if not result or result.get("status") != "success":
        print("❌ AI评分失败")
        return 1

    scored = result.get("processed", 0)
    print(f"✅ 评分完成: {scored} 条")

    # 等待评分完成
    time.sleep(5)

    # Step 4: 发送邮件
    print("\n[步骤4] 发送邮件...")
    result = call_api("/publish/email")

    if not result or result.get("status") != "success":
        print("❌ 邮件发送失败")
        return 1

    print(f"✅ 邮件发送成功")

    print("\n" + "="*80)
    print("✅ 端到端测试完成！")
    print("="*80)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
