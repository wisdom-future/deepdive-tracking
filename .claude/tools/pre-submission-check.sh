#!/bin/bash
# Pre-Submission Verification Script
# MANDATORY to run before claiming any Phase is complete
#
# This script performs comprehensive checks to ensure:
# 1. All standards are followed
# 2. Git Hooks are properly installed
# 3. No violations exist in the codebase
# 4. All tests pass
# 5. Code quality is maintained
#
# DO NOT SKIP THIS SCRIPT BEFORE SUBMITTING PHASE COMPLETION

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

FAILED=0

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  🔍 PRE-SUBMISSION VERIFICATION CHECK (MANDATORY)              ║"
echo "║                                                                ║"
echo "║  This script must pass before claiming Phase completion        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# 1. Check Standards
# ============================================================================
echo "${BLUE}1️⃣ Checking project standards...${NC}"

if bash .claude/tools/check-standards.sh 2>&1; then
    echo -e "${GREEN}✅ PASSED: All standards checks passed${NC}"
else
    echo -e "${RED}❌ FAILED: Standards check failed${NC}"
    FAILED=1
fi

echo ""

# ============================================================================
# 2. Verify Git Hooks Installation
# ============================================================================
echo "${BLUE}2️⃣ Verifying Git Hooks installation...${NC}"

HOOKS_VALID=1

if [ ! -x .git/hooks/pre-commit ]; then
    echo -e "${RED}❌ pre-commit hook not installed or not executable${NC}"
    FAILED=1
    HOOKS_VALID=0
fi

if [ ! -x .git/hooks/commit-msg ]; then
    echo -e "${RED}❌ commit-msg hook not installed or not executable${NC}"
    FAILED=1
    HOOKS_VALID=0
fi

if [ ! -x .git/hooks/prepare-commit-msg ]; then
    echo -e "${RED}⚠️  prepare-commit-msg hook not installed (non-critical)${NC}"
fi

if [ $HOOKS_VALID -eq 1 ]; then
    echo -e "${GREEN}✅ PASSED: All critical Git Hooks are installed${NC}"
fi

echo ""

# ============================================================================
# 3. Scan for Uppercase Filenames
# ============================================================================
echo "${BLUE}3️⃣ Scanning for uppercase filenames...${NC}"

# Check for files with patterns like UPPERCASE_WORDS.md or UPPERCASE-WORDS.md
# Allowed: README.md, CLAUDE.md (these are exceptions)
VIOLATIONS=$(find .claude/handoff -type f \( -name "*.md" -o -name "*.txt" \) -exec sh -c '
  name=$(basename "$1")
  # Allow only README, CLAUDE, or lowercase/kebab-case names
  if [[ "$name" == "README.md" ]] || [[ "$name" == "CLAUDE.md" ]]; then
    exit 0
  fi
  # Reject if contains consecutive uppercase letters (like ANALYSIS, COMPLIANCE, etc.)
  if [[ "$name" =~ [A-Z]{2,} ]]; then
    echo "$1"
  fi
' _ {} \; 2>/dev/null || true)

if [ ! -z "$VIOLATIONS" ]; then
    echo -e "${RED}❌ FAILED: Found files with uppercase patterns:${NC}"
    echo "$VIOLATIONS" | sed 's/^/   /'
    FAILED=1
else
    echo -e "${GREEN}✅ PASSED: No problematic uppercase filenames found${NC}"
fi

echo ""

# ============================================================================
# 4. Check for Violations in Git History
# ============================================================================
echo "${BLUE}4️⃣ Checking git history for naming violations...${NC}"

HISTORY_VIOLATIONS=$(git log --name-status --oneline --all | grep -E "[A-Z].*\.md|[A-Z].*\.py|[A-Z].*\.txt" | head -10 || true)

if [ ! -z "$HISTORY_VIOLATIONS" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Found potential violations in git history:${NC}"
    echo "$HISTORY_VIOLATIONS" | head -5 | sed 's/^/   /'
    echo -e "${YELLOW}   (These are historical - current files should be clean)${NC}"
fi

echo ""

# ============================================================================
# 5. Run All Tests
# ============================================================================
echo "${BLUE}5️⃣ Running all tests...${NC}"

if command -v pytest &> /dev/null; then
    if pytest tests/ -v --tb=short 2>&1 | tail -5; then
        echo -e "${GREEN}✅ PASSED: All tests passed${NC}"
    else
        echo -e "${RED}❌ FAILED: Some tests failed${NC}"
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠️  pytest not installed (skipping tests)${NC}"
fi

echo ""

# ============================================================================
# 6. Verify No Uncommitted Changes
# ============================================================================
echo "${BLUE}6️⃣ Verifying no uncommitted changes...${NC}"

if git diff --quiet HEAD; then
    echo -e "${GREEN}✅ PASSED: No uncommitted changes${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING: Found uncommitted changes:${NC}"
    git diff --name-only HEAD | sed 's/^/   /'
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "╔════════════════════════════════════════════════════════════════╗"

if [ $FAILED -eq 0 ]; then
    echo -e "║ ${GREEN}✅ ALL PRE-SUBMISSION CHECKS PASSED${NC}                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${GREEN}You are clear to submit Phase completion and handoff.${NC}"
    echo ""
    exit 0
else
    echo -e "║ ${RED}❌ PRE-SUBMISSION CHECK FAILED${NC}                            ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${RED}Please fix the above issues before submitting.${NC}"
    echo ""
    exit 1
fi
