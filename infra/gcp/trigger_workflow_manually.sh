#!/bin/bash
# Manual workflow trigger - 手动触发工作流
# Supports both Cloud Scheduler and direct API call

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-deepdive-tracking}"
REGION="asia-east1"
SERVICE_URL="https://deepdive-tracking-orp2dcdqua-de.a.run.app"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================================="
echo "DeepDive Tracking - Manual Workflow Trigger"
echo "手动触发工作流"
echo "=================================================="
echo ""

# Show menu
echo "Select trigger method:"
echo "  1) Via Cloud Scheduler (recommended - uses OIDC auth)"
echo "  2) Via API endpoint directly (requires service to be public)"
echo "  3) Check workflow status"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}Method 1: Triggering via Cloud Scheduler${NC}"
        echo "=================================================="
        echo ""

        # Show available jobs
        echo "Available scheduler jobs:"
        gcloud scheduler jobs list --location=$REGION --project=$PROJECT_ID | grep deepdive || echo "  No jobs found"

        echo ""
        echo "Which job to trigger?"
        echo "  1) deepdive-daily-workflow (daily workflow)"
        echo "  2) deepdive-weekly-report (weekly report)"
        echo "  3) deepdive-intensive-workflow (intensive - if active)"
        echo ""
        read -p "Enter choice (1-3): " job_choice

        case $job_choice in
            1) JOB_NAME="deepdive-daily-workflow" ;;
            2) JOB_NAME="deepdive-weekly-report" ;;
            3) JOB_NAME="deepdive-intensive-workflow" ;;
            *) echo "Invalid choice"; exit 1 ;;
        esac

        echo ""
        echo "Triggering: $JOB_NAME"
        echo ""

        gcloud scheduler jobs run $JOB_NAME \
            --location=$REGION \
            --project=$PROJECT_ID

        echo ""
        echo -e "${GREEN}✓ Job triggered successfully${NC}"
        echo ""
        echo "View logs:"
        echo "  gcloud scheduler jobs logs $JOB_NAME --location=$REGION --limit=10"
        echo ""
        echo "Or view in console:"
        echo "  https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
        ;;

    2)
        echo ""
        echo -e "${BLUE}Method 2: Direct API Call${NC}"
        echo "=================================================="
        echo ""

        echo "Which workflow to trigger?"
        echo "  1) Daily workflow"
        echo "  2) Weekly workflow"
        echo ""
        read -p "Enter choice (1-2): " api_choice

        case $api_choice in
            1) ENDPOINT="/api/v1/workflows/daily" ;;
            2) ENDPOINT="/api/v1/workflows/weekly" ;;
            *) echo "Invalid choice"; exit 1 ;;
        esac

        echo ""
        echo "Calling: ${SERVICE_URL}${ENDPOINT}"
        echo ""

        response=$(curl -s -X POST "${SERVICE_URL}${ENDPOINT}" \
            -H "Content-Type: application/json" \
            -w "\nHTTP_CODE:%{http_code}")

        http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
        body=$(echo "$response" | grep -v "HTTP_CODE:")

        echo "Response:"
        echo "$body" | python -m json.tool 2>/dev/null || echo "$body"
        echo ""

        if [ "$http_code" = "200" ]; then
            echo -e "${GREEN}✓ Workflow triggered successfully (HTTP $http_code)${NC}"
        else
            echo -e "${YELLOW}⚠ Unexpected HTTP code: $http_code${NC}"
        fi
        ;;

    3)
        echo ""
        echo -e "${BLUE}Method 3: Check Workflow Status${NC}"
        echo "=================================================="
        echo ""

        echo "Fetching workflow status..."
        echo ""

        response=$(curl -s "${SERVICE_URL}/api/v1/workflows/status")

        echo "Response:"
        echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
        ;;

    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=================================================="
echo ""
echo "Additional commands:"
echo ""
echo "View Cloud Run logs:"
echo "  gcloud run services logs read deepdive-tracking --region=$REGION --limit=50"
echo ""
echo "View workflow results:"
echo "  ls -lh logs/workflow_*.json"
echo ""
