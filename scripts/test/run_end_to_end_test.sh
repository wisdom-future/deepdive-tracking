#!/bin/bash
# End-to-End Grok Test Runner
# Executes complete workflow: Clear → Collect → Score → Analyze → Publish

set -e  # Exit on error

echo "================================================================================"
echo " END-TO-END GROK SCORING TEST"
echo "================================================================================"
echo ""
echo "Test started at: $(date -Iseconds)"
echo ""

# Navigate to app directory (Cloud Run sets WORKDIR to /app)
cd /app

# Step 1: Clear old data
echo "================================================================================"
echo " STEP 1: Clear Old Scoring Data"
echo "================================================================================"
python scripts/debug/clear_old_scoring_data.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to clear old data"
    exit 1
fi
echo ""

# Step 2: Collect fresh news
echo "================================================================================"
echo " STEP 2: Collect Fresh News Articles"
echo "================================================================================"
python scripts/collection/collect_news.py
if [ $? -ne 0 ]; then
    echo "❌ Failed to collect news"
    exit 1
fi
echo ""

# Step 3: Score with Grok
echo "================================================================================"
echo " STEP 3: Score Articles with Grok"
echo "================================================================================"
python scripts/evaluation/score_collected_news.py 50
if [ $? -ne 0 ]; then
    echo "❌ Failed to score articles"
    exit 1
fi
echo ""

# Step 4: Analyze diversity
echo "================================================================================"
echo " STEP 4: Analyze Source Diversity"
echo "================================================================================"
python scripts/debug/analyze_scoring_issue.py
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to analyze diversity (non-fatal)"
fi
echo ""

# Step 5: Publish
echo "================================================================================"
echo " STEP 5: Publish TOP News with Diversity Selection"
echo "================================================================================"
python scripts/publish/send_top_ai_news_to_github.py
if [ $? -ne 0 ]; then
    echo "⚠️  Failed to publish (non-fatal)"
fi
echo ""

echo "================================================================================"
echo " TEST COMPLETED"
echo "================================================================================"
echo "Test finished at: $(date -Iseconds)"
echo ""
echo "✅ All steps completed successfully"
echo ""
exit 0
