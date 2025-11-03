# Scripts Directory Structure

This directory contains all automation scripts for the DeepDive Tracking project, organized by functionality.

## Directory Organization

```
scripts/
├── 00-deployment/       # Cloud Run deployment tools
├── 00-setup/            # Initial setup and configuration scripts
├── 01-collection/       # News collection and data gathering
├── 02-evaluation/       # AI scoring and evaluation
├── 03-review/           # Content review and quality control
├── 03-verification/     # Post-review verification
├── 04-publish/          # Publishing and channel management
├── 05-verification/     # Publishing verification
├── 06-initialization/   # Database and cache initialization
├── quickstart/          # Quick start automation
├── tests/               # Test and validation scripts
└── README.md            # This file
```

---

## 🚀 Deployment (00-deployment)

**Cloud Run deployment tools**

| Script | Purpose |
|--------|---------|
| `deploy_to_cloud_run.py` | Python-based Cloud Run deployment tool |
| `deploy_to_cloud_run.sh` | Shell-based Cloud Run deployment tool |

### Usage

```bash
# Dry-run mode
python scripts/00-deployment/deploy_to_cloud_run.py --dry-run

# Actual deployment
python scripts/00-deployment/deploy_to_cloud_run.py
```

See `docs/deployment/cloud-run-deployment.md` for complete guide.

---

## 🔧 Setup (00-setup)

**Initial project setup and configuration**

| Script | Purpose |
|--------|---------|
| `1_init_data_sources.py` | Initialize news data sources |
| `2_configure_authors.py` | Configure content authors |
| `3_clear_collected_data.py` | Clear historical collected data |
| `fix_data_sources.py` | Fix data source configuration issues |

---

## 📰 Collection (01-collection)

**News collection from configured data sources**

| Script | Purpose |
|--------|---------|
| `collect_news.py` | Main news collection script |
| `diagnose_sources.py` | Diagnose data source connectivity |

---

## ⭐ Evaluation (02-evaluation)

**AI-powered news scoring and categorization**

| Script | Purpose |
|--------|---------|
| `score_collected_news.py` | Score collected news articles |
| `score_batch.py` | Score a batch of articles |
| `quick_score_10.py` | Quick score for 10 articles (testing) |
| `score_missing.py` | Score articles missing scores |
| `test_api.py` | Test OpenAI API connectivity |

---

## 👁️ Review (03-review)

**Automated content review and quality control**

| Script | Purpose |
|--------|---------|
| `auto_review_articles.py` | Automatically review scored articles |

---

## ✅ Verification (03-verification, 05-verification)

**Data verification and summary reporting**

| Script | Purpose |
|--------|---------|
| `demo_mock.py` | Demo with mock data |
| `view_summary.py` | View collection summary |
| `verify_phase2.py` | Verify phase 2 completion |

---

## 📢 Publishing (04-publish)

**Multi-channel publishing and distribution**

| Script | Purpose |
|--------|---------|
| `init_publish_priorities.py` | Initialize publishing priorities |
| `show_publish_priorities.py` | Display publishing configuration |
| `publish_to_wechat.py` | Publish to WeChat channel |
| `test_wechat_publish.py` | Test WeChat publishing |
| `full_wechat_workflow.py` | Full WeChat workflow testing |
| `show_data_sources.py` | List configured data sources |

### Publishing Priorities

```
1. Email (Priority 10)     ← Highest priority
2. GitHub (Priority 9)     ← Second priority
3. WeChat (Priority 8)     ← Third priority
```

See `docs/guides/priority-publishing.md` for complete guide.

---

## 🗄️ Initialization (06-initialization)

**Database and cache initialization**

| Script | Purpose |
|--------|---------|
| `init_media_cache_table.py` | Initialize media cache table |

---

## 🧪 Testing (tests)

**Automated test and validation scripts**

| Script | Purpose |
|--------|---------|
| `run_priority_publishing_test.py` | Test priority publishing |
| `run_complete_e2e_test.py` | Full end-to-end workflow test |
| `run_multi_channel_publishing_test.py` | Multi-channel publishing test |
| `test_html_cleaner.py` | Test HTML cleaning utilities |
| `test_publishing_service.py` | Test publishing service |
| `test_review_service.py` | Test review service |

### Usage

```bash
# Test publishing (3 articles, dry-run)
python scripts/tests/run_priority_publishing_test.py 3 --dry-run

# Test publishing (actual)
python scripts/tests/run_priority_publishing_test.py 3
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
python scripts/01-collection/collect_news.py
python scripts/02-evaluation/score_collected_news.py
python scripts/03-review/auto_review_articles.py
python scripts/04-publish/show_publish_priorities.py
```

### Setup

```bash
python scripts/00-setup/1_init_data_sources.py
python scripts/00-setup/2_configure_authors.py
python scripts/04-publish/init_publish_priorities.py
```

### Publishing

```bash
python scripts/04-publish/init_publish_priorities.py
python scripts/tests/run_priority_publishing_test.py 3 --dry-run
python scripts/tests/run_priority_publishing_test.py 3
```

### Deployment

```bash
python scripts/00-deployment/deploy_to_cloud_run.py --dry-run
python scripts/00-deployment/deploy_to_cloud_run.py
```

---

## 🎯 Quick Reference

| Phase | Script |
|-------|--------|
| Setup | `scripts/00-setup/1_init_data_sources.py` |
| Collect | `scripts/01-collection/collect_news.py` |
| Evaluate | `scripts/02-evaluation/score_collected_news.py` |
| Review | `scripts/03-review/auto_review_articles.py` |
| Publish | `scripts/04-publish/init_publish_priorities.py` |
| Deploy | `scripts/00-deployment/deploy_to_cloud_run.py` |
| Test | `scripts/tests/run_complete_e2e_test.py` |

---

**Last Updated**: 2025-11-03
**Version**: 1.0
