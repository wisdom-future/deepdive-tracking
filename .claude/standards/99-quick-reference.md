# 快速参考卡片

**用途：** 快速查找常用规范
**阅读时间：** 5-10分钟
**更新频率：** 每周

---

## ⚡ 最常用的10条规范

```
1️⃣  代码必须通过 black 格式化 (max-line-length=88)
    black src/

2️⃣  所有函数都要有类型注解和 docstring
    def process(x: int) -> str:
        """处理输入"""

3️⃣  文件名用 snake_case，类名用 PascalCase
    file_name.py vs class ClassName

4️⃣  提交信息遵循 Conventional Commits
    feat(module): add new feature

5️⃣  分支名: feature/XXX-short-desc
    feature/001-add-rss-parser

6️⃣  所有代码通过检查: black, flake8, mypy, pytest
    bash .claude/tools/check-all.sh

7️⃣  测试覆盖率 > 85%
    pytest --cov=src --cov-fail-under=85

8️⃣  没有硬编码密钥或密码
    from os import getenv; API_KEY = getenv('OPENAI_API_KEY')

9️⃣  源代码在 src/，测试在 tests/，文档在 docs/
    严格遵守目录结构

🔟  所有 MUST 规范无例外遵守
    MUST = 代码无法merge
```

---

## 📋 命名速查表

### 文件和目录
```
✅ content_manager.py          (源文件)
✅ test_content_manager.py     (测试文件)
✅ __init__.py                 (包标记)
❌ ContentManager.py           (错误)
❌ content-manager.py          (错误)
```

### 类、函数、变量
```
✅ class ContentManager
✅ def process_content()
✅ user_id = 123
✅ is_active = True
❌ class contentManager
❌ def ProcessContent()
❌ userId = 123
```

### 常量和配置
```
✅ MAX_RETRY_COUNT = 3
✅ DEFAULT_TIMEOUT = 30
✅ DATABASE_URL = getenv('DATABASE_URL')
❌ max_retry_count = 3
❌ maxRetryCount = 3
```

### 数据库
```
✅ CREATE TABLE data_sources (...)
✅ ALTER TABLE raw_news ADD COLUMN created_at ...
✅ CREATE INDEX idx_raw_news_source_id ...
❌ CREATE TABLE DataSources
❌ ALTER TABLE RawNews
```

### API路由
```
✅ GET    /api/v1/contents
✅ GET    /api/v1/contents/{id}
✅ POST   /api/v1/admin/review/{id}/decision
✅ DELETE /api/v1/admin/sources/{id}
❌ GET    /api/v1/get_contents
❌ GET    /api/v1/contents_by_id
```

---

## 💻 代码模板速查

### API端点
```python
from fastapi import APIRouter, HTTPException
from src.api.v1.schemas.content import ContentResponse

router = APIRouter(prefix="/contents", tags=["contents"])

@router.get("/{id}")
async def get_content(id: int) -> ContentResponse:
    """获取内容详情"""
    try:
        content = await service.get(id)
        return ContentResponse(**content.dict())
    except ContentNotFoundError:
        raise HTTPException(status_code=404)
```

### 服务类
```python
class ContentService:
    """内容服务"""

    def __init__(self, db_session):
        self.db_session = db_session

    def get(self, content_id: int) -> Content:
        """获取内容"""
        result = self.db_session.query(Content).filter_by(id=content_id).first()
        if not result:
            raise ContentNotFoundError(f"Content {content_id} not found")
        return result
```

### 单元测试
```python
import pytest
from src.services.content import ContentService

class TestContentService:
    @pytest.fixture
    def service(self):
        return ContentService(db_session=Mock())

    def test_get_returns_content(self, service):
        result = service.get(1)
        assert result is not None

    def test_get_raises_error_if_not_found(self, service):
        with pytest.raises(ContentNotFoundError):
            service.get(999)
```

---

## 🌳 Git工作流速查

### 创建分支
```bash
# 确保在develop分支
git checkout develop
git pull origin develop

# 创建feature分支
git checkout -b feature/001-add-rss-parser

# 或 bugfix/hotfix
git checkout -b bugfix/fix-timeout-error
```

### 提交代码
```bash
# 提交信息格式
git commit -m "feat(collection): add RSS feed parser"

# ✅ 正确的类型
feat, fix, refactor, test, docs, chore, perf, ci, style, revert

# ✅ 正确的scope
collection, ai, content, publishing, api, database, cache, auth, config

# ✅ 提交前检查
bash .claude/tools/check-all.sh
```

### 创建PR
```bash
git push origin feature/001-add-rss-parser

# 然后创建PR
# 标题: [FEATURE] 清晰的描述
# 描述: 包括背景、改动、测试方案
```

### Merge前
```
□ 通过所有自动检查 (GitHub Actions)
□ 至少1个reviewer审核
□ 所有对话已解决
□ 分支是最新的 (与develop同步)
```

---

## 🧪 测试速查

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/unit/services/test_content.py

# 运行并显示覆盖率
pytest --cov=src

# 强制覆盖率大于85%
pytest --cov=src --cov-fail-under=85

# 显示未覆盖的行
pytest --cov=src --cov-report=html
```

### 测试结构
```
tests/
├── unit/                    (单元测试)
│   ├── services/
│   ├── models/
│   ├── utils/
│   └── api/
├── integration/             (集成测试)
└── e2e/                     (端到端测试)
```

### 测试命名
```
✅ test_get_content_returns_content
✅ test_get_content_raises_error_if_not_found
✅ test_create_with_valid_data_saves_to_db
❌ test_content
❌ test_function
```

---

## 🔧 工具命令速查

### 环境初始化
```bash
# 一键初始化环境
bash .claude/tools/setup-standards.sh

# 安装Git hooks
bash .claude/hooks/install-hooks.sh
```

### 代码检查和修复
```bash
# 检查所有规范
bash .claude/tools/check-all.sh

# 自动修复规范问题
bash .claude/tools/auto-fix.sh

# 只查看问题，不修复
bash .claude/tools/check-all.sh --dry-run

# 项目健康检查
bash .claude/tools/health-check.sh
```

### 手动检查
```bash
# 格式化代码
black src/ tests/

# 风格检查
flake8 src/ tests/

# 类型检查
mypy src/

# 运行测试
pytest --cov=src --cov-fail-under=85
```

---

## 📁 目录结构速查

### 必须遵守的目录
```
src/                    所有源代码
├── main.py
├── config/
├── api/
├── services/
├── models/
├── database/
├── cache/
├── tasks/
├── utils/
└── __init__.py

tests/                  所有测试
├── unit/
├── integration/
└── fixtures/

docs/                   所有文档
├── README.md
├── product/
├── tech/
└── ...

.claude/                规范和配置
├── standards/
├── tools/
├── templates/
├── hooks/
└── config/
```

### 不允许的位置
```
❌ project_root/some_module.py          (源代码)
❌ project_root/test_something.py       (测试)
❌ random_folder/document.md            (文档)
```

---

## 🔒 安全速查

### ❌ 不要做这些
```python
# ❌ 硬编码密钥
API_KEY = 'sk-1234567890'
PASSWORD = 'admin123'
DATABASE_URL = 'postgresql://user:pass@host'

# ❌ 硬编码敏感配置
DEBUG = True
SECRET_KEY = 'secret'

# ❌ 未验证的用户输入
query = f"SELECT * FROM users WHERE id = {user_id}"

# ❌ 明文存储密码
user.password = user_input_password
```

### ✅ 应该这样做
```python
# ✅ 从环境变量读取
from os import getenv
API_KEY = getenv('OPENAI_API_KEY')
DATABASE_URL = getenv('DATABASE_URL')

# ✅ 参数化查询
from sqlalchemy import text
query = text("SELECT * FROM users WHERE id = :id")
result = db.execute(query, {"id": user_id})

# ✅ 密码哈希
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
hashed = pwd_context.hash(password)
```

---

## 📝 文档速查

### Docstring格式
```python
def create_content(
    news_id: int,
    override_category: Optional[str] = None,
) -> Content:
    """
    从新闻创建内容。

    更详细的说明，可以跨越多行。

    Args:
        news_id: 新闻ID，必须存在
        override_category: 可选，覆盖AI预测

    Returns:
        Content对象

    Raises:
        NewsNotFoundError: 如果新闻不存在
        AIProcessingError: 如果AI处理失败

    Example:
        >>> content = create_content(123)
        >>> print(content.title)
        'OpenAI发布GPT-4o'
    """
    pass
```

### 注释规范
```python
# ✅ 解释"为什么"，而不是"是什么"
# 使用Simhash算法用于快速去重
score = calculate_simhash(content)

# ❌ 冗余的"是什么"注释
x = 1  # 设置x为1
y = x + 1  # y等于x加1

# ✅ 复杂逻辑前的注释
# 计算余弦相似度，阈值0.8为重复
if similarity > 0.8:
    is_duplicate = True
```

---

## 🎯 常见错误和修复

### 错误1：代码未格式化
```bash
# ❌ 问题
def process_data(a,b,c):
    return a+b+c

# ✅ 修复
black src/

# ✅ 结果
def process_data(a, b, c):
    return a + b + c
```

### 错误2：没有类型注解
```bash
# ❌ 问题
def get_content(id):
    return db.query(id)

# ✅ 修复
def get_content(id: int) -> Optional[Content]:
    return db.query(Content).filter_by(id=id).first()
```

### 错误3：分支名不符合规范
```bash
# ❌ 问题
git checkout -b new_feature

# ✅ 修复
git checkout -b feature/001-add-new-feature

# ❌ 问题
git checkout -b fix-bug

# ✅ 修复
git checkout -b bugfix/fix-timeout-issue
```

### 错误4：提交信息不清晰
```bash
# ❌ 问题
git commit -m "fixed stuff"
git commit -m "WIP"

# ✅ 修复
git commit -m "fix(ai): handle timeout error gracefully"
git commit -m "feat(collection): add RSS feed parser support"
```

### 错误5：硬编码密钥
```bash
# ❌ 问题
API_KEY = 'sk-1234567890'

# ✅ 修复
API_KEY = getenv('OPENAI_API_KEY')
# 在 .env 文件中设置
```

---

## ❓ 快速问答

**Q: 我该先看哪个文档？**
A: 本文档 + 00-overview.md + 相关具体规范

**Q: 如何快速修复代码格式问题？**
A: `bash .claude/tools/auto-fix.sh`

**Q: 测试覆盖率不够怎么办？**
A: 运行 `pytest --cov=src --cov-report=html` 查看未覆盖的代码，添加测试

**Q: 我遇到了Git冲突怎么办？**
A: 阅读 08-git-workflow.md 中的冲突处理部分

**Q: 提交被Git hook拒绝了怎么办？**
A: 运行 `bash .claude/tools/auto-fix.sh` 自动修复，然后重新提交

**Q: 我想改进规范怎么办？**
A: 提出Issue或PR，修改 `.claude/standards/` 中的相应文件

---

## 🔗 完整规范导航

| 规范 | 用途 |
|------|------|
| 00-overview.md | 规范导航 |
| 01-project-setup.md | 项目初始化 |
| 02-directory-structure.md | 目录结构 |
| 03-naming-conventions.md | 命名规范 |
| 04-python-code-style.md | Python代码 |
| 05-api-design.md | API设计 |
| 06-database-design.md | 数据库 |
| 07-testing-standards.md | 测试规范 |
| 08-git-workflow.md | Git工作流 |
| 09-documentation.md | 文档规范 |
| 10-security.md | 安全规范 |
| 11-deployment.md | 部署规范 |

---

**最后提醒：**
> 规范的目的是让团队更高效协作。
> 每次遵守规范都是在为项目质量加分！✨

