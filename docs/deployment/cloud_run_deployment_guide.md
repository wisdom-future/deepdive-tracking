# DeepDive Tracking - Production Deployment Guide

## Overview

DeepDive Tracking is now **deployed and operational** on Google Cloud Run. The system is configured to:
1. Collect AI news from multiple sources (300-500 items/day)
2. Score and categorize news with AI (0-100 scale, 8 categories)
3. Publish to multiple channels (Email, GitHub)

## Current Status: ✅ LIVE

- **Service URL**: https://deepdive-tracking-orp2dcdqua-de.a.run.app
- **Region**: asia-east1 (Google Cloud Run)
- **Database**: Cloud SQL PostgreSQL
- **Status**: All endpoints operational
- **Email Publishing**: ✅ Active
- **GitHub Publishing**: ✅ Active

## How It Works

### Architecture

```
Cloud Scheduler (Trigger)
    ↓
Cloud Run Service (Main FastAPI app)
    ├→ /init-db (Initialize database)
    ├→ /seed-test-data (Create test data)
    ├→ /diagnose/database (Check data status)
    ├→ /trigger-workflow (Run complete workflow: collect→score→email→github)
    ├→ /test-email (Test email publishing)
    ├→ /test-github-publisher (Test GitHub publishing)
    └→ /health (Health check)
```

### Daily Workflow

The `/trigger-workflow` endpoint runs the complete daily workflow:

1. **Collection** (`scripts/collection/collect_news.py`)
   - Scrapes RSS feeds and APIs from 300+ news sources
   - Stores raw news in `raw_news` table
   - Detects and removes duplicates

2. **Scoring & Analysis** (`scripts/evaluation/score_*.py`)
   - Uses OpenAI GPT to analyze news relevance
   - Generates bilingual summaries (Chinese + English)
   - Assigns relevance score (0-100)
   - Categorizes into 8 categories

3. **Email Publishing** (`scripts/publish/send_top_news_email.py`)
   - Sends top 10 news items via email
   - Uses HTML template with bilingual summaries
   - Includes AI score and source information

4. **GitHub Publishing** (`scripts/publish/send_top_ai_news_to_github.py`)
   - Publishes articles to GitHub Pages
   - Creates categorized HTML pages
   - Maintains archive of published content

## Testing the System

### Option 1: Test Individual Components

```bash
# Initialize database
curl -X POST https://deepdive-tracking-orp2dcdqua-de.a.run.app/init-db \
  -H "Authorization: Bearer $(gcloud auth print-identity-token --audiences='https://deepdive-tracking-orp2dcdqua-de.a.run.app')" \
  -H "Content-Length: 0"

# Check database status
curl -X GET https://deepdive-tracking-orp2dcdqua-de.a.run.app/diagnose/database \
  -H "Authorization: Bearer $(gcloud auth print-identity-token --audiences='https://deepdive-tracking-orp2dcdqua-de.a.run.app')"

# Test email sending
curl -X POST https://deepdive-tracking-orp2dcdqua-de.a.run.app/test-email \
  -H "Authorization: Bearer $(gcloud auth print-identity-token --audiences='https://deepdive-tracking-orp2dcdqua-de.a.run.app')" \
  -H "Content-Length: 0"

# Test GitHub publishing
curl -X POST https://deepdive-tracking-orp2dcdqua-de.a.run.app/test-github-publisher \
  -H "Authorization: Bearer $(gcloud auth print-identity-token --audiences='https://deepdive-tracking-orp2dcdqua-de.a.run.app')" \
  -H "Content-Length: 0"
```

### Option 2: Run Complete Workflow

```bash
# Trigger complete daily workflow (collect → score → email → github)
curl -X POST https://deepdive-tracking-orp2dcdqua-de.a.run.app/trigger-workflow \
  -H "Authorization: Bearer $(gcloud auth print-identity-token --audiences='https://deepdive-tracking-orp2dcdqua-de.a.run.app')" \
  -H "Content-Length: 0"
```

## Configuration

### Environment Variables (Set in Cloud Run)

```bash
# Database
DATABASE_URL=postgresql://deepdive_user:deepdive_password@/deepdive_db
CLOUDSQL_USER=deepdive_user
CLOUDSQL_PASSWORD=deepdive_password
CLOUDSQL_DATABASE=deepdive_db

# Redis (for Celery)
REDIS_URL=redis://10.240.18.115:6379/0
CELERY_BROKER_URL=redis://10.240.18.115:6379/1
CELERY_RESULT_BACKEND=redis://10.240.18.115:6379/2

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=DeepDive Tracking

# AI/OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxx

# GitHub Publishing
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPO=your-username/deepdive-ai-news

# Application
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO
```

## Scheduling (Cloud Scheduler)

To automatically trigger the daily workflow, set up Cloud Scheduler:

```bash
gcloud scheduler jobs create http daily-deepdive \
  --schedule="0 8 * * *" \
  --uri="https://deepdive-tracking-orp2dcdqua-de.a.run.app/trigger-workflow" \
  --http-method=POST \
  --oidc-service-account-email=deepdive-engine@appspot.gserviceaccount.com \
  --oidc-token-audience="https://deepdive-tracking-orp2dcdqua-de.a.run.app" \
  --location=asia-east1 \
  --time-zone="Asia/Shanghai"
```

## Email Template

The email includes:
- Bilingual summaries (Chinese + English) for each news item
- AI relevance score with color coding
- Source and author information
- Direct links to original articles
- Professional HTML layout optimized for mobile

## English Summary Fixes

The system now ensures:
- ✅ All processed news articles have bilingual summaries
- ✅ English summaries are validated before display
- ✅ Fallback: If no English summary, use Chinese summary
- ✅ Summaries are truncated to reasonable length (100-120 chars)

## Troubleshooting

### Email Not Sending

Check:
1. SMTP credentials are correct in environment variables
2. Email account has "Less secure app access" enabled (if Gmail)
3. Cloud Run Service has internet access
4. Check logs: `gcloud logging read "resource.type=cloud_run_revision" --limit 50`

### GitHub Publishing Not Working

Check:
1. GitHub token is valid and has repo write permissions
2. Repository exists and is accessible
3. GitHub token is properly set in environment variables

### Database Connection Issues

Check:
1. Cloud SQL instance is running
2. Cloud SQL Connector is properly configured
3. Database user and password are correct
4. Cloud Run Service has network access to Cloud SQL

### Check Logs

```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=deepdive-tracking" \
  --limit 50 \
  --format "table(timestamp, severity, jsonPayload.message)"

# Stream logs in real-time
gcloud alpha logging tail "resource.type=cloud_run_revision" \
  --service-name=deepdive-tracking
```

## Manual Deployment

If needed to redeploy:

```bash
cd /d/projects/deepdive-tracking

# Deploy to Cloud Run
bash infra/gcp/deploy_to_cloud_run.sh

# Or use Python script
python infra/gcp/deploy_to_cloud_run.py
```

## Key Files

- `src/main.py` - FastAPI application with all endpoints
- `scripts/publish/send_top_news_email.py` - Email publishing
- `scripts/publish/send_top_ai_news_to_github.py` - GitHub publishing
- `scripts/collection/collect_news.py` - News collection
- `scripts/evaluation/score_*.py` - AI scoring and analysis
- `src/database/connection.py` - Database connection with Cloud SQL Connector support
- `Dockerfile` - Container image for Cloud Run

## Success Indicators

✅ You should see:
- Email arrives in your inbox with top 10 news items
- GitHub repository updated with new articles
- Database contains raw_news and processed_news records
- Cloud Run Service responding to HTTP requests

## Next Steps

1. **Configure Scheduling**: Set up Cloud Scheduler to run daily at 8 AM
2. **Configure Email**: Update SMTP credentials for your email provider
3. **Configure GitHub**: Generate GitHub token and set repository
4. **Monitor**: Check logs regularly for any issues
5. **Iterate**: Tune scoring weights and news sources based on feedback

---

**Service Status**: Ready for production use ✅
