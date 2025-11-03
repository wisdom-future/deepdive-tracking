# Cloud Run 部署指南

本文档说明如何使用标准化的部署脚本将 DeepDive Tracking 部署到 Google Cloud Run。

## 快速开始

### 使用 Python 脚本部署

```bash
# Dry-run 模式（不实际部署）
python scripts/deploy_to_cloud_run.py --dry-run

# 实际部署到 Cloud Run
python scripts/deploy_to_cloud_run.py

# 部署到特定项目
python scripts/deploy_to_cloud_run.py --project-id my-project --region asia-east1
```

### 使用 Shell 脚本部署

```bash
# 赋予执行权限
chmod +x scripts/deploy_to_cloud_run.sh

# Dry-run 模式
./scripts/deploy_to_cloud_run.sh --dry-run

# 实际部署
./scripts/deploy_to_cloud_run.sh

# 自定义部署参数
./scripts/deploy_to_cloud_run.sh --project-id my-project --region us-central1
```

---

## 部署脚本详解

### deploy_to_cloud_run.py

**标准化命名**: ✅ snake_case 命名规范
**类型**: Python 3 脚本
**功能**: 完整的 Cloud Run 部署工具

#### 功能特性

- ✅ 验证 GCP 设置和认证
- ✅ 检查 Cloud Run API 是否启用
- ✅ 构建并部署 Docker 镜像
- ✅ 配置环境变量
- ✅ 验证部署成功
- ✅ 支持 Dry-run 模式测试
- ✅ 支持跳过 Docker 构建

#### 使用方式

```bash
python scripts/deploy_to_cloud_run.py [OPTIONS]
```

#### 命令行选项

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--project-id ID` | GCP 项目 ID | deepdive-engine |
| `--region REGION` | GCP 区域 | asia-east1 |
| `--service-name NAME` | Cloud Run 服务名 | deepdive-tracking |
| `--dry-run` | 打印命令不执行 | 否 |
| `--skip-build` | 跳过 Docker 构建 | 否 |

#### 环境变量

可以通过环境变量配置默认值：

```bash
export GCP_PROJECT_ID="my-project"
export GCP_REGION="us-central1"
export CLOUD_RUN_SERVICE_NAME="my-service"

python scripts/deploy_to_cloud_run.py
```

#### 部署过程

脚本执行以下步骤：

1. **验证 GCP 设置**
   - 检查 gcloud CLI 是否安装
   - 验证 GCP 项目配置
   - 检查认证状态

2. **启用 Cloud Run API**
   - 检查 Cloud Run API 是否启用
   - 如未启用则自动启用

3. **部署到 Cloud Run**
   - 构建 Docker 镜像（使用 Dockerfile）
   - 推送镜像到 Artifact Registry
   - 创建 Cloud Run 服务
   - 配置环境变量
   - 设置访问权限

4. **验证部署**
   - 检查服务是否正常运行
   - 获取服务 URL
   - 打印下一步操作指南

### deploy_to_cloud_run.sh

**标准化命名**: ✅ snake_case 命名规范
**类型**: Bash Shell 脚本
**功能**: Shell 版本的 Cloud Run 部署工具

#### 功能特性

- ✅ 跨平台兼容（Linux, macOS, WSL）
- ✅ 彩色输出，易于读取
- ✅ 完整的错误处理
- ✅ 支持所有 Python 版本相同的选项
- ✅ 内置帮助文档

#### 使用方式

```bash
./scripts/deploy_to_cloud_run.sh [OPTIONS]
```

#### 命令行选项

| 选项 | 描述 |
|------|------|
| `--help` | 显示帮助信息 |
| `--dry-run` | Dry-run 模式 |
| `--skip-build` | 跳过 Docker 构建 |
| `--project-id ID` | GCP 项目 ID |
| `--region REGION` | GCP 区域 |
| `--service-name NAME` | Cloud Run 服务名 |

#### 输出样式

脚本使用彩色输出便于阅读：

- 🔍 蓝色：信息和步骤说明
- ✓ 绿色：成功操作
- ✗ 红色：错误
- ⚠ 黄色：警告
- 🚀 标题：主要步骤

---

## 完整部署示例

### 示例 1: 标准部署

```bash
# 1. 首先进行 dry-run 测试
python scripts/deploy_to_cloud_run.py --dry-run

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
# ======================================================================
# 🚀 DEEPDIVE TRACKING - CLOUD RUN DEPLOYMENT
# ======================================================================
# Project ID: deepdive-engine
# Region: asia-east1
# Service: deepdive-tracking
# Mode: NORMAL
#
# ✓ gcloud CLI is installed
# ✓ GCP project configured: deepdive-engine
# ✓ Cloud Run API is enabled
# ✓ Deploy deepdive-tracking to Cloud Run completed
# ✓ Service deployed successfully!
# 📍 Service URL: https://deepdive-tracking-xxxxx.asia-east1.run.app
```

### 示例 2: 自定义部署

```bash
# 部署到不同的项目和区域
python scripts/deploy_to_cloud_run.py \
  --project-id my-custom-project \
  --region us-central1 \
  --service-name my-deepdive-service
```

### 示例 3: 跳过 Docker 构建

```bash
# 如果已经有现成的 Docker 镜像，可以跳过构建
python scripts/deploy_to_cloud_run.py --skip-build
```

### 示例 4: 使用 Shell 脚本

```bash
# 赋予执行权限
chmod +x scripts/deploy_to_cloud_run.sh

# 执行部署
./scripts/deploy_to_cloud_run.sh

# 自定义区域部署
./scripts/deploy_to_cloud_run.sh --region us-west1
```

---

## 环境配置

### GCP 认证设置

```bash
# 初始化 gcloud 并登录
gcloud init

# 设置默认项目
gcloud config set project deepdive-engine

# 验证配置
gcloud config list
```

### 必需的 GCP API

脚本会自动启用以下 API：

- Cloud Run Admin API (`run.googleapis.com`)
- Cloud Build API (自动启用)
- Artifact Registry API (自动启用)

### 所需权限

确保 GCP 用户账号或服务账号具有以下权限：

- `run.admin` - 管理 Cloud Run 服务
- `artifactregistry.admin` - 管理 Artifact Registry
- `cloudbuild.builds.editor` - 创建 Cloud Build
- `iam.serviceAccountUser` - 使用服务账号

---

## 部署后的验证

### 1. 检查服务状态

```bash
gcloud run services describe deepdive-tracking --region asia-east1
```

### 2. 查看服务 URL

```bash
gcloud run services describe deepdive-tracking --region asia-east1 --format='value(status.url)'
```

### 3. 查看部署日志

```bash
gcloud run services describe deepdive-tracking --region asia-east1
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --tail
```

### 4. 测试服务

```bash
# 获取服务 URL
SERVICE_URL=$(gcloud run services describe deepdive-tracking --region asia-east1 --format='value(status.url)')

# 测试 API
curl "$SERVICE_URL/health"
```

---

## 故障排查

### 问题 1: 无法找到 gcloud 命令

**症状**: `gcloud: command not found`

**解决方案**:
```bash
# 安装 Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# 初始化 gcloud
gcloud init
```

### 问题 2: 认证失败

**症状**: `Error: User [xxx] does not have permission denied`

**解决方案**:
```bash
# 重新登录
gcloud auth login

# 或使用服务账号
gcloud auth activate-service-account --key-file=key.json
```

### 问题 3: Cloud Run API 未启用

**症状**: `Cloud Run API is not enabled`

**解决方案**:
```bash
gcloud services enable run.googleapis.com
```

### 问题 4: Docker 构建失败

**症状**: `Build failed: ...`

**检查项**:
1. 确保 Dockerfile 存在于项目根目录
2. 确保 requirements.txt 或 setup.py 有效
3. 检查镜像大小（Cloud Run 限制 4GB）
4. 查看构建日志：`gcloud builds log <BUILD_ID>`

### 问题 5: 部署超时

**症状**: `Timed out waiting for operation...`

**解决方案**:
```bash
# 增加超时时间（在脚本中修改）
# 或使用后台监控
gcloud builds log <BUILD_ID> --stream
```

---

## 最佳实践

### 1. 总是先使用 Dry-run 模式

```bash
# 验证命令和配置
python scripts/deploy_to_cloud_run.py --dry-run

# 然后执行实际部署
python scripts/deploy_to_cloud_run.py
```

### 2. 定期更新凭证

```bash
# 更新 Secret Manager 中的凭证
gcloud secrets versions add secret-name --data-file=-

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
# 查看所有版本
gcloud run services describe deepdive-tracking --region asia-east1 --format='value(status.latestReadyRevision)'

# 查看版本历史
gcloud run revisions list --service=deepdive-tracking --region=asia-east1
```

---

## 后续步骤

部署完成后，执行以下步骤：

### 1. 初始化数据库

```bash
python scripts/init_publish_priorities.py
```

### 2. 测试发布功能

```bash
# Dry-run 模式
python scripts/run_priority_publishing_test.py 3 --dry-run

# 实际发送
python scripts/run_priority_publishing_test.py 3
```

### 3. 验证邮件发送

检查接收邮箱：`hello.junjie.duan@gmail.com`

### 4. 查看统计信息

```bash
python scripts/show_publish_priorities.py
```

---

## 参考资源

- [Cloud Run 官方文档](https://cloud.google.com/run/docs)
- [部署 Python 应用到 Cloud Run](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Cloud Run 环境变量配置](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Cloud Run 定价](https://cloud.google.com/run/pricing)

---

**最后更新**: 2025-11-03
**脚本版本**: 1.0
