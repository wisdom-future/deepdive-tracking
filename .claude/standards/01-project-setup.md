# 项目初始化规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 一键初始化本地环境
✅ 依赖版本锁定
✅ 开发工具自动配置
✅ 清晰的步骤说明
✅ 快速诊断环节
```

---

## 系统要求

### 🔴 MUST - 严格遵守

1. **Python 版本**
   ```
   最小版本：Python 3.10
   推荐版本：Python 3.11+
   ❌ 不支持 Python 3.9 及以下
   ```

2. **操作系统**
   ```
   ✅ macOS (Intel/Apple Silicon)
   ✅ Linux (Ubuntu 20.04+, CentOS 8+)
   ✅ Windows 10/11 (使用 WSL 2)
   ```

3. **必要工具**
   ```
   - Git >= 2.30
   - Docker >= 20.10 (可选，用于容器开发)
   - Make >= 3.81 (可选，用于运行Makefile)
   ```

---

## 本地环境初始化

### 🔴 MUST - 严格遵守

1. **快速初始化（推荐）**
   ```bash
   # 克隆仓库
   git clone https://github.com/deepdive-tracking/repo.git
   cd deepdive-tracking

   # 一键初始化
   bash .claude/tools/setup-standards.sh
   ```

2. **手动初始化步骤**

   **Step 1: 创建虚拟环境**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   ```

   **Step 2: 升级 pip**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

   **Step 3: 安装依赖**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

   **Step 4: 安装 Git Hooks**
   ```bash
   bash .claude/hooks/install-hooks.sh
   ```

   **Step 5: 配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入本地配置
   ```

   **Step 6: 初始化数据库**
   ```bash
   # 创建数据库
   createdb deepdive_dev

   # 运行迁移
   alembic upgrade head
   ```

   **Step 7: 验证安装**
   ```bash
   # 运行健康检查
   bash .claude/tools/health-check.sh
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 Docker 容器开发**
   ```bash
   # 构建开发镜像
   docker-compose build

   # 启动开发环境
   docker-compose up -d

   # 进入容器
   docker-compose exec api bash

   # 停止开发环境
   docker-compose down
   ```

---

## 依赖管理

### 🔴 MUST - 严格遵守

1. **requirements.txt（生产依赖）**
   ```
   fastapi==0.104.1
   uvicorn[standard]==0.24.0
   sqlalchemy==2.0.23
   psycopg2-binary==2.9.9
   pydantic==2.5.0
   pydantic-settings==2.1.0
   python-jose[cryptography]==3.3.0
   passlib[bcrypt]==1.7.4
   python-multipart==0.0.6
   aioredis==2.0.1
   celery==5.3.4
   feedparser==6.0.10
   requests==2.31.0
   beautifulsoup4==4.12.2
   ```

2. **requirements-dev.txt（开发依赖）**
   ```
   -r requirements.txt

   # Testing
   pytest==7.4.3
   pytest-cov==4.1.0
   pytest-asyncio==0.21.1
   pytest-xdist==3.5.0
   pytest-benchmark==4.0.0
   pytest-mock==3.12.0

   # Linting & Formatting
   black==23.12.0
   flake8==6.1.0
   mypy==1.7.1
   isort==5.13.2
   pylint==3.0.3

   # Security
   bandit==1.7.5
   safety==2.3.5

   # Development
   ipython==8.18.1
   ipdb==0.13.13
   faker==20.1.0
   factory-boy==3.3.0

   # Documentation
   sphinx==7.2.6
   sphinx-rtd-theme==2.0.0
   ```

3. **安装依赖**
   ```bash
   # 安装生产依赖
   pip install -r requirements.txt

   # 安装开发依赖（包括生产依赖）
   pip install -r requirements-dev.txt

   # 添加新依赖
   pip install package-name
   pip freeze > requirements.txt  # 更新版本锁定
   ```

### 🟡 SHOULD - 强烈建议

1. **使用 Poetry 管理依赖**
   ```bash
   # 初始化Poetry项目
   poetry init

   # 添加依赖
   poetry add fastapi

   # 添加开发依赖
   poetry add --group dev pytest

   # 安装依赖
   poetry install

   # 更新依赖
   poetry update
   ```

---

## IDE 配置

### 🔴 MUST - 严格遵守

1. **VS Code 配置（.vscode/settings.json）**
   ```json
   {
       "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
       "python.linting.enabled": true,
       "python.linting.pylintEnabled": false,
       "python.linting.flake8Enabled": true,
       "python.linting.flake8Args": [
           "--max-line-length=88",
           "--extend-ignore=E203,W503"
       ],
       "python.formatting.provider": "black",
       "python.formatting.blackArgs": [
           "--line-length=88"
       ],
       "[python]": {
           "editor.formatOnSave": true,
           "editor.codeActionsOnSave": {
               "source.organizeImports": "explicit"
           },
           "editor.defaultFormatter": "ms-python.python"
       },
       "mypy.enabled": true,
       "mypy.runUsingActiveInterpreter": true,
       "mypy.args": [
           "--ignore-missing-imports",
           "--show-error-codes"
       ]
   }
   ```

2. **VS Code 扩展推荐**
   ```
   - Python (ms-python.python)
   - Pylance (ms-python.vscode-pylance)
   - Flake8 (ms-python.flake8)
   - MyPy (ms-python.mypy-type-checker)
   - Black Formatter (ms-python.black-formatter)
   - Isort (ms-python.isort)
   - Git Graph (mhutchie.git-graph)
   - Docker (ms-vscode.docker)
   - SQLTools (mtxr.sqltools)
   ```

3. **PyCharm 配置**
   ```
   - Settings > Project > Python Interpreter
     选择虚拟环境中的 Python
   - Settings > Editor > Code Style > Python
     Line length: 88 (Black)
   - Settings > Tools > Python Integrated Tools
     Default test runner: pytest
   - Enable Inspections 检查代码问题
   ```

### 🟡 SHOULD - 强烈建议

1. **EditorConfig 配置（.editorconfig）**
   ```
   root = true

   [*]
   charset = utf-8
   end_of_line = lf
   insert_final_newline = true
   trim_trailing_whitespace = true

   [*.py]
   indent_style = space
   indent_size = 4
   max_line_length = 88

   [*.{json,yaml,yml}]
   indent_style = space
   indent_size = 2

   [*.md]
   trim_trailing_whitespace = false
   ```

---

## Git 初始化

### 🔴 MUST - 严格遵守

1. **配置 Git 用户信息**
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **安装 Git Hooks**
   ```bash
   bash .claude/hooks/install-hooks.sh
   ```

3. **创建开发分支**
   ```bash
   git checkout -b develop origin/develop
   ```

---

## 数据库初始化

### 🔴 MUST - 严格遵守

1. **PostgreSQL 安装和配置**
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15

   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql

   # 创建数据库和用户
   createdb deepdive_dev
   createdb deepdive_test

   createuser deepdive_user
   psql deepdive_dev -c "ALTER USER deepdive_user WITH PASSWORD 'password';"
   psql deepdive_dev -c "ALTER USER deepdive_user CREATEDB;"
   ```

2. **使用 Docker 运行数据库**
   ```bash
   docker run -d \
     --name postgres \
     -e POSTGRES_DB=deepdive_dev \
     -e POSTGRES_USER=deepdive_user \
     -e POSTGRES_PASSWORD=password \
     -p 5432:5432 \
     postgres:15
   ```

3. **初始化数据库结构**
   ```bash
   alembic upgrade head
   ```

---

## 环境变量配置

### 🔴 MUST - 严格遵守

1. **.env.example 示例**
   ```
   # Environment
   ENVIRONMENT=development
   DEBUG=true
   LOG_LEVEL=DEBUG

   # Database
   DATABASE_URL=postgresql://deepdive_user:password@localhost:5432/deepdive_dev
   DATABASE_POOL_SIZE=10

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # API Keys
   OPENAI_API_KEY=your-openai-key
   CLAUDE_API_KEY=your-claude-key

   # JWT
   JWT_SECRET_KEY=your-secret-key
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24

   # Celery
   CELERY_BROKER_URL=redis://localhost:6379/1
   CELERY_RESULT_BACKEND=redis://localhost:6379/2

   # Application
   APP_TITLE=DeepDive Tracking
   APP_VERSION=1.0.0
   CORS_ORIGINS=http://localhost:3000,http://localhost:8080
   ```

2. **复制和配置**
   ```bash
   cp .env.example .env
   # 编辑 .env 填入本地配置
   ```

---

## 本地开发服务器

### 🔴 MUST - 严格遵守

1. **启动应用服务器**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **访问应用**
   ```
   API: http://localhost:8000
   API 文档: http://localhost:8000/docs
   ReDoc: http://localhost:8000/redoc
   ```

3. **后台任务（Celery）**
   ```bash
   # 启动Celery Worker
   celery -A src.tasks.celery_app worker --loglevel=info

   # 启动Flower监控
   celery -A src.tasks.celery_app flower
   # 访问: http://localhost:5555
   ```

---

## 验证安装

### 🔴 MUST - 严格遵守

1. **运行健康检查**
   ```bash
   bash .claude/tools/health-check.sh
   ```

2. **运行所有测试**
   ```bash
   pytest
   ```

3. **检查代码质量**
   ```bash
   bash .claude/tools/check-all.sh
   ```

4. **启动本地服务器**
   ```bash
   uvicorn src.main:app --reload
   # 访问 http://localhost:8000/docs
   ```

---

## 初始化检查清单

完成以下步骤：

- [ ] Python 3.10+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 依赖已安装（pip install -r requirements-dev.txt）
- [ ] Git 配置完毕（user.name, user.email）
- [ ] Git Hooks 已安装
- [ ] .env 文件已配置
- [ ] PostgreSQL 已安装并启动
- [ ] 数据库迁移已执行（alembic upgrade head）
- [ ] IDE 已配置（VS Code/PyCharm）
- [ ] 所有测试通过（pytest）
- [ ] 代码检查通过（black, flake8, mypy）
- [ ] 本地服务器可启动并访问

---

## 快速命令参考

```bash
# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements-dev.txt

# 运行应用
uvicorn src.main:app --reload

# 运行测试
pytest

# 检查代码
bash .claude/tools/check-all.sh

# 数据库迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "description"
```

---

**记住：** 花10分钟设置好开发环境，可以省去之后的几个小时的调试时间。

