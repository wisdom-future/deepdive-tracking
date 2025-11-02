# DeepDive Tracking - Getting Started Guide

## Quick Start - Running the Complete Workflow Test

### Step 1: Verify Database and Data

The system comes with sample data pre-loaded. Check the database status:

```bash
python -c "
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import get_settings
from src.models import RawNews, ProcessedNews, ContentReview, PublishedContent

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

print('Database Status:')
print(f'  Raw News:        {session.query(RawNews).count():>6d} articles')
print(f'  Scored News:     {session.query(ProcessedNews).count():>6d} articles')
print(f'  Content Reviews: {session.query(ContentReview).count():>6d} articles')
print(f'  Published:       {session.query(PublishedContent).count():>6d} articles')
"
```

### Step 2: Run the Simplified Workflow Test

The easiest way to test the complete workflow is using `test_workflow_simple.py`:

```bash
# Basic usage (processes 5 articles by default)
python test_workflow_simple.py

# Process specific number of articles
python test_workflow_simple.py 10

# With WeChat credentials configured
export WECHAT_APP_ID='wxc3d4bc2d698da563'
export WECHAT_APP_SECRET='e9f5d2a2b2ffe5bc4e23c9904c0021b6'
python test_workflow_simple.py
```

### What the Test Does

The `test_workflow_simple.py` script tests the complete end-to-end workflow with real data:

1. **Step 1: View Collected Articles**
   - Shows recently collected articles
   - Indicates which are already scored

2. **Step 2: AI Scoring**
   - Attempts to score unscored articles
   - If OpenAI API key not configured, gracefully skips and uses existing data
   - Displays scoring statistics

3. **Step 3: Display Scored Articles**
   - Shows sample of scored articles with:
     - AI-generated scores (0-100)
     - Classification (8 categories)
     - Keywords and metadata

4. **Step 4: Auto-Review Workflow**
   - Creates review records for scored articles
   - Auto-approves articles above score threshold (default: 50)
   - Displays review statistics

5. **Step 5: WeChat Publishing**
   - If WeChat credentials configured: attempts to publish
   - If not configured: shows configuration instructions
   - Displays publishing statistics

### Expected Output

```
================================================================================
  DeepDive Tracking - 完整端到端工作流测试
================================================================================

[步骤 1] 查看已采集的文章 (Show Collected Articles)
  找到 118 篇已采集的文章

[步骤 2] AI 评分 (Scoring)
  找到 5 篇待评分的文章
  ⚠️  OpenAI API key 未配置，跳过评分
  将使用已有的 18 篇已评分文章继续工作流

[步骤 3] 显示已评分的文章样本 (Show Scored Articles)
  找到 18 篇已评分的文章

[步骤 4] 自动审核 (Auto Review)
  创建了 13 条审核记录
  ✓ 自动审核完成
    自动批准: 3 篇

[步骤 5] 微信发布 (WeChat Publishing)
  ✓ WeChat 凭证已配置
  ✓ WeChat 发布完成
    成功发布: 2 篇

================================================================================
  工作流执行完成
================================================================================

数据库统计:
  原始新闻:    118 篇
  已评分:      18 篇 (15%)
  已审核:      18 篇
  已发布:       5 篇

✅ 完整工作流测试成功!
```

## Configuration

### API Keys and Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and configure:

#### OpenAI (for AI Scoring)
```
OPENAI_API_KEY=sk-proj-YOUR_API_KEY_HERE
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.3
```

#### WeChat (for Publishing)
```
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
```

### Environment Variables

Set via command line:

```bash
# WeChat
export WECHAT_APP_ID='wxc3d4bc2d698da563'
export WECHAT_APP_SECRET='e9f5d2a2b2ffe5bc4e23c9904c0021b6'

# OpenAI
export OPENAI_API_KEY='sk-proj-YOUR_KEY'
```

## Data Flow

```
Raw Articles (118 total)
    ↓
[Collection: RSS feeds collected - DONE]
    ↓
[Scoring: AI evaluates quality - 18/118 scored]
    ├─ Score: 0-100
    ├─ Category: 8 categories
    └─ Keywords: Extracted entities
    ↓
[Auto-Review: Rule-based approval - 18/18 reviewed]
    ├─ Auto-approve if score >= 50
    └─ Manual review for score < 50
    ↓
[Publishing: Multi-channel publish - 5/8 published]
    ├─ WeChat Official Account
    ├─ XiaoHongShu (future)
    └─ Web Platform (future)
```

## Next Steps

### 1. Score All Articles (Optional)
If you have OpenAI API key configured:

```bash
export OPENAI_API_KEY='sk-proj-YOUR_KEY'
python scripts/02-evaluation/score_collected_news.py 50
```

### 2. View Detailed Analysis
```bash
python scripts/03-verification/view_summary.py
```

### 3. Manual Review of Articles
The UI/API will allow manual review of:
- Articles awaiting approval
- Articles with confidence < 70%
- Articles in specific categories

### 4. Configure Publishing Channels

#### WeChat
1. Add WeChat Official Account credentials to `.env`
2. Whitelist your IP address in WeChat backend
3. Run test: `python test_workflow_simple.py`

#### XiaoHongShu (Future)
```env
XIAOHONGSHU_API_URL=https://api.xiaohongshu.com
XIAOHONGSHU_TOKEN=your_token
```

## Troubleshooting

### "OpenAI API key not configured"
- Add `OPENAI_API_KEY` to `.env` or export as environment variable
- Test script gracefully handles this and uses existing data

### "WeChat credentials not configured"
- Add `WECHAT_APP_ID` and `WECHAT_APP_SECRET` to `.env`
- Or export as environment variables
- Ensure IP whitelist is configured in WeChat backend

### SQLAlchemy Row Binding Error
- Make sure you're using Python 3.8+
- Update SQLAlchemy: `pip install --upgrade sqlalchemy`

### Database Issues
- Check that database file exists: `data/db/deepdive_tracking.db`
- Run migrations if needed: `alembic upgrade head`

## Architecture Overview

### Services Layer

```
src/services/
├── ai/                    # AI evaluation
│   └── scoring_service.py
├── collection/            # Data collection
│   └── collection_manager.py
├── review/               # Content review
│   └── review_service.py
├── publishing/           # Publishing to channels
│   └── publishing_service.py
├── channels/             # Channel integrations
│   ├── wechat_channel.py
│   └── xiaohongshu_channel.py (planned)
└── workflow/             # High-level orchestration
    ├── auto_review_workflow.py
    └── wechat_workflow.py
```

### Models

```
src/models/
├── raw_news.py           # Collected articles
├── processed_news.py     # Scored articles
├── content_review.py     # Review records
└── published_content.py  # Published records
```

### Test Scripts

```
test_workflow_simple.py   # Main entry point - uses existing data
test_complete_workflow.py # Full workflow including collection
scripts/
├── 01-collection/        # Article collection
├── 02-evaluation/        # AI scoring
├── 03-verification/      # Results viewing
└── 04-publish/          # Publishing
```

## Performance Metrics

From the last test run:
- **Collection**: 118 articles collected
- **Scoring**: 18 articles (15%) scored, ~$0.30 cost
- **Review**: 18 articles reviewed, 22.2% approval rate
- **Publishing**: 2-5 articles published per run

## Additional Resources

- Product Requirements: `docs/product/requirements.md`
- System Design: `docs/tech/system-design-summary.md`
- API Reference: `docs/tech/architecture.md`
- Project Standards: `CLAUDE.md`

## Support

For issues or questions:
1. Check the logs in the test output
2. Review the project standards in `CLAUDE.md`
3. Check the architecture documentation in `docs/`

Good luck with the complete workflow test! 🚀
