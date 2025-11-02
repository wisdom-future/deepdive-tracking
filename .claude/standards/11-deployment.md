# 部署规范

**版本：** 1.0
**强制级别：** 🔴 MUST
**更新日期：** 2025-11-02

---

## 核心原则

```
✅ 基础设施即代码（IaC）
✅ 自动化部署流程
✅ 可重复和可靠的发布
✅ 快速回滚能力
✅ 完整的监控和日志
```

---

## Docker 容器化

### 🔴 MUST - 严格遵守

1. **Dockerfile 规范**
   ```dockerfile
   # 使用官方Python镜像
   FROM python:3.11-slim

   # 设置工作目录
   WORKDIR /app

   # 安装系统依赖
   RUN apt-get update && apt-get install -y \
       gcc \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*

   # 复制依赖文件
   COPY requirements.txt .

   # 安装Python依赖
   RUN pip install --no-cache-dir -r requirements.txt

   # 复制应用代码
   COPY src/ ./src/

   # 创建非root用户
   RUN useradd -m -u 1000 appuser && \
       chown -R appuser:appuser /app
   USER appuser

   # 暴露端口
   EXPOSE 8000

   # 健康检查
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD python -c "import requests; requests.get('http://localhost:8000/health')"

   # 启动命令
   CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Docker 最佳实践**
   ```
   ✅ 使用小型基础镜像（alpine, slim）
   ✅ 多阶段构建减少镜像大小
   ✅ 安装依赖时清理缓存
   ✅ 创建非root用户运行应用
   ✅ 设置 HEALTHCHECK
   ✅ 使用 .dockerignore 排除不必要文件
   ❌ 在容器中以root身份运行
   ❌ 将密钥放在镜像中
   ❌ 使用 latest 标签
   ```

3. **.dockerignore 文件**
   ```
   __pycache__
   *.pyc
   *.pyo
   *.pyd
   .Python
   env/
   venv/
   .git
   .gitignore
   .vscode
   .env
   .env.local
   *.db
   *.sqlite3
   ```

4. **docker-compose.yml 示例**
   ```yaml
   version: '3.8'

   services:
     api:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgresql://user:password@db:5432/deepdive
         - REDIS_URL=redis://redis:6379/0
       depends_on:
         - db
         - redis
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
         interval: 30s
         timeout: 10s
         retries: 3

     db:
       image: postgres:15
       environment:
         POSTGRES_DB: deepdive
         POSTGRES_USER: user
         POSTGRES_PASSWORD: password
       volumes:
         - postgres_data:/var/lib/postgresql/data

     redis:
       image: redis:7-alpine
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
         interval: 10s
         timeout: 5s

   volumes:
     postgres_data:
   ```

---

## Kubernetes 部署

### 🔴 MUST - 严格遵守

1. **Deployment 配置**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: deepdive-api
     labels:
       app: deepdive-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: deepdive-api
     strategy:
       type: RollingUpdate
       rollingUpdate:
         maxSurge: 1
         maxUnavailable: 0
     template:
       metadata:
         labels:
           app: deepdive-api
       spec:
         containers:
         - name: api
           image: deepdive-tracking:v1.0.0
           ports:
           - containerPort: 8000
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: app-secrets
                 key: database-url
           livenessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 10
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /ready
               port: 8000
             initialDelaySeconds: 5
             periodSeconds: 5
           resources:
             requests:
               memory: "256Mi"
               cpu: "100m"
             limits:
               memory: "512Mi"
               cpu: "500m"
   ```

2. **Service 配置**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: deepdive-api-service
   spec:
     selector:
       app: deepdive-api
     ports:
     - protocol: TCP
       port: 80
       targetPort: 8000
     type: LoadBalancer
   ```

3. **ConfigMap 和 Secret**
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: app-config
   data:
     LOG_LEVEL: "INFO"
     ENVIRONMENT: "production"

   ---
   apiVersion: v1
   kind: Secret
   metadata:
     name: app-secrets
   type: Opaque
   stringData:
     database-url: postgresql://user:password@db:5432/deepdive
     jwt-secret-key: your-secret-key
     openai-api-key: sk-xxxxxxxx
   ```

---

## CI/CD 流程

### 🔴 MUST - 严格遵守

1. **GitHub Actions 流程**
   ```yaml
   name: CI/CD

   on:
     push:
       branches: [develop, main]
     pull_request:
       branches: [develop, main]

   jobs:
     test:
       runs-on: ubuntu-latest
       services:
         postgres:
           image: postgres:15
           env:
             POSTGRES_DB: test
             POSTGRES_USER: user
             POSTGRES_PASSWORD: password
           options: >-
             --health-cmd pg_isready
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5
           ports:
             - 5432:5432
         redis:
           image: redis:7
           options: >-
             --health-cmd "redis-cli ping"
             --health-interval 10s
             --health-timeout 5s
             --health-retries 5
           ports:
             - 6379:6379

       steps:
       - uses: actions/checkout@v3
       - uses: actions/setup-python@v4
         with:
           python-version: '3.11'

       - name: Install dependencies
         run: |
           pip install -r requirements.txt
           pip install pytest pytest-cov

       - name: Lint with flake8
         run: flake8 src tests

       - name: Type check with mypy
         run: mypy src

       - name: Format check with black
         run: black --check src tests

       - name: Run tests
         env:
           DATABASE_URL: postgresql://user:password@localhost:5432/test
           REDIS_URL: redis://localhost:6379/0
         run: pytest --cov=src --cov-fail-under=85

       - name: Build Docker image
         run: docker build -t deepdive-tracking:latest .

       - name: Push Docker image
         if: github.ref == 'refs/heads/main'
         run: |
           echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
           docker tag deepdive-tracking:latest myregistry/deepdive-tracking:v${{ github.run_number }}
           docker push myregistry/deepdive-tracking:v${{ github.run_number }}

       - name: Deploy to Kubernetes
         if: github.ref == 'refs/heads/main'
         run: |
           kubectl set image deployment/deepdive-api \
             api=myregistry/deepdive-tracking:v${{ github.run_number }} \
             --record
   ```

---

## 环境管理

### 🔴 MUST - 严格遵守

1. **环境隔离**
   ```
   开发环境 (development)
   - 用于本地开发
   - 可以使用测试数据
   - 详细的日志输出

   测试环境 (staging/testing)
   - 与生产环境配置一致
   - 使用克隆的生产数据（脱敏）
   - 用于上线前测试

   生产环境 (production)
   - 真实用户数据
   - 安全的配置和凭证
   - 完整的监控和告警
   ```

2. **环境变量配置**
   ```python
   import os
   from enum import Enum

   class Environment(Enum):
       DEV = "development"
       STAGING = "staging"
       PROD = "production"

   env = Environment(os.getenv('ENVIRONMENT', 'development'))

   if env == Environment.PROD:
       DEBUG = False
       LOG_LEVEL = "WARNING"
       # 生产环境配置
   else:
       DEBUG = True
       LOG_LEVEL = "DEBUG"
       # 开发环境配置
   ```

---

## 数据库迁移

### 🔴 MUST - 严格遵守

1. **使用 Alembic 管理迁移**
   ```bash
   # 生成迁移文件
   alembic revision --autogenerate -m "add new column"

   # 应用迁移
   alembic upgrade head

   # 回滚迁移
   alembic downgrade -1
   ```

2. **部署前执行迁移**
   ```bash
   # 在部署脚本中
   alembic upgrade head
   ```

---

## 监控和日志

### 🔴 MUST - 严格遵守

1. **应用健康检查**
   ```python
   @app.get("/health")
   async def health_check():
       """基础健康检查。"""
       return {"status": "healthy"}

   @app.get("/ready")
   async def readiness_check():
       """就绪检查，检查所有依赖是否可用。"""
       try:
           # 检查数据库
           db_session.execute("SELECT 1")
           # 检查Redis
           redis_client.ping()
           return {"status": "ready"}
       except Exception:
           raise HTTPException(status_code=503)
   ```

2. **日志输出到标准输出**
   ```python
   # 容器日志最佳实践
   import logging
   import sys

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       stream=sys.stdout  # 输出到stdout，容器可以捕获
   )
   ```

3. **结构化日志**
   ```python
   import json
   import logging

   logger = logging.getLogger(__name__)

   # 结构化日志格式
   logger.info(json.dumps({
       "event": "user_login",
       "user_id": 123,
       "ip_address": "192.168.1.1",
       "timestamp": "2025-11-02T10:00:00Z"
   }))
   ```

---

## 回滚策略

### 🔴 MUST - 严格遵守

1. **版本标签管理**
   ```bash
   # 每个发布版本都要标签
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0

   # Docker镜像标签
   docker tag deepdive-tracking:latest deepdive-tracking:v1.0.0
   ```

2. **Kubernetes 快速回滚**
   ```bash
   # 查看部署历史
   kubectl rollout history deployment/deepdive-api

   # 回滚到上一个版本
   kubectl rollout undo deployment/deepdive-api

   # 回滚到特定版本
   kubectl rollout undo deployment/deepdive-api --to-revision=3
   ```

3. **数据库回滚**
   ```bash
   # 保持迁移可逆
   alembic downgrade -1

   # 或回滚到特定版本
   alembic downgrade <revision>
   ```

---

## 部署检查清单

部署前检查：

- [ ] 所有测试通过
- [ ] 代码审查完成
- [ ] 安全检查通过
- [ ] 依赖更新且漏洞检查通过
- [ ] Docker镜像构建成功
- [ ] 版本号更新
- [ ] CHANGELOG.md 已更新
- [ ] 数据库迁移已准备
- [ ] 监控和告警已配置
- [ ] 回滚计划已制定
- [ ] 性能测试通过
- [ ] 灾难恢复计划就绪

---

**记住：** 好的部署流程是高效运维的基础。自动化一切，定期测试回滚，持续监控。

