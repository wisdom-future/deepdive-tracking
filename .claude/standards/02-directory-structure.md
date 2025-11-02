# 目录结构规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 源代码必须在 src/ 下
✅ 测试代码必须在 tests/ 下
✅ 文档必须在 docs/ 下
✅ 规范和配置必须在 .claude/ 下
✅ 不允许在其他位置创建代码
```

---

## 完整目录树

```
deepdive-tracking/
│
├── 📄 CLAUDE.md                    ← 项目规范入口
├── 📄 .env.example                 ← 环境变量模板
├── 📄 .gitignore                   ← Git忽略规则
├── 📄 .pre-commit-config.yaml      ← Pre-commit配置
├── 📄 docker-compose.yml           ← 本地开发环境
├── 📄 Makefile                     ← 常用命令
├── 📄 README.md                    ← 项目说明
├── 📄 LICENSE                      ← 许可证
│
├── src/                            ← ✅ 所有源代码
│   ├── __init__.py
│   ├── main.py                     ← 应用入口
│   ├── config/                     ← 配置管理
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── dev.py
│   │   ├── test.py
│   │   └── prod.py
│   ├── api/                        ← API层
│   │   ├── __init__.py
│   │   ├── router.py               ← 路由汇聚
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── error_handler.py
│   │   │   └── logging.py
│   │   └── v1/                     ← 版本隔离
│   │       ├── __init__.py
│   │       ├── endpoints/
│   │       │   ├── __init__.py
│   │       │   ├── contents.py
│   │       │   ├── sources.py
│   │       │   ├── review.py
│   │       │   ├── publishing.py
│   │       │   └── analytics.py
│   │       ├── schemas/
│   │       │   ├── __init__.py
│   │       │   ├── content.py
│   │       │   ├── source.py
│   │       │   ├── common.py
│   │       │   └── error.py
│   │       └── dependencies.py
│   │
│   ├── services/                   ← 业务逻辑层
│   │   ├── __init__.py
│   │   ├── collection/
│   │   │   ├── __init__.py
│   │   │   ├── collector.py
│   │   │   ├── rss_collector.py
│   │   │   ├── web_crawler.py
│   │   │   └── deduplicator.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── processor.py
│   │   │   ├── models.py
│   │   │   ├── prompts.py
│   │   │   └── router.py
│   │   ├── content/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py
│   │   │   ├── review.py
│   │   │   └── editor.py
│   │   └── publishing/
│   │       ├── __init__.py
│   │       ├── publisher.py
│   │       ├── channels/
│   │       │   ├── __init__.py
│   │       │   ├── wechat.py
│   │       │   ├── xiaohongshu.py
│   │       │   └── web.py
│   │       └── scheduler.py
│   │
│   ├── models/                     ← 数据模型
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── data_source.py
│   │   ├── raw_news.py
│   │   ├── processed_news.py
│   │   ├── content_review.py
│   │   ├── published_content.py
│   │   └── statistics.py
│   │
│   ├── database/                   ← 数据库操作
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── session.py
│   │   └── migrations/
│   │       ├── __init__.py
│   │       ├── env.py
│   │       └── versions/
│   │
│   ├── cache/                      ← 缓存管理
│   │   ├── __init__.py
│   │   ├── redis_client.py
│   │   └── decorators.py
│   │
│   ├── tasks/                      ← 异步任务
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── collection_tasks.py
│   │   ├── ai_tasks.py
│   │   ├── publishing_tasks.py
│   │   └── analytics_tasks.py
│   │
│   ├── utils/                      ← 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── validators.py
│   │   ├── decorators.py
│   │   ├── exceptions.py
│   │   ├── helpers.py
│   │   └── constants.py
│   │
│   └── __init__.py
│
├── tests/                          ← ✅ 所有测试代码
│   ├── conftest.py                 ← pytest配置和fixtures
│   ├── __init__.py
│   ├── unit/                       ← 单元测试
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── test_contents.py
│   │   │   ├── test_sources.py
│   │   │   └── test_review.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── collection/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_collector.py
│   │   │   │   └── test_deduplicator.py
│   │   │   ├── ai/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_processor.py
│   │   │   │   └── test_router.py
│   │   │   └── publishing/
│   │   │       ├── __init__.py
│   │   │       └── test_publisher.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── test_content.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── test_validators.py
│   │       └── test_helpers.py
│   ├── integration/                ← 集成测试
│   │   ├── __init__.py
│   │   ├── test_api_workflow.py
│   │   ├── test_database.py
│   │   └── test_services.py
│   ├── fixtures/                   ← 测试数据和模拟
│   │   ├── __init__.py
│   │   ├── factories.py             ← 数据工厂
│   │   └── mocks.py                 ← Mock对象
│   └── e2e/                        ← 端到端测试
│       ├── __init__.py
│       └── test_complete_workflow.py
│
├── docs/                           ← ✅ 所有文档
│   ├── README.md
│   ├── CONTRIBUTING.md
│   ├── product/                    ← 产品相关文档
│   │   └── requirements.md
│   ├── tech/                       ← 技术文档
│   │   ├── architecture.md
│   │   ├── architecture-diagrams.md
│   │   ├── api-design.md
│   │   ├── database-schema.md
│   │   └── system-design-summary.md
│   ├── content/                    ← 内容管理文档
│   ├── operations/                 ← 运维文档
│   ├── api/                        ← API文档
│   ├── development/                ← 开发文档
│   └── images/                     ← 文档图片
│
├── .claude/                        ← ✅ 规范和配置
│   ├── standards-architecture.md   ← 规范架构设计
│   ├── standards/                  ← 规范文档库
│   │   ├── 00-overview.md
│   │   ├── 01-project-setup.md
│   │   ├── 02-directory-structure.md
│   │   ├── 03-naming-conventions.md
│   │   ├── 04-python-code-style.md
│   │   ├── 05-api-design.md
│   │   ├── 06-database-design.md
│   │   ├── 07-testing-standards.md
│   │   ├── 08-git-workflow.md
│   │   ├── 09-documentation.md
│   │   ├── 10-security.md
│   │   ├── 11-deployment.md
│   │   └── 99-quick-reference.md
│   ├── tools/                      ← 自动化工具
│   │   ├── setup-standards.sh
│   │   ├── check-all.sh
│   │   ├── auto-fix.sh
│   │   ├── health-check.sh
│   │   └── validate-commit.sh
│   ├── hooks/                      ← Git hooks
│   │   ├── pre-commit-config.yaml
│   │   ├── install-hooks.sh
│   │   └── commit-msg-validator.py
│   ├── templates/                  ← 代码模板
│   │   ├── api/
│   │   │   ├── endpoint.py.template
│   │   │   ├── schema.py.template
│   │   │   └── test_endpoint.py.template
│   │   ├── service/
│   │   │   ├── service.py.template
│   │   │   └── test_service.py.template
│   │   ├── model/
│   │   │   └── model.py.template
│   │   ├── database/
│   │   │   ├── migration.py.template
│   │   │   └── test_migration.py.template
│   │   └── docs/
│   │       ├── feature.md.template
│   │       ├── api-endpoint.md.template
│   │       └── troubleshooting.md.template
│   └── config/                     ← 工具配置
│       ├── pyproject.toml
│       ├── pytest.ini
│       ├── mypy.ini
│       ├── .pylintrc
│       └── .flake8
│
├── .github/                        ← GitHub Actions
│   ├── workflows/
│   │   ├── lint.yml
│   │   ├── test.yml
│   │   ├── build.yml
│   │   └── deploy.yml
│   └── ISSUE_TEMPLATE/
│
├── infra/                          ← 基础设施代码
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.prod.yml
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── secret.yaml
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── scripts/                        ← 工具脚本
│   ├── setup.sh
│   ├── lint.sh
│   ├── test.sh
│   ├── build.sh
│   └── migrate.sh
│
└── pyproject.toml / setup.py      ← Python项目配置
```

---

## 目录规则

### 🔴 MUST - 严格遵守

1. **源代码位置**
   ```
   ✅ src/services/collector.py
   ❌ services/collector.py
   ❌ collectors/collector.py
   ❌ collector.py (在根目录)
   ```

2. **测试位置**
   ```
   ✅ tests/unit/services/test_collector.py
   ❌ src/services/test_collector.py
   ❌ tests/test_collector.py
   ❌ test_collector.py (在根目录)
   ```

3. **目录结构对称性**
   ```
   src/services/collection/collector.py
   tests/unit/services/collection/test_collector.py
   ↑ 目录结构必须对应
   ```

4. **模块深度限制**
   ```
   ✅ src/services/ai/processor.py         (3层)
   ✅ src/services/ai/models/gpt_model.py (4层，可接受)
   ❌ src/a/b/c/d/e/f/file.py             (过深，不允许)
   ```

5. **每个目录都必须有 __init__.py**
   ```
   ✅ src/
       ├── __init__.py
       ├── services/
       │   ├── __init__.py
       │   └── collection/
       │       ├── __init__.py
       │       └── collector.py
   ```

### 🟡 SHOULD - 强烈建议

1. **相关功能聚集**
   - 同功能的文件应该放在同一目录下
   - 避免分散到多个位置

2. **命名要有含义**
   - 目录名应该反映内容
   - `utils/` 内的文件应该是真正的工具函数

3. **逻辑隔离**
   - API层和服务层明确分离
   - 数据库操作封装在database/目录

---

## 不允许的位置

```
❌ 项目根目录创建Python文件
❌ 混合源代码和测试代码
❌ 在src/下创建tests/
❌ 在tests/下创建src/
❌ 随意创建新的一级目录
❌ 将不同层的代码混放
```

---

## 添加新功能时的步骤

```
1️⃣  确定功能属于哪一层
    API / Service / Model / Task / etc.

2️⃣  在对应目录创建模块
    src/services/new_feature/
    ├── __init__.py
    ├── manager.py
    └── processor.py

3️⃣  在tests/unit下创建对应测试
    tests/unit/services/new_feature/
    ├── __init__.py
    ├── test_manager.py
    └── test_processor.py

4️⃣  验证结构一致
    src/services/new_feature/X.py
    tests/unit/services/new_feature/test_X.py
    ↑ 路径应该对应
```

---

## 检查清单

- [ ] 源代码都在 src/ 下
- [ ] 测试都在 tests/ 下
- [ ] 目录结构 src/ 和 tests/ 对应
- [ ] 每个目录都有 __init__.py
- [ ] 没有无关的一级目录
- [ ] 代码没有混在根目录
