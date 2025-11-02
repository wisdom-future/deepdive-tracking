# DeepDive Tracking

AI-powered news tracking platform for technology decision makers. Automatically collects, analyzes, and curates AI industry news from multiple sources, delivering daily insights and weekly reports via multiple channels.

## Features

- **Automated News Collection**: Collects 300-500 AI news items daily from RSS feeds and web sources
- **AI-Powered Analysis**: Intelligent scoring (0-100) and categorization (8 categories) using GPT-4o
- **Quality Control**: Human review and curation system for content quality assurance
- **Multi-Channel Publishing**: Distribute curated news to WeChat, Xiaohongshu, and Web
- **Analytics Dashboard**: Track engagement and audience metrics

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Cache**: Redis
- **Task Queue**: Celery
- **AI**: OpenAI GPT-4o
- **Infrastructure**: Docker, Kubernetes, GitHub Actions

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/wisdom-future/deepdive-tracking.git
cd deepdive-tracking
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make dev-install
```

4. Copy environment configuration:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run development server:
```bash
make run
```

The API will be available at `http://localhost:8000`
API docs available at `http://localhost:8000/docs`

## Development

### Code Quality

All code must pass these checks:

```bash
make check-all  # Run all checks
```

Individual checks:
```bash
make format     # Format code with black
make lint       # Run flake8
make type-check # Run mypy
make test       # Run tests
```

### Testing

```bash
make test         # Run all tests with coverage
make test-cov     # Generate HTML coverage report
make test-quick   # Run quick tests (no coverage)
```

### Database

```bash
make migrate      # Run pending migrations
make migrate-new  # Create new migration
make db-drop      # Drop database (dev only)
```

## Project Structure

```
src/
├── config/           # Configuration management
├── api/              # API endpoints
│   └── v1/          # API v1
├── services/         # Business logic
│   ├── collection/  # News collection
│   ├── ai/          # AI processing
│   ├── content/     # Content management
│   └── publishing/  # Multi-channel publishing
├── models/          # Database models
├── database/        # Database operations
├── cache/           # Redis caching
├── tasks/           # Celery tasks
└── utils/           # Utility functions

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
├── fixtures/        # Test data
└── e2e/            # End-to-end tests

docs/
├── product/        # Product documentation
├── tech/           # Technical documentation
└── api/            # API documentation
```

## Documentation

- [Product Requirements](docs/product/requirements.md)
- [Technical Architecture](docs/tech/architecture.md)
- [API Design](docs/tech/api-design.md)
- [Database Schema](docs/tech/database-schema.md)

## Project Standards

This project follows strict standards and conventions documented in `.claude/standards/`. Read:

- [CLAUDE.md](CLAUDE.md) - Project guidelines and standards overview
- [.claude/standards/](`.claude/standards/`) - Detailed standards

Key standards:
- Code must be formatted with Black (max 88 chars)
- All functions must have type hints and docstrings
- Test coverage must be > 85%
- Commits follow Conventional Commits format

## Contributing

Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

- **Team**: DeepDive Team
- **Email**: team@deepdive.com

---

**Version**: 0.1.0 (Alpha)
**Last Updated**: 2025-11-02
