#!/bin/bash
# Standards compliance checker
# Run this to verify all code follows project standards

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🔍 PROJECT STANDARDS COMPLIANCE CHECK                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# 1. File naming check
# ============================================================================
echo "${BLUE}1. Checking file naming conventions...${NC}"

check_file_names() {
    local pattern='[A-Z].*\.(py|md|txt|yml|yaml|sh)$'
    local violations=$(find . -type f \( -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.sh" \) \
        -path "./src/*" -o -path "./tests/*" -o -path "./.claude/*" 2>/dev/null | \
        grep -E "$pattern" | grep -v ".git" | grep -v "__pycache__" || true)

    if [ ! -z "$violations" ]; then
        echo -e "${RED}❌ Found files with uppercase naming:${NC}"
        echo "$violations" | sed 's/^/   /'
        return 1
    fi
    echo -e "${GREEN}✅ All file names follow snake_case convention${NC}"
    return 0
}

if ! check_file_names; then
    FAILED=1
fi

echo ""

# ============================================================================
# 2. Python code style
# ============================================================================
echo "${BLUE}2. Checking Python code style...${NC}"

if command -v black &> /dev/null; then
    echo "   Running black..."
    if black --check src/ tests/ .claude/ 2>&1 | grep -q "would reformat"; then
        echo -e "${YELLOW}⚠️  Some Python files need formatting${NC}"
        echo "   Run: black src/ tests/ .claude/"
    else
        echo -e "${GREEN}✅ Black formatting check passed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  black not installed${NC}"
fi

echo ""

# ============================================================================
# 3. Flake8 style check
# ============================================================================
echo "${BLUE}3. Checking code style with flake8...${NC}"

if command -v flake8 &> /dev/null; then
    echo "   Running flake8..."
    if flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503 2>&1; then
        echo -e "${GREEN}✅ flake8 check passed${NC}"
    else
        echo -e "${RED}❌ flake8 found issues${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠️  flake8 not installed${NC}"
fi

echo ""

# ============================================================================
# 4. Type checking with mypy
# ============================================================================
echo "${BLUE}4. Checking types with mypy...${NC}"

if command -v mypy &> /dev/null; then
    echo "   Running mypy..."
    if mypy src/ tests/ --ignore-missing-imports 2>&1 | grep -q "error:"; then
        echo -e "${RED}❌ Type errors found${NC}"
        mypy src/ tests/ --ignore-missing-imports
        FAILED=1
    else
        echo -e "${GREEN}✅ mypy check passed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  mypy not installed${NC}"
fi

echo ""

# ============================================================================
# 5. Tests
# ============================================================================
echo "${BLUE}5. Running tests...${NC}"

if command -v pytest &> /dev/null; then
    echo "   Running pytest..."
    if pytest tests/ -q --tb=short 2>&1; then
        echo -e "${GREEN}✅ All tests passed${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠️  pytest not installed${NC}"
fi

echo ""

# ============================================================================
# 6. Security check
# ============================================================================
echo "${BLUE}6. Checking for hardcoded secrets...${NC}"

SECRETS=$(grep -ri "password\|api.key\|secret\|token\|private.key" src/ tests/ 2>/dev/null | \
    grep -v "#" | grep -v "test_" | grep -v "example" | grep -v "sample" || true)

if [ ! -z "$SECRETS" ]; then
    echo -e "${RED}❌ Possible hardcoded secrets found:${NC}"
    echo "$SECRETS" | sed 's/^/   /'
    FAILED=1
else
    echo -e "${GREEN}✅ No obvious hardcoded secrets found${NC}"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "╔════════════════════════════════════════════════════════════════╗"

if [ $FAILED -eq 0 ]; then
    echo -e "║ ${GREEN}✅ ALL STANDARDS CHECKS PASSED${NC}                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    exit 0
else
    echo -e "║ ${RED}❌ SOME STANDARDS CHECKS FAILED${NC}                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Please fix the issues above and try again."
    exit 1
fi
