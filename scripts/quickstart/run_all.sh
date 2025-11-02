#!/bin/bash

#############################################################################
# DeepDive Tracking - 一键启动脚本 (One-Click Testing Script)
#############################################################################
#
# 功能: 自动运行完整的 P1-3 端到端测试
#     (Collection → Evaluation → Verification)
#
# 用途: 快速验证系统是否正常运行
#
# 使用:
#     bash scripts/quickstart/run_all.sh
#
# 输出: 完整的系统流程运行结果
#
#############################################################################

set -e  # 任何命令失败就停止

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}DeepDive Tracking - P1-3 完整端到端测试${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 检查Python
echo -e "${YELLOW}[准备] 检查环境${NC}"
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}错误: Python 未安装${NC}"
    exit 1
fi

PYTHON_CMD="python3"
if ! $PYTHON_CMD --version &> /dev/null; then
    PYTHON_CMD="python"
fi

echo -e "${GREEN}✓ Python 可用: $($PYTHON_CMD --version)${NC}"
echo ""

# 第一步: 采集新闻
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[步骤 1/3] 采集新闻数据${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "$PROJECT_ROOT/scripts/01-collection/collect_news.py" ]; then
    cd "$PROJECT_ROOT"
    $PYTHON_CMD scripts/01-collection/collect_news.py
    COLLECT_STATUS=$?

    if [ $COLLECT_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ 采集完成${NC}"
    else
        echo -e "${RED}✗ 采集失败 (错误代码: $COLLECT_STATUS)${NC}"
        echo -e "${YELLOW}可能原因:${NC}"
        echo "  - 数据库未初始化"
        echo "  - 网络连接问题"
        echo "  - 数据源不可用"
        exit 1
    fi
else
    echo -e "${RED}错误: 找不到采集脚本${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[提示] 采集完成，开始等待 3 秒...${NC}"
sleep 3

# 第二步: 评分新闻
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[步骤 2/3] AI 评分${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "$PROJECT_ROOT/scripts/02-evaluation/score_batch.py" ]; then
    cd "$PROJECT_ROOT"
    $PYTHON_CMD scripts/02-evaluation/score_batch.py
    SCORE_STATUS=$?

    if [ $SCORE_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ 评分完成${NC}"
    else
        echo -e "${RED}✗ 评分失败 (错误代码: $SCORE_STATUS)${NC}"
        echo -e "${YELLOW}可能原因:${NC}"
        echo "  - OpenAI API Key 未配置"
        echo "  - API 配额不足"
        echo "  - 网络连接问题"
        echo ""
        echo -e "${YELLOW}建议: 运行 scripts/02-evaluation/test_api.py 诊断 API 问题${NC}"
    fi
else
    echo -e "${RED}错误: 找不到评分脚本${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[提示] 评分完成，开始等待 3 秒...${NC}"
sleep 3

# 第三步: 查看结果
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}[步骤 3/3] 查看数据库结果${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [ -f "$PROJECT_ROOT/scripts/03-verification/view_summary.py" ]; then
    cd "$PROJECT_ROOT"
    $PYTHON_CMD scripts/03-verification/view_summary.py
    VIEW_STATUS=$?

    if [ $VIEW_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ 数据查看完成${NC}"
    else
        echo -e "${RED}✗ 数据查看失败 (错误代码: $VIEW_STATUS)${NC}"
    fi
else
    echo -e "${RED}错误: 找不到查看脚本${NC}"
    exit 1
fi

# 总结
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 P1-3 完整端到端测试完成！${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}📊 测试结果总结:${NC}"
echo "  ✓ 采集: 新闻已从数据源采集"
echo "  ✓ 评分: 新闻已通过 AI 评分"
echo "  ✓ 验证: 数据库统计已显示"
echo ""

echo -e "${YELLOW}📝 下一步:${NC}"
echo "  1. 查看 TOP 10 新闻结果"
echo "  2. 验证数据质量"
echo "  3. 准备进行 P1-4 性能测试"
echo ""

echo -e "${YELLOW}📚 更多信息:${NC}"
echo "  - 采集详解:  docs/development/p1-ready-for-testing.md"
echo "  - 脚本指南:  docs/development/scripts-guide.md"
echo "  - 主要指南:  scripts/README.md"
echo ""

exit 0
