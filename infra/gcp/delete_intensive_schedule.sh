#!/bin/bash
# Delete intensive schedule after first month
# 第一个月密集调度结束后删除任务

set -e

echo "=================================================="
echo "Delete Intensive Schedule - 删除密集调度任务"
echo "=================================================="

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-deepdive-tracking}"
REGION="asia-east1"
JOB_NAME_INTENSIVE="deepdive-intensive-workflow"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Job Name: $JOB_NAME_INTENSIVE"
echo ""

# Check if job exists
if ! gcloud scheduler jobs describe $JOB_NAME_INTENSIVE --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Job does not exist: $JOB_NAME_INTENSIVE"
    echo "  Nothing to delete."
    exit 0
fi

# Show job details
echo "Current job details:"
gcloud scheduler jobs describe $JOB_NAME_INTENSIVE \
    --location=$REGION \
    --project=$PROJECT_ID \
    --format="table(name,schedule,state)"

echo ""
echo -e "${YELLOW}⚠ WARNING: This will delete the intensive schedule job.${NC}"
echo "  The daily (8:00 AM) and weekly jobs will remain active."
echo ""
read -p "Are you sure you want to delete? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Delete the job
echo ""
echo "Deleting intensive schedule job..."

gcloud scheduler jobs delete $JOB_NAME_INTENSIVE \
    --location=$REGION \
    --project=$PROJECT_ID \
    --quiet

echo -e "${GREEN}✓${NC} Intensive schedule job deleted"

# Show remaining jobs
echo ""
echo "Remaining scheduler jobs:"
gcloud scheduler jobs list --location=$REGION --project=$PROJECT_ID | grep deepdive

echo ""
echo -e "${GREEN}=================================================="
echo "✓ Cleanup Complete!"
echo "==================================================${NC}"
echo ""
echo "Remaining active schedules:"
echo "  - deepdive-daily-workflow: Every day at 8:00 AM"
echo "  - deepdive-weekly-report: Every Sunday at 10:00 AM"
echo ""
