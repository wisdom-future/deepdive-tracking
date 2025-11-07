#!/bin/bash
# Setup Cloud Scheduler for DeepDive Tracking daily workflow
# 配置GCP Cloud Scheduler实现每日自动执行

set -e

echo "=================================================="
echo "DeepDive Tracking - Cloud Scheduler Setup"
echo "=================================================="

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-deepdive-tracking}"
REGION="asia-east1"
SERVICE_URL="https://deepdive-tracking-orp2dcdqua-de.a.run.app"
SERVICE_ACCOUNT="deepdive-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "Configuration:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service URL: $SERVICE_URL"
echo ""

# Step 1: Enable APIs
echo "[1/5] Enabling required APIs..."
gcloud services enable cloudscheduler.googleapis.com \
    --project=$PROJECT_ID

gcloud services enable run.googleapis.com \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} APIs enabled"

# Step 2: Create service account for scheduler
echo ""
echo "[2/5] Creating service account..."

# Check if service account exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Service account already exists: $SERVICE_ACCOUNT"
else
    gcloud iam service-accounts create deepdive-scheduler \
        --display-name="DeepDive Scheduler Service Account" \
        --project=$PROJECT_ID

    echo -e "${GREEN}✓${NC} Service account created: $SERVICE_ACCOUNT"
fi

# Step 3: Grant permissions
echo ""
echo "[3/5] Granting permissions..."

# Grant Cloud Run Invoker role
gcloud run services add-iam-policy-binding deepdive-tracking \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker" \
    --region=$REGION \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} Permissions granted"

# Step 4: Create Cloud Scheduler jobs
echo ""
echo "[4/5] Creating Cloud Scheduler jobs..."

# Job 1: Daily workflow (Every day at 8:00 AM Beijing Time)
JOB_NAME_DAILY="deepdive-daily-workflow"

# Delete existing job if any
if gcloud scheduler jobs describe $JOB_NAME_DAILY --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Deleting existing job: $JOB_NAME_DAILY"
    gcloud scheduler jobs delete $JOB_NAME_DAILY \
        --location=$REGION \
        --project=$PROJECT_ID \
        --quiet
fi

# Create daily job (8:00 AM)
gcloud scheduler jobs create http $JOB_NAME_DAILY \
    --location=$REGION \
    --schedule="0 8 * * *" \
    --time-zone="Asia/Shanghai" \
    --uri="${SERVICE_URL}/api/v1/workflows/daily" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --oidc-token-audience=$SERVICE_URL \
    --attempt-deadline=30m \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} Daily job created: $JOB_NAME_DAILY"
echo "  Schedule: Every day at 8:00 AM Beijing Time"
echo "  Endpoint: ${SERVICE_URL}/api/v1/workflows/daily"

# Job 2: Weekly report (Every Sunday at 10:00 AM Beijing Time)
JOB_NAME_WEEKLY="deepdive-weekly-report"

# Delete existing job if any
if gcloud scheduler jobs describe $JOB_NAME_WEEKLY --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Deleting existing job: $JOB_NAME_WEEKLY"
    gcloud scheduler jobs delete $JOB_NAME_WEEKLY \
        --location=$REGION \
        --project=$PROJECT_ID \
        --quiet
fi

# Create weekly job
gcloud scheduler jobs create http $JOB_NAME_WEEKLY \
    --location=$REGION \
    --schedule="0 10 * * 0" \
    --time-zone="Asia/Shanghai" \
    --uri="${SERVICE_URL}/api/v1/workflows/weekly" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --oidc-token-audience=$SERVICE_URL \
    --attempt-deadline=45m \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} Weekly job created: $JOB_NAME_WEEKLY"
echo "  Schedule: Every Sunday at 10:00 AM Beijing Time"
echo "  Endpoint: ${SERVICE_URL}/api/v1/workflows/weekly"

# Job 3: Intensive schedule for first month (Every 6 hours)
# This is a TEMPORARY job for the first month - to be deleted after 30 days
JOB_NAME_INTENSIVE="deepdive-intensive-workflow"

echo ""
echo "Creating intensive schedule job for first month..."

# Delete existing job if any
if gcloud scheduler jobs describe $JOB_NAME_INTENSIVE --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠${NC} Deleting existing job: $JOB_NAME_INTENSIVE"
    gcloud scheduler jobs delete $JOB_NAME_INTENSIVE \
        --location=$REGION \
        --project=$PROJECT_ID \
        --quiet
fi

# Create intensive job (every 6 hours: 0:00, 6:00, 12:00, 18:00)
gcloud scheduler jobs create http $JOB_NAME_INTENSIVE \
    --location=$REGION \
    --schedule="0 0,6,12,18 * * *" \
    --time-zone="Asia/Shanghai" \
    --uri="${SERVICE_URL}/api/v1/workflows/daily" \
    --http-method=POST \
    --oidc-service-account-email=$SERVICE_ACCOUNT \
    --oidc-token-audience=$SERVICE_URL \
    --attempt-deadline=30m \
    --project=$PROJECT_ID

echo -e "${GREEN}✓${NC} Intensive job created: $JOB_NAME_INTENSIVE"
echo "  Schedule: Every 6 hours (0:00, 6:00, 12:00, 18:00) Beijing Time"
echo "  Endpoint: ${SERVICE_URL}/api/v1/workflows/daily"
echo -e "${YELLOW}  NOTE: This is a TEMPORARY job for first month${NC}"
echo -e "${YELLOW}  Remember to delete after 30 days!${NC}"

# Step 5: Verify
echo ""
echo "[5/5] Verifying setup..."

echo ""
echo "Scheduler Jobs:"
gcloud scheduler jobs list --location=$REGION --project=$PROJECT_ID | grep deepdive

echo ""
echo -e "${GREEN}=================================================="
echo "✓ Cloud Scheduler Setup Complete!"
echo "==================================================${NC}"
echo ""
echo "Configured Jobs:"
echo "  1. ${JOB_NAME_DAILY} - Daily at 8:00 AM"
echo "  2. ${JOB_NAME_WEEKLY} - Weekly Sunday at 10:00 AM"
echo "  3. ${JOB_NAME_INTENSIVE} - Every 6 hours (TEMPORARY - 30 days)"
echo ""
echo "Next steps:"
echo ""
echo "1. Test manually:"
echo "   gcloud scheduler jobs run $JOB_NAME_DAILY --location=$REGION --project=$PROJECT_ID"
echo ""
echo "2. View logs:"
echo "   gcloud scheduler jobs logs $JOB_NAME_DAILY --location=$REGION --limit=10"
echo ""
echo "3. Check execution history:"
echo "   gcloud scheduler jobs describe $JOB_NAME_DAILY --location=$REGION"
echo ""
echo -e "${YELLOW}IMPORTANT: After 30 days, delete the intensive job:${NC}"
echo "   gcloud scheduler jobs delete $JOB_NAME_INTENSIVE --location=$REGION --project=$PROJECT_ID"
echo ""
echo "Or use the cleanup script:"
echo "   bash infra/gcp/delete_intensive_schedule.sh"
echo ""
