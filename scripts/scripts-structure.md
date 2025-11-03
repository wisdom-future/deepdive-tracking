# Scripts Directory Structure

This directory contains all automation scripts for the DeepDive Tracking project, organized by functionality.

## Directory Organization

```
scripts/
├── collection/          # News collection and data gathering
├── deployment/          # Cloud Run deployment tools
├── evaluation/          # AI scoring and evaluation
├── initialization/      # Database and cache initialization
├── post-verification/   # Publishing verification & post-publish checks
├── publish/             # Publishing and channel management
├── quickstart/          # Quick start automation
├── review/              # Content review and quality control
├── setup/               # Initial setup and configuration scripts
├── tests/               # Test and validation scripts
├── verification/        # Post-review verification
└── scripts-structure.md # This file
```

---

## 🚀 Deployment

**Cloud Run deployment tools**

| Script | Purpose |
|--------|---------|
| `deploy_to_cloud_run.py` | Python-based Cloud Run deployment tool |
| `deploy_to_cloud_run.sh` | Shell-based Cloud Run deployment tool |

### Usage

```bash
# Dry-run mode
python scripts/deployment/deploy_to_cloud_run.py --dry-run

# Actual deployment
python scripts/deployment/deploy_to_cloud_run.py
```

See `docs/deployment/cloud-run-deployment.md` for complete guide.

---

## 🔧 Setup

**Initial project setup and configuration**

| Script | Purpose |
|--------|---------|
| `1_init_data_sources.py` | Initialize news data sources |
| `2_configure_authors.py` | Configure content authors |
| `3_clear_collected_data.py` | Clear historical collected data |
| `fix_data_sources.py` | Fix data source configuration issues |

---

## 📰 Collection

**News collection from configured data sources**

| Script | Purpose |
|--------|---------|
| `collect_news.py` | Main news collection script |
| `diagnose_sources.py` | Diagnose data source connectivity |

---

## ⭐ Evaluation

**AI-powered news scoring and categorization**

| Script | Purpose |
|--------|---------|
| `score_collected_news.py` | Score collected news articles |
| `score_batch.py` | Score a batch of articles |
| `quick_score_10.py` | Quick score for 10 articles (testing) |
| `score_missing.py` | Score articles missing scores |
| `test_api.py` | Test OpenAI API connectivity |

---

## 👁️ Review

**Automated content review and quality control**

| Script | Purpose |
|--------|---------|
| `auto_review_articles.py` | Automatically review scored articles |

---

## ✅ Verification

**Post-review data verification and summary reporting**

| Script | Purpose |
|--------|---------|
| `demo_mock.py` | Demo with mock data |
| `view_summary.py` | View collection summary |
| `verify_phase2.py` | Verify phase 2 completion |

---

## ✅ Post-Verification

**Publishing verification and post-publish checks**

| Script | Purpose |
|--------|---------|
| (Scripts to be added) | Verification after publishing |

---

## 📢 Publishing

**Multi-channel publishing and distribution**

### Configuration Scripts

| Script | Purpose |
|--------|---------|
| `init_publish_priorities.py` | Initialize publishing priorities |
| `show_publish_priorities.py` | Display publishing configuration |
| `show_data_sources.py` | List configured data sources |

### Publishing Scripts

| Script | Purpose |
|--------|---------|
| `send_top_news_email.py` | Send top news via email (individual) |
| `send_top_ai_news_digest.py` | Send consolidated AI news digest (card layout) |
| `send_top_ai_news_to_github.py` | Publish top AI news to GitHub |
| `publish_to_wechat.py` | Publish to WeChat channel |
| `full_wechat_workflow.py` | Full WeChat workflow testing |

### Publishing Priorities

```
1. Email (Priority 10)     ← Highest priority
2. GitHub (Priority 9)     ← Second priority
3. WeChat (Priority 8)     ← Third priority
```

See `docs/guides/priority-publishing.md` for complete guide.

---

## 🗄️ Initialization

**Database and cache initialization**

| Script | Purpose |
|--------|---------|
| `init_media_cache_table.py` | Initialize media cache table |

---

## 🧪 Testing (scripts/tests/)

**Automated test and validation scripts**

All test scripts follow the `test_*.py` naming convention for consistency.

| Script | Purpose |
|--------|---------|
| `test_publishing_priority.py` | Test priority publishing (Email → GitHub → WeChat) |
| `test_e2e_complete.py` | Full end-to-end workflow test (Collection → Scoring → Review → Publishing) |
| `test_publishing_multi_channel.py` | Multi-channel publishing test (WeChat, GitHub, Email) |
| `test_email_verification.py` | Email system verification and testing |
| `test_wechat_publish.py` | Test WeChat publishing functionality |
| `test_html_cleaner.py` | Test HTML cleaning utilities |
| `test_publishing_service.py` | Test publishing service functionality |
| `test_review_service.py` | Test review service functionality |

### Naming Convention

- **Prefix**: All test scripts use `test_` prefix (not `run_`)
- **Format**: `test_<domain>_<function>.py`
  - `test_e2e_complete.py` - End-to-end tests
  - `test_publishing_priority.py` - Priority publishing tests
  - `test_publishing_multi_channel.py` - Multi-channel publishing tests
  - `test_publishing_service.py` - Publishing service unit tests
  - `test_email_verification.py` - Email system tests

### Usage

```bash
# Test publishing with priority (5 articles, dry-run)
python scripts/tests/test_publishing_priority.py 5 --dry-run

# Test publishing with priority (actual)
python scripts/tests/test_publishing_priority.py 5

# Test complete end-to-end workflow
python scripts/tests/test_e2e_complete.py 10

# Test multi-channel publishing
python scripts/tests/test_publishing_multi_channel.py wechat,github,email 5
```

---

## ⚡ Quick Start (quickstart)

**Pre-configured automation workflows**

| Script | Purpose |
|--------|---------|
| `run_all.sh` | Run complete workflow |

---

## 📊 Typical Workflows

### Daily News Processing

```bash
python scripts/collection/collect_news.py
python scripts/evaluation/score_collected_news.py
python scripts/review/auto_review_articles.py
python scripts/publish/show_publish_priorities.py
```

### Setup

```bash
python scripts/setup/1_init_data_sources.py
python scripts/setup/2_configure_authors.py
python scripts/publish/init_publish_priorities.py
```

### Publishing

```bash
python scripts/publish/init_publish_priorities.py
python scripts/tests/test_publishing_priority.py 3 --dry-run
python scripts/tests/test_publishing_priority.py 3
```

### Email Publishing (Consolidated AI News Digest)

```bash
python scripts/publish/send_top_ai_news_digest.py
```

### Deployment

```bash
python scripts/deployment/deploy_to_cloud_run.py --dry-run
python scripts/deployment/deploy_to_cloud_run.py
```

---

## 🎯 Quick Reference

| Phase | Script |
|-------|--------|
| Setup | `scripts/setup/1_init_data_sources.py` |
| Collect | `scripts/collection/collect_news.py` |
| Evaluate | `scripts/evaluation/score_collected_news.py` |
| Review | `scripts/review/auto_review_articles.py` |
| Verify | `scripts/verification/view_summary.py` |
| Publish (Config) | `scripts/publish/init_publish_priorities.py` |
| Publish (Email) | `scripts/publish/send_top_ai_news_digest.py` |
| Publish (GitHub) | `scripts/publish/send_top_ai_news_to_github.py` |
| Publish (WeChat) | `scripts/publish/publish_to_wechat.py` |
| Deploy | `scripts/deployment/deploy_to_cloud_run.py` |
| Test (E2E) | `scripts/tests/test_e2e_complete.py` |
| Test (Priority) | `scripts/tests/test_publishing_priority.py` |

---

## 📝 File Naming Conventions

### Operational Scripts (Business Logic)

- **Publishing**: `send_*.py`, `publish_*.py`
  - Example: `send_top_ai_news_digest.py`, `publish_to_wechat.py`
- **Configuration**: `init_*.py`, `show_*.py`
  - Example: `init_publish_priorities.py`, `show_publish_priorities.py`
- **Data Processing**: `collect_*.py`, `score_*.py`, `auto_*.py`, `verify_*.py`
  - Example: `collect_news.py`, `score_collected_news.py`, `auto_review_articles.py`

### Test Scripts (scripts/tests/)

- **All test scripts**: `test_*.py` prefix (NEVER `run_*`)
  - Example: `test_publishing_priority.py`, `test_e2e_complete.py`

---

## 🔄 Directory Structure and Purpose

### Root-level `tests/` vs `scripts/tests/`

- **`tests/` directory**: Unit tests, integration tests, and E2E tests for the source code (`src/`)
  - Structured as: `tests/unit/`, `tests/integration/`, `tests/e2e/`
  - Tests core business logic and APIs
  - Run with: `pytest tests/`

- **`scripts/tests/` directory**: Workflow and system tests for the automation scripts
  - Tests complete end-to-end workflows (Collection → Scoring → Review → Publishing)
  - Tests multi-channel publishing coordination
  - Tests publishing priority logic
  - Run individually as needed

---

**Last Updated**: 2025-11-03
**Version**: 2.0
