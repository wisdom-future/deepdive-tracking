# 部署脚本参考卡片

本文档提供所有部署脚本的快速参考。

---

## 📍 Cloud Run 部署脚本 (标准化命名)

### Python 脚本: `scripts/deploy_to_cloud_run.py`

**命名规范**: ✅ snake_case (符合规范)

```bash
# Dry-run 模式 - 测试不执行
python scripts/deploy_to_cloud_run.py --dry-run

# 标准部署
python scripts/deploy_to_cloud_run.py

# 自定义部署
python scripts/deploy_to_cloud_run.py \
  --project-id my-project \
  --region us-central1 \
  --service-name my-service

# 跳过 Docker 构建
python scripts/deploy_to_cloud_run.py --skip-build
```

**选项**:
- `--project-id ID` - GCP 项目 ID (默认: deepdive-engine)
- `--region REGION` - GCP 区域 (默认: asia-east1)
- `--service-name NAME` - 服务名 (默认: deepdive-tracking)
- `--dry-run` - 不执行，仅打印命令
- `--skip-build` - 跳过 Docker 构建

---

### Shell 脚本: `scripts/deploy_to_cloud_run.sh`

**命名规范**: ✅ snake_case (符合规范)

```bash
# 赋予执行权限
chmod +x scripts/deploy_to_cloud_run.sh

# 显示帮助
./scripts/deploy_to_cloud_run.sh --help

# Dry-run 模式
./scripts/deploy_to_cloud_run.sh --dry-run

# 标准部署
./scripts/deploy_to_cloud_run.sh

# 自定义部署
./scripts/deploy_to_cloud_run.sh \
  --project-id my-project \
  --region us-west1
```

**选项**:
- `--help` - 显示帮助
- `--project-id ID` - GCP 项目 ID
- `--region REGION` - GCP 区域
- `--service-name NAME` - 服务名
- `--dry-run` - 不执行，仅打印
- `--skip-build` - 跳过 Docker 构建

---

## 📍 优先级发布脚本 (标准化命名)

### 初始化配置: `scripts/init_publish_priorities.py`

**命名规范**: ✅ snake_case (符合规范)

初始化默认优先级配置 (Email > GitHub > WeChat)

```bash
python scripts/init_publish_priorities.py
```

---

### 查看配置: `scripts/show_publish_priorities.py`

**命名规范**: ✅ snake_case (符合规范)

显示当前优先级配置和统计信息

```bash
python scripts/show_publish_priorities.py
```

---

### 测试发布: `scripts/run_priority_publishing_test.py`

**命名规范**: ✅ snake_case (符合规范)

测试发布功能 (支持 dry-run)

```bash
# Dry-run 模式 - 不发送真实邮件
python scripts/run_priority_publishing_test.py 3 --dry-run

# 实际发送 3 篇文章
python scripts/run_priority_publishing_test.py 3
```

---

## 🚀 完整部署流程

### 第 1 步: Dry-run 测试

```bash
# 测试部署脚本
python scripts/deploy_to_cloud_run.py --dry-run
```

### 第 2 步: 部署到 Cloud Run

```bash
# 执行实际部署
python scripts/deploy_to_cloud_run.py
```

等待 5-10 分钟完成 Docker 构建和部署

### 第 3 步: 初始化数据库

```bash
# 创建数据库表
python scripts/init_publish_priorities.py
```

### 第 4 步: 验证发布功能

```bash
# Dry-run 测试
python scripts/run_priority_publishing_test.py 3 --dry-run

# 实际测试
python scripts/run_priority_publishing_test.py 3
```

### 第 5 步: 查看统计

```bash
# 显示配置和统计
python scripts/show_publish_priorities.py
```

---

## 📋 脚本对比表

| 脚本 | 语言 | 命名规范 | 用途 | 功能 |
|------|------|---------|------|------|
| deploy_to_cloud_run.py | Python | ✅ | Cloud Run 部署 | 完整的部署工具 |
| deploy_to_cloud_run.sh | Bash | ✅ | Cloud Run 部署 | 跨平台 Shell 版 |
| init_publish_priorities.py | Python | ✅ | 初始化配置 | 创建默认优先级 |
| show_publish_priorities.py | Python | ✅ | 查看配置 | 显示配置和统计 |
| run_priority_publishing_test.py | Python | ✅ | E2E 测试 | 测试发布功能 |

---

## 🔧 环境变量

### deploy_to_cloud_run.py 支持的环境变量

```bash
export GCP_PROJECT_ID="my-project"      # GCP 项目 ID
export GCP_REGION="us-central1"         # GCP 区域
export CLOUD_RUN_SERVICE_NAME="my-svc"  # 服务名

python scripts/deploy_to_cloud_run.py
```

### deploy_to_cloud_run.sh 支持的环境变量

```bash
export GCP_PROJECT_ID="my-project"
export GCP_REGION="us-central1"
export CLOUD_RUN_SERVICE_NAME="my-svc"

./scripts/deploy_to_cloud_run.sh
```

---

## 📚 相关文档

| 文档 | 路径 | 描述 |
|------|------|------|
| Cloud Run 部署指南 | docs/deployment/CLOUD_RUN_DEPLOYMENT.md | 完整的部署指南 |
| 优先级发布文档 | docs/guides/priority-publishing.md | 发布系统文档 |
| 配置指南 | docs/guides/configure-publishing-channels.md | 邮件/GitHub 配置 |
| 部署进度 | docs/deployment/GCP-DEPLOYMENT-PROGRESS.md | 部署状态报告 |
| 部署总结 | DEPLOYMENT-SUMMARY.md | 完整部署总结 |

---

## ✅ 最佳实践

### 1. 始终使用 Dry-run 模式进行验证

```bash
python scripts/deploy_to_cloud_run.py --dry-run
# 检查命令是否正确
# 然后执行实际部署
python scripts/deploy_to_cloud_run.py
```

### 2. 使用环境变量配置

```bash
# 设置环境变量
export GCP_PROJECT_ID="my-project"

# 脚本会自动使用这些值
python scripts/deploy_to_cloud_run.py
```

### 3. 检查部署日志

```bash
# 查看部署进度
gcloud run services describe deepdive-tracking --region asia-east1

# 查看应用日志
gcloud logging read "resource.type=cloud_run_revision" --tail
```

### 4. 验证部署成功

```bash
# 初始化数据库
python scripts/init_publish_priorities.py

# 运行测试
python scripts/run_priority_publishing_test.py 3 --dry-run
python scripts/run_priority_publishing_test.py 3

# 检查统计
python scripts/show_publish_priorities.py
```

---

## 🐛 常见问题

### Q: 部署脚本无法运行

A: 检查 Python 版本和依赖
```bash
python --version  # 需要 Python 3.7+
pip install -r requirements.txt
```

### Q: Shell 脚本权限问题

A: 赋予执行权限
```bash
chmod +x scripts/deploy_to_cloud_run.sh
```

### Q: GCP 认证失败

A: 重新登录
```bash
gcloud auth login
gcloud config set project deepdive-engine
```

### Q: 部署超时

A: Docker 构建需要时间，可能需要 10-15 分钟
```bash
# 监控构建进度
gcloud builds list
gcloud builds log <BUILD_ID> --stream
```

---

## 📞 获取帮助

### 查看脚本帮助

```bash
# Python 脚本帮助
python scripts/deploy_to_cloud_run.py --help

# Shell 脚本帮助
./scripts/deploy_to_cloud_run.sh --help
```

### 查看部署指南

```bash
# 详细的 Cloud Run 部署指南
cat docs/deployment/CLOUD_RUN_DEPLOYMENT.md

# 优先级发布系统文档
cat docs/guides/priority-publishing.md
```

---

**最后更新**: 2025-11-03
**版本**: 1.0
**标准遵守**: ✅ 所有脚本均使用 snake_case 命名规范
