# Cloud Run 部署指南

本文档说明如何将 DeepDive Tracking 部署到 Google Cloud Run。

## 快速开始

### 使用 Python 部署脚本

```bash
# Dry-run 模式（测试，不实际部署）
python scripts/deploy_to_cloud_run.py --dry-run

# 实际部署到 Cloud Run
python scripts/deploy_to_cloud_run.py

# 自定义部署
python scripts/deploy_to_cloud_run.py \
  --project-id my-project \
  --region asia-east1 \
  --service-name my-service
```

### 使用 Shell 脚本部署

```bash
# 赋予执行权限
chmod +x scripts/deploy_to_cloud_run.sh

# Dry-run 模式
./scripts/deploy_to_cloud_run.sh --dry-run

# 实际部署
./scripts/deploy_to_cloud_run.sh

# 自定义部署
./scripts/deploy_to_cloud_run.sh --region us-central1
```

---

## 部署脚本详解

### Python 脚本: deploy_to_cloud_run.py

**命名规范**: ✅ snake_case

**功能**:
- ✅ 验证 GCP 设置和认证
- ✅ 检查 Cloud Run API 是否启用
- ✅ 构建并部署 Docker 镜像
- ✅ 配置环境变量
- ✅ 验证部署成功

**命令行选项**:
```
--project-id ID         GCP 项目 ID (默认: deepdive-engine)
--region REGION         GCP 区域 (默认: asia-east1)
--service-name NAME     Cloud Run 服务名 (默认: deepdive-tracking)
--dry-run              不执行，仅打印命令
--skip-build           跳过 Docker 构建
```

**环境变量**:
```bash
export GCP_PROJECT_ID="my-project"
export GCP_REGION="us-central1"
export CLOUD_RUN_SERVICE_NAME="my-service"

python scripts/deploy_to_cloud_run.py
```

### Shell 脚本: deploy_to_cloud_run.sh

**命名规范**: ✅ snake_case

**功能**:
- ✅ 跨平台兼容（Linux, macOS, WSL）
- ✅ 彩色输出，易于读取
- ✅ 完整的错误处理
- ✅ 支持所有 Python 版本相同的选项

**命令行选项**:
```
--help                显示帮助信息
--dry-run            Dry-run 模式
--skip-build         跳过 Docker 构建
--project-id ID      GCP 项目 ID
--region REGION      GCP 区域
--service-name NAME  Cloud Run 服务名
```

---

## 部署前置条件

### 1. GCP 账号和项目

```bash
# 安装 Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# 初始化 gcloud
gcloud init

# 设置默认项目
gcloud config set project deepdive-engine

# 验证配置
gcloud config list
```

### 2. 启用必要的 API

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. 创建基础设施（如需要）

如果尚未创建，需要先创建数据库和缓存：

```bash
# Cloud SQL PostgreSQL
gcloud sql instances create deepdive-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-east1

# Cloud Memorystore Redis
gcloud redis instances create deepdive-redis \
  --size=1 \
  --region=asia-east1 \
  --tier=basic \
  --redis-version=redis_7_2
```

---

## 完整部署示例

### 标准部署流程

```bash
# 1. 首先进行 dry-run 测试
python scripts/deploy_to_cloud_run.py --dry-run

# 检查输出，确保命令正确
# 输出示例：
# ======================================================================
# 🚀 DEEPDIVE TRACKING - CLOUD RUN DEPLOYMENT
# ======================================================================
# Project ID: deepdive-engine
# Region: asia-east1
# Service: deepdive-tracking
# Mode: DRY-RUN

# 2. 如果 dry-run 测试通过，执行实际部署
python scripts/deploy_to_cloud_run.py

# 输出示例：
# ✓ gcloud CLI is installed
# ✓ GCP project configured: deepdive-engine
# ✓ Cloud Run API is enabled
# ✓ Deploy deepdive-tracking to Cloud Run completed
# ✓ Service deployed successfully!
# 📍 Service URL: https://deepdive-tracking-xxxxx.asia-east1.run.app

# 3. 初始化数据库
python scripts/init_publish_priorities.py

# 4. 验证发布功能
python scripts/run_priority_publishing_test.py 3 --dry-run

# 5. 实际测试
python scripts/run_priority_publishing_test.py 3
```

### 自定义部署

```bash
# 部署到不同的项目和区域
python scripts/deploy_to_cloud_run.py \
  --project-id my-custom-project \
  --region us-central1 \
  --service-name my-deepdive-service
```

---

## 部署后验证

### 1. 检查服务状态

```bash
gcloud run services describe deepdive-tracking --region asia-east1
```

### 2. 获取服务 URL

```bash
gcloud run services describe deepdive-tracking --region asia-east1 --format='value(status.url)'
```

### 3. 测试健康端点

```bash
SERVICE_URL=$(gcloud run services describe deepdive-tracking --region asia-east1 --format='value(status.url)')
curl "$SERVICE_URL/health"

# 预期响应:
# {"status":"ok","version":"0.1.0"}
```

### 4. 查看部署日志

```bash
# 查看最近日志
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --tail

# 查看错误日志
gcloud logging read "severity=ERROR" --limit=20
```

---

## 环境变量配置

Cloud Run 服务自动使用以下环境变量：

- `DATABASE_URL` - PostgreSQL 连接字符串
- `REDIS_URL` - Redis 缓存连接
- `CELERY_BROKER_URL` - Celery 任务队列连接
- `CELERY_RESULT_BACKEND` - Celery 结果存储连接
- `APP_ENV` - 应用环境（production）
- `DEBUG` - 调试模式（False）
- `LOG_LEVEL` - 日志级别（INFO）

这些变量在部署时由脚本自动配置。

---

## 故障排查

### 问题 1: "gcloud: command not found"

**解决方案**:
```bash
# 安装 Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# 重新初始化 gcloud
gcloud init
```

### 问题 2: 认证失败

**解决方案**:
```bash
# 重新登录
gcloud auth login

# 或使用服务账号
gcloud auth activate-service-account --key-file=key.json
```

### 问题 3: Cloud Run API 未启用

**解决方案**:
```bash
gcloud services enable run.googleapis.com
```

### 问题 4: Docker 构建失败

**检查项**:
1. 确保 Dockerfile 存在于项目根目录
2. 确保 requirements.txt 有效
3. 查看构建日志：`gcloud builds log <BUILD_ID>`

### 问题 5: 容器启动失败

**常见原因**:
- 应用监听端口不是 8080（Cloud Run 标准）
- 数据库连接超时
- 缺少必要的依赖

**解决方案**:
```bash
# 查看详细错误日志
gcloud logging read "resource.type=cloud_run_revision" --limit=20 --format=json | jq '.[] | {severity, textPayload}'

# 检查容器日志
gcloud run revisions list --service=deepdive-tracking --region=asia-east1
```

---

## 最佳实践

### 1. 总是先使用 Dry-run 模式

```bash
python scripts/deploy_to_cloud_run.py --dry-run
# 验证命令和配置无误后再执行实际部署
```

### 2. 定期更新凭证

```bash
# 更新 Secret Manager 中的凭证
echo -n "NEW_VALUE" | gcloud secrets versions add secret-name --data-file=-

# 重新部署以应用新凭证
python scripts/deploy_to_cloud_run.py
```

### 3. 监控部署

```bash
# 持续查看日志
gcloud logging read "resource.type=cloud_run_revision" --tail

# 监控错误
gcloud logging read "severity=ERROR" --limit=20
```

### 4. 版本管理

```bash
# 查看部署的版本
gcloud run revisions list --service=deepdive-tracking --region=asia-east1

# 回滚到之前的版本
gcloud run services update-traffic deepdive-tracking --region=asia-east1 --to-revisions=REVISION_ID=100
```

---

## 成本估计

| 服务 | 配置 | 月成本 |
|------|------|--------|
| Cloud Run | 1GB RAM, 1 vCPU, 900s timeout | $10-15 |
| Cloud SQL | PostgreSQL db-f1-micro | $15-20 |
| Cloud Memorystore | Redis 1GB | $10-12 |
| Cloud Logging | 记录存储 | $5-10 |
| Artifact Registry | Docker 镜像存储 | $1-2 |
| **总计** | | **$40-60/月** |

---

## 相关资源

- [Cloud Run 官方文档](https://cloud.google.com/run/docs)
- [部署 Python 应用到 Cloud Run](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Cloud Run 环境变量配置](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Run 定价](https://cloud.google.com/run/pricing)

---

**最后更新**: 2025-11-03
**脚本版本**: 1.0
**文档版本**: 1.0
