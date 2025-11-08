# GitHub Pages 发布配置指南

## 📋 概述

DeepDive Tracking 支持将TOP新闻自动发布到GitHub Pages，提供美观的HTML页面展示。

**发布地址示例：**
- 每日摘要：`https://wisdom-future.github.io/deepdive-tracking/news/digests/2025-11-08.html`
- 索引页面：`https://wisdom-future.github.io/deepdive-tracking/news/index.html`

---

## 🚀 配置步骤

### 步骤1：创建GitHub Personal Access Token

1. 访问 [GitHub Token 设置页面](https://github.com/settings/tokens/new)

2. 配置Token：
   - **Note**: `DeepDive Tracking Publisher`
   - **Expiration**: `No expiration` 或选择较长时间
   - **Select scopes**: 勾选以下权限
     - ✅ `repo` (Full control of private repositories)
       - ✅ repo:status
       - ✅ repo_deployment
       - ✅ public_repo
       - ✅ repo:invite

3. 点击 **Generate token** 生成Token

4. **复制Token** - 注意：离开页面后无法再次查看！
   ```
   ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

### 步骤2：配置GCP Secret Manager

由于项目部署在GCP Cloud Run，需要将Token存储在Secret Manager中：

```bash
# 创建GitHub Token Secret
echo -n "ghp_your_actual_token_here" | gcloud secrets create GITHUB_TOKEN \
  --data-file=- \
  --project=deepdive-engine

# 授予Cloud Run服务账号访问权限
gcloud secrets add-iam-policy-binding GITHUB_TOKEN \
  --member="serviceAccount:726493701291-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=deepdive-engine

# 验证Secret已创建
gcloud secrets list --project=deepdive-engine | grep GITHUB_TOKEN
```

---

### 步骤3：更新环境变量

#### 本地开发环境（`.env`）：

```bash
# GitHub Pages 配置
GITHUB_TOKEN=ghp_your_actual_token_here
GITHUB_REPO=wisdom-future/deepdive-tracking
GITHUB_USERNAME=wisdom-future
```

#### GCP Cloud Run环境变量：

```bash
# 更新Cloud Run环境变量
gcloud run services update deepdive-tracking \
  --update-env-vars "GITHUB_REPO=wisdom-future/deepdive-tracking" \
  --update-env-vars "GITHUB_USERNAME=wisdom-future" \
  --project=deepdive-engine \
  --region=asia-east1

# Token从Secret Manager读取，src/utils/gcp_secrets.py会自动加载
```

---

### 步骤4：启用GitHub Pages

1. 访问仓库设置：`https://github.com/wisdom-future/deepdive-tracking/settings/pages`

2. 配置GitHub Pages：
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/docs`

3. 点击 **Save**

4. 等待几分钟，GitHub会自动构建并部署站点

5. 访问发布地址：`https://wisdom-future.github.io/deepdive-tracking/`

---

## 🧪 测试发布

### 方法1：手动触发（推荐）

```bash
# 本地测试
python scripts/publish/publish_to_github_pages.py

# GCP Cloud Run测试
curl -X POST \
  "https://deepdive-tracking-726493701291.asia-east1.run.app/publish/github" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 方法2：通过API触发

```bash
# 完整工作流（采集 → 评分 → 邮件 → GitHub）
curl -X POST \
  "https://deepdive-tracking-726493701291.asia-east1.run.app/workflows/full" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 📂 发布内容结构

发布后，GitHub仓库中会创建以下文件结构：

```
docs/
└── news/
    ├── index.html                    # 索引页面（列出所有摘要）
    └── digests/
        ├── 2025-11-08.html          # 每日摘要
        ├── 2025-11-09.html
        └── 2025-11-10.html
```

每个HTML页面都是独立的，包含完整的样式和内容。

---

## 🎨 页面样式

- **响应式设计**：支持移动端和桌面端
- **渐变背景**：紫色渐变主题
- **卡片布局**：每条新闻独立卡片展示
- **评分徽章**：根据评分显示不同颜色
- **悬停效果**：鼠标悬停时卡片上浮

---

## 🔧 高级配置

### 自定义样式

如果需要自定义页面样式，可以修改：
- `scripts/publish/publish_to_github_pages.py` 中的CSS样式

### 修改发布数量

默认发布TOP 10新闻，修改查询：
```python
.limit(10).all()  # 改为其他数量
```

### 添加CNAME（自定义域名）

如果要使用自定义域名：
```bash
# 推送CNAME文件到GitHub
echo "news.deepdive-tracking.com" | \
gcloud secrets versions access latest --secret="GITHUB_TOKEN" | \
xargs -I {} curl -X PUT \
  -H "Authorization: Bearer {}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/wisdom-future/deepdive-tracking/contents/docs/CNAME" \
  -d '{"message":"Add CNAME","content":"bmV3cy5kZWVwZGl2ZS10cmFja2luZy5jb20K"}'
```

---

## 🐛 故障排除

### 问题1：Token权限不足

**错误信息**：`HTTP 403: Resource not accessible by personal access token`

**解决方法**：
1. 确认Token勾选了 `repo` 权限
2. 重新生成Token并更新Secret

### 问题2：GitHub Pages未生效

**检查步骤**：
1. 确认 `docs/news/` 目录存在
2. 确认GitHub Pages设置正确（Settings → Pages）
3. 等待5-10分钟让GitHub完成构建

### 问题3：文件未更新

**原因**：GitHub Pages有缓存

**解决方法**：
1. 强制刷新浏览器（Ctrl+F5）
2. 等待缓存过期（通常10分钟）

### 问题4：Cloud Run无法访问Secret

**检查权限**：
```bash
# 验证服务账号权限
gcloud secrets get-iam-policy GITHUB_TOKEN \
  --project=deepdive-engine

# 应该看到compute服务账号有secretAccessor角色
```

---

## 📊 自动化发布

### 使用Cloud Scheduler定时发布

```yaml
# 每天早上9点发布到GitHub
gcloud scheduler jobs create http deepdive-github-daily \
  --location=asia-east1 \
  --schedule="0 9 * * *" \
  --uri="https://deepdive-tracking-726493701291.asia-east1.run.app/publish/github" \
  --http-method=POST \
  --oidc-service-account-email=deepdive-scheduler@deepdive-engine.iam.gserviceaccount.com \
  --oidc-token-audience="https://deepdive-tracking-726493701291.asia-east1.run.app" \
  --time-zone="Asia/Shanghai"
```

---

## 🔐 安全注意事项

1. **Token管理**：
   - ✅ 使用GCP Secret Manager存储Token
   - ❌ 不要将Token提交到代码仓库
   - ❌ 不要在日志中打印Token

2. **权限最小化**：
   - Token只授予必要的 `repo` 权限
   - 定期轮换Token（建议每6个月）

3. **审计**：
   - 在GitHub Settings → Developer settings → Personal access tokens 中查看Token使用记录

---

## 📚 相关文档

- [GitHub API文档](https://docs.github.com/en/rest)
- [GitHub Pages文档](https://docs.github.com/en/pages)
- [GCP Secret Manager文档](https://cloud.google.com/secret-manager/docs)

---

## ✅ 配置清单

完成以下检查确保配置正确：

- [ ] GitHub Personal Access Token已创建
- [ ] Token已存储在GCP Secret Manager（`GITHUB_TOKEN`）
- [ ] Cloud Run环境变量已配置（`GITHUB_REPO`, `GITHUB_USERNAME`）
- [ ] GitHub Pages已启用（Settings → Pages）
- [ ] 手动测试发布成功
- [ ] 访问发布的页面确认正常显示

---

**配置完成后，每次执行发布都会自动将TOP新闻推送到GitHub Pages！** 🎉
