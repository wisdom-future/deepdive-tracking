# 测试规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 测试优先开发（TDD）
✅ 测试覆盖率 > 85%
✅ 快速反馈循环
✅ 测试即文档
✅ 自动化所有测试
```

---

## 测试金字塔

```
        /\
       /  \ End-to-End Tests (10%)
      /    \
     /------\
    /  \     Integration Tests (20%)
   /    \   /
  /------\ /
 /  Unit   \/ Tests (70%)
/__________\
```

- **Unit Tests (70%):** 快速，隔离，可靠
- **Integration Tests (20%):** 测试模块间交互
- **E2E Tests (10%):** 真实用户场景

---

## 单元测试规范

### 🔴 MUST - 严格遵守

1. **测试文件位置和命名**
   ```
   src/services/content/manager.py
   →
   tests/unit/services/content/test_manager.py

   ✅ 目录结构完全对应
   ❌ tests/test_content_manager.py (扁平结构)
   ❌ src/services/content/test_manager.py (混入源代码)
   ```

2. **测试函数命名规范**
   ```python
   ✅ def test_get_content_returns_content_when_exists():
   ✅ def test_get_content_raises_error_when_not_found():
   ✅ def test_create_content_saves_to_database():
   ✅ def test_validate_content_accepts_valid_data():

   ❌ def test_content():
   ❌ def test_get():
   ❌ def testGetContent():
   ```

3. **AAA 模式：Arrange-Act-Assert**
   ```python
   def test_get_content_returns_content():
       # Arrange: 准备测试数据
       content_id = 123
       expected_content = Content(id=123, title="Test")
       mock_db.query.return_value.filter_by.return_value.first.return_value = expected_content

       # Act: 执行被测试的代码
       result = service.get(content_id)

       # Assert: 验证结果
       assert result.id == expected_content.id
       assert result.title == expected_content.title
   ```

4. **一个测试验证一个行为**
   ```python
   ✅ def test_create_content_saves_title():
           content = create_content(title="Test")
           assert content.title == "Test"

   ✅ def test_create_content_sets_status_to_draft():
           content = create_content()
           assert content.status == "draft"

   ❌ def test_create_content():
           content = create_content(title="Test", category="AI")
           assert content.title == "Test"
           assert content.category == "AI"
           assert content.status == "draft"
           assert content.created_at is not None
           (验证太多行为)
   ```

5. **使用 Fixtures 管理测试数据**
   ```python
   @pytest.fixture
   def content_manager(db_session):
       """内容管理器 fixture。"""
       return ContentManager(db_session)

   @pytest.fixture
   def sample_content():
       """示例内容 fixture。"""
       return Content(
           id=123,
           title="Test",
           body="Content body",
           category="AI",
           score=85
       )

   def test_get_content(content_manager, sample_content):
       # 使用 fixtures
       result = content_manager.get(sample_content.id)
       assert result.title == sample_content.title
   ```

6. **使用 Mock 隔离被测试的代码**
   ```python
   from unittest.mock import Mock, patch, MagicMock

   def test_create_content_calls_ai_service():
       # Mock 外部服务
       ai_service = Mock()
       ai_service.score.return_value = 85

       service = ContentService(ai_service=ai_service)
       content = service.create(title="Test")

       # 验证 AI 服务被调用
       ai_service.score.assert_called_once()
       assert content.score == 85
   ```

7. **测试异常情况**
   ```python
   def test_get_content_raises_error_when_not_found():
       with pytest.raises(ContentNotFoundError):
           service.get(999)  # 不存在的ID

   def test_create_content_raises_error_with_invalid_data():
       with pytest.raises(ValidationError):
           service.create(title="", body="")  # 无效数据
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 Parametrize 测试多个场景**
   ```python
   @pytest.mark.parametrize("score,expected", [
       (0, "very low"),
       (50, "medium"),
       (100, "very high"),
   ])
   def test_score_rating(score, expected):
       assert rate_score(score) == expected
   ```

2. **测试边界条件**
   ```python
   def test_score_validation():
       assert validate_score(0)      # 最小值
       assert validate_score(100)    # 最大值
       assert not validate_score(-1)  # 超出范围
       assert not validate_score(101) # 超出范围
   ```

---

## 集成测试规范

### 🔴 MUST - 严格遵守

1. **测试文件位置**
   ```
   tests/integration/test_api_workflow.py
   tests/integration/test_database.py
   tests/integration/test_services.py
   ```

2. **使用真实或测试数据库**
   ```python
   @pytest.fixture(scope="session")
   def test_db():
       """创建测试数据库。"""
       # 使用测试数据库，不是生产数据库
       engine = create_engine("sqlite:///:memory:")
       Base.metadata.create_all(engine)
       yield engine
       Base.metadata.drop_all(engine)

   def test_create_and_retrieve_content(test_db):
       # 使用真实数据库，测试实际交互
       session = SessionLocal(bind=test_db)
       service = ContentService(session)
       content = service.create(title="Test")
       retrieved = service.get(content.id)
       assert retrieved.title == "Test"
   ```

3. **测试 API 端点**
   ```python
   from fastapi.testclient import TestClient

   def test_get_content_endpoint(client: TestClient):
       response = client.get("/api/v1/contents/123")
       assert response.status_code == 200
       data = response.json()
       assert data["id"] == 123

   def test_create_content_endpoint(client: TestClient):
       response = client.post(
           "/api/v1/contents",
           json={
               "title": "Test",
               "body": "Content",
               "category": "AI"
           }
       )
       assert response.status_code == 201
       data = response.json()
       assert data["title"] == "Test"
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 conftest.py 共享 fixtures**
   ```python
   # tests/conftest.py
   @pytest.fixture
   def client():
       """FastAPI测试客户端。"""
       from fastapi.testclient import TestClient
       from src.main import app
       return TestClient(app)

   @pytest.fixture
   def db_session():
       """数据库会话 fixture。"""
       engine = create_engine("sqlite:///:memory:")
       Base.metadata.create_all(engine)
       session = SessionLocal(bind=engine)
       yield session
       session.close()
   ```

---

## E2E 测试规范

### 🔴 MUST - 严格遵守

1. **测试完整的用户流程**
   ```python
   # tests/e2e/test_complete_workflow.py
   def test_news_to_publication_workflow():
       # 1. 创建原始新闻
       news = create_raw_news(
           title="OpenAI发布GPT-4",
           content="...",
           source="openai.com"
       )
       assert news.id > 0

       # 2. AI评分和分类
       content = ai_service.process(news)
       assert 0 <= content.score <= 100
       assert content.category in VALID_CATEGORIES

       # 3. 人工审核
       review = create_review(
           content_id=content.id,
           decision="approved",
           comment="Good quality"
       )
       assert review.status == "approved"

       # 4. 发布到多渠道
       for channel in ["wechat", "xiaohongshu", "web"]:
           result = publish(content.id, channel)
           assert result.success
   ```

2. **使用测试数据工厂**
   ```python
   # tests/fixtures/factories.py
   class NewsFactory:
       @staticmethod
       def create(title="Test News", **kwargs):
           return News(
               title=title,
               content=kwargs.get("content", "Default content"),
               source=kwargs.get("source", "test-source"),
               created_at=datetime.now()
           )

   # 使用
   def test_workflow(db_session):
       news = NewsFactory.create(title="Custom Title")
       db_session.add(news)
       db_session.commit()
   ```

---

## 测试覆盖率要求

### 🔴 MUST - 严格遵守

1. **最小覆盖率 85%**
   ```bash
   # 运行测试并检查覆盖率
   pytest --cov=src --cov-fail-under=85

   # 生成HTML覆盖率报告
   pytest --cov=src --cov-report=html
   open htmlcov/index.html
   ```

2. **关键路径覆盖率 95%+**
   ```python
   # 关键业务逻辑必须有高覆盖率
   # - 内容评分逻辑
   # - 发布工作流
   # - 用户认证和授权
   # - 数据验证
   ```

3. **不计入覆盖率的代码**
   ```python
   # 使用 pragma: no cover 标记不需要测试的代码
   if __name__ == "__main__":  # pragma: no cover
       main()

   except Exception:  # pragma: no cover
       pass  # 不太可能出现的异常
   ```

### 🟡 SHOULD - 强烈建议

1. **分析未覆盖的代码**
   ```bash
   # 查看哪些代码未被覆盖
   coverage report
   coverage html

   # 检查特定文件
   coverage report src/services/content/manager.py
   ```

---

## 测试执行规范

### 🔴 MUST - 严格遵守

1. **使用 pytest 框架**
   ```bash
   # 运行所有测试
   pytest

   # 运行特定文件
   pytest tests/unit/services/test_content.py

   # 运行特定测试
   pytest tests/unit/services/test_content.py::test_get_content

   # 运行带某个标记的测试
   pytest -m "not slow"

   # 显示打印输出
   pytest -s
   ```

2. **使用 pytest 配置文件**
   ```ini
   # pytest.ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts = --strict-markers --tb=short
   ```

3. **测试必须能并行运行**
   ```bash
   # 使用 pytest-xdist 并行运行
   pytest -n auto
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 pytest-cov 生成覆盖率报告**
   ```bash
   pytest --cov=src --cov-report=term-missing --cov-report=html
   ```

2. **使用 pytest-benchmark 进行性能测试**
   ```python
   def test_content_processing_performance(benchmark):
       result = benchmark(process_content, large_dataset)
       assert result.success
   ```

---

## 测试数据管理

### 🔴 MUST - 严格遵守

1. **不使用生产数据测试**
   ```python
   ✅ # 使用测试数据库
      engine = create_engine("sqlite:///:memory:")

   ❌ # 连接到生产数据库
      engine = create_engine(os.getenv("DATABASE_URL"))
   ```

2. **每个测试必须独立**
   ```python
   ✅ def test_create_content(db_session):
           # 每个测试都有独立的数据库会话
           content = create_content(db_session)
           assert content.id > 0
           # 测试结束后自动回滚

   ❌ def test_create_content():
           content1 = create_content()
           content2 = create_content()
           # content1的数据影响content2
   ```

3. **使用 fixtures 清理测试数据**
   ```python
   @pytest.fixture
   def db_session():
       session = SessionLocal()
       yield session
       session.rollback()  # 清理
       session.close()
   ```

---

## Mock 和 Stub 规范

### 🔴 MUST - 严格遵守

1. **使用 Mock 隔离外部依赖**
   ```python
   from unittest.mock import Mock, patch

   def test_create_content_calls_ai_service(db_session):
       # Mock AI服务
       with patch('src.services.content.ai_service') as mock_ai:
           mock_ai.score.return_value = 85
           service = ContentService(db_session)
           content = service.create(title="Test")

           # 验证调用
           mock_ai.score.assert_called_once()
           assert content.score == 85
   ```

2. **不要过度 Mock**
   ```python
   ❌ # 过度mocking，失去了集成测试的意义
      def test_workflow():
          mock_db = Mock()
          mock_ai = Mock()
          mock_cache = Mock()
          mock_queue = Mock()
          # 所有依赖都mocked...

   ✅ # 只mock外部服务
      def test_workflow(db_session):
          with patch('requests.get') as mock_http:
              mock_http.return_value.text = "data"
              result = process_data()
              assert result.success
   ```

---

## 测试检查清单

提交代码前检查：

- [ ] 所有新代码都有相应的测试
- [ ] 测试覆盖率 > 85%
- [ ] 所有测试通过
- [ ] 没有跳过的测试（xfail, skip）
- [ ] 测试命名清晰描述功能
- [ ] 使用了 AAA 模式
- [ ] Mock 正确隔离外部依赖
- [ ] 测试数据使用 fixtures
- [ ] 没有硬编码的测试数据
- [ ] 测试能并行运行
- [ ] 性能关键路径有性能测试

---

**记住：** 好的测试是你的安全网。它让你放心地重构和优化代码。测试写得好，就写得好；写得差，就成了累赘。投入时间写好测试。

