#!/bin/bash
# GCP 端到端完整测试脚本
# 1. 清空数据库
# 2. 数据采集
# 3. AI评分
# 4. 邮件发送

set -e  # 遇到错误立即退出

echo "=================================="
echo "DeepDive Tracking - 端到端测试"
echo "=================================="

# 获取认证token
echo ""
echo "[步骤0] 获取GCP认证token..."
TOKEN=$(gcloud auth print-identity-token)
echo "✓ Token获取成功"

BASE_URL="https://deepdive-tracking-726493701291.asia-east1.run.app"

# 步骤1: 清空数据库（通过诊断API检查）
echo ""
echo "[步骤1] 检查数据库状态..."
curl -s -X GET "$BASE_URL/diagnose/database" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool | head -20

echo ""
echo "⚠️  需要手动清空数据库"
echo "请运行: python scripts/debug/clean_all_data_gcp.py"
echo ""
read -p "数据库已清空？按Enter继续..."

# 步骤2: 数据采集
echo ""
echo "[步骤2] 执行数据采集..."
echo "调用: POST $BASE_URL/trigger/workflow?step=collect"
curl -s -X POST "$BASE_URL/trigger/workflow?step=collect" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool

echo ""
echo "✓ 数据采集完成"
sleep 3

# 步骤3: AI评分
echo ""
echo "[步骤3] 执行AI评分..."
echo "调用: POST $BASE_URL/trigger/workflow?step=score"
curl -s -X POST "$BASE_URL/trigger/workflow?step=score" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool

echo ""
echo "✓ AI评分完成"
sleep 3

# 步骤4: 邮件发送
echo ""
echo "[步骤4] 发送邮件..."
echo "调用: POST $BASE_URL/publish/email"
curl -s -X POST "$BASE_URL/publish/email" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | python -m json.tool

echo ""
echo "=================================="
echo "✅ 端到端测试完成！"
echo "=================================="
echo ""
echo "请检查邮箱: hello.junjie.duan@gmail.com"
