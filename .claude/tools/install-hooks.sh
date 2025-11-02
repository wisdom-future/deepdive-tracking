#!/bin/bash
# Install Git hooks for enforcing project standards

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Installing Git hooks..."
echo ""

# Ensure hooks directory exists
mkdir -p "$HOOKS_DIR"

# Make hooks executable
for hook in pre-commit prepare-commit-msg commit-msg; do
    hook_file="$HOOKS_DIR/$hook"
    if [ -f "$hook_file" ]; then
        chmod +x "$hook_file"
        echo "✅ $hook hook installed and made executable"
    else
        echo "⚠️  $hook hook not found in .git/hooks"
    fi
done

echo ""
echo "✅ All hooks installed successfully!"
echo ""
echo "The following hooks are now active:"
echo "  1. pre-commit       - Checks file naming, code style, tests"
echo "  2. prepare-commit-msg - Templates commit messages"
echo "  3. commit-msg       - Validates Conventional Commits format"
echo ""
echo "These hooks will run automatically before each commit."
echo "To bypass hooks (NOT RECOMMENDED): git commit --no-verify"
echo ""
