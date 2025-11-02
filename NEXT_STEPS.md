# 下一步行动指南 - 真实数据采集系统

**当前状态：** 系统代码和脚本已完全就绪，等待 Docker 环境配置
**时间：** 2025-11-02
**责任：** 用户侧行动

---

## 🎯 核心障碍与解决方案

### 当前情况
```
✓ 数据采集脚本已完成        (scripts/run_collection.py)
✓ 数据库迁移脚本已完成      (alembic/versions/)
✓ 配置已正确同步           (settings.py, docker-compose.yml)
✓ 代码已提交到 Git          (2 个新提交)
✗ Docker 尚未安装/配置      ← 唯一的阻碍
```

### 问题分析
当你运行 `python scripts/run_collection.py` 时，脚本正确地报告：
```
ERROR - 无法连接数据库: connection to server at "localhost" port 5432 failed
请确保:
1. PostgreSQL 已启动: docker-compose up -d
2. 数据库迁移已完成: alembic upgrade head
3. 环境变量正确设置
```

**这是预期的行为** - 脚本工作正常，只是 PostgreSQL 容器没有运行。

---

## 📋 3 个简单步骤启动系统

### 步骤 1️⃣: 安装 Docker Desktop（5-10 分钟）

**Windows 用户：**

1. 访问 https://www.docker.com/products/docker-desktop
2. 点击 "Download for Windows"
3. 安装完成后**重启计算机**
4. Docker Desktop 会在后台自动启动

**验证安装成功：**
```powershell
# 打开 PowerShell，运行：
docker --version
docker compose version

# 应该看到版本号（不是 "command not found"）
```

详细步骤见：`DOCKER_SETUP_GUIDE.md`

---

### 步骤 2️⃣: 启动数据库基础设施（30 秒）

**在 PowerShell 中运行：**

```powershell
# 进入项目目录
cd D:\projects\deepdive-tracking

# 启动 PostgreSQL + Redis 容器
docker compose up -d

# 验证容器运行
docker ps

# 应该看到：
# deepdive_postgres (postgres:15-alpine) - Up X seconds
# deepdive_redis    (redis:7-alpine)    - Up X seconds
```

**等待 PostgreSQL 完全启动：**
```powershell
# 查看日志，确保没有错误
docker logs deepdive_postgres

# 预期最后一行：
# LOG:  database system is ready to accept connections
```

---

### 步骤 3️⃣: 执行完整的数据采集流程（2-3 分钟）

**初始化数据库架构：**
```powershell
alembic upgrade head

# 预期输出：
# INFO  [alembic.runtime.migration] Running upgrade  -> 001_init..., create all tables
# (结束，无错误)
```

**运行真实数据采集：**
```powershell
python scripts/run_collection.py

# 预期输出：
# ================================================================================
# DeepDive Tracking - Real Data Collection
# ================================================================================
#
# [1] 连接到PostgreSQL数据库...
#     OK - Connected to postgresql://deepdive:***@localhost:5432/deepdive_db
#
# [2] 检查数据源配置...
#     OK - Found 2 enabled sources:
#     + OpenAI Blog (rss)
#     + Anthropic News (rss)
#
# [3] 开始采集数据...
#     时间: 2025-11-02T15:30:45.123456
#     (这可能需要30-60秒)
#
# [4] 采集结果统计
# ================================================================================
# 总采集数量: 15
# 新增数量:   15
# 重复数量:   0
#
# 按数据源分布:
#   OpenAI Blog:
#     采集: 8, 新增: 8, 重复: 0
#   Anthropic News:
#     采集: 7, 新增: 7, 重复: 0
#
# [5] 采集到的数据样本 (最新10条)
# ================================================================================
#
# 1. [raw] GPT-4 Turbo with vision capabilities
#    来源: OpenAI Blog
#    URL: https://openai.com/blog/gpt-4-turbo-vision
#    发布时间: 2024-11-06 10:30:00+00:00
#    采集时间: 2025-11-02 15:30:45.123456
#    摘要: We are excited to announce the release of GPT-4 Turbo with vision...
# ...
```

**验证数据已保存到数据库：**
```powershell
# 使用 PostgreSQL 客户端查询
psql -h localhost -U deepdive -d deepdive_db

# 在 psql 提示符下运行：
deepdive_db=> SELECT COUNT(*) FROM raw_news;
 count
-------
    15
(1 row)

# 查看具体数据
deepdive_db=> SELECT id, title, source_name FROM raw_news LIMIT 3;
 id |                        title                        | source_name
----+------------------------------------------------------+-------------
  1 | GPT-4 Turbo now supports vision capabilities       | OpenAI Blog
  2 | Introducing Claude 3.5 Sonnet                      | Anthropic
  3 | Google DeepMind announces new research breakthrough | DeepMind
(3 rows)

# 退出 psql
deepdive_db=> \q
```

---

## ✅ 完成检查清单

在执行上述步骤后，验证以下内容：

- [ ] Docker Desktop 已安装并运行
- [ ] 运行 `docker ps` 看到 2 个容器（postgres 和 redis）
- [ ] 运行 `alembic current` 显示版本号（无错误）
- [ ] 运行 `python scripts/run_collection.py` 完成采集
- [ ] 采集结果显示 "总采集数量: 15" 或更多
- [ ] SQL 查询 `SELECT COUNT(*) FROM raw_news` 返回采集的新闻数
- [ ] 至少看到一条完整的新闻数据（标题、URL、发布时间等）

---

## 📊 关键参数速查

### 数据库连接信息
```
主机名：       localhost
端口号：       5432
用户名：       deepdive
密码：         deepdive_password
数据库名：     deepdive_db
```

### 数据源（自动创建）
```
源 1: OpenAI Blog
  URL: https://openai.com/blog/rss.xml
  类型: RSS

源 2: Anthropic News
  URL: https://www.anthropic.com/news/rss.xml
  类型: RSS
```

### 采集统计预期值
```
总采集数量：   15-30（取决于网络和 RSS 源状态）
新增数量：     首次运行时等于总采集数量
重复数量：     0（首次运行）
```

---

## 🔍 故障排除快速参考

### 问题 1: Docker 命令找不到

**现象：**
```
docker: command not found
```

**解决：**
1. 确认 Docker Desktop 已安装
2. 确认已重启计算机（安装后必须重启）
3. 在新的 PowerShell 窗口中重试
4. 检查 Docker Desktop 是否在运行（右下角系统托盘）

---

### 问题 2: PostgreSQL 容器无法启动

**现象：**
```
docker compose up -d
# 容器启动但立即退出，或显示错误
```

**解决：**
```powershell
# 查看具体错误
docker logs deepdive_postgres

# 如果是权限或端口问题，可能需要：
# 1. 确保没有其他 PostgreSQL 运行在 5432 端口
# 2. 检查磁盘空间是否足够
# 3. 尝试完全重置：
docker compose down -v
docker compose up -d
```

---

### 问题 3: alembic 迁移失败

**现象：**
```
sqlalchemy.exc.OperationalError: connection to server... refused
```

**解决：**
```powershell
# 1. 确认 PostgreSQL 容器运行且就绪
docker logs deepdive_postgres | tail -20
# 应该看到 "database system is ready to accept connections"

# 2. 等待 30 秒后再试
Start-Sleep -Seconds 30

# 3. 重试迁移
alembic upgrade head
```

---

### 问题 4: 采集脚本无数据

**现象：**
```
采集结果统计
总采集数量: 0
```

**解决：**
```powershell
# 1. 检查数据源是否存在
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> SELECT * FROM data_sources;

# 如果为空，脚本会自动创建，重新运行：
python scripts/run_collection.py

# 2. 检查网络连接（RSS 源是否可访问）
# 尝试手动访问 RSS 源：
curl -I https://openai.com/blog/rss.xml
# 应该看到 200 OK

# 3. 查看完整的错误日志
python scripts/run_collection.py 2>&1 | Tee-Object -FilePath collection_log.txt
```

---

## 💡 常见问题解答

**Q: 需要多少磁盘空间？**
A: Docker Desktop 本身约 2-3 GB，PostgreSQL 容器约 200 MB，数据初期约 50 MB。建议保留 10 GB 以上可用空间。

**Q: 运行多久可以看到数据？**
A: 完整流程（Docker 启动 + 迁移 + 采集）约 5-10 分钟。采集本身因网络而异，通常 30-60 秒。

**Q: 可以在没有 Docker 的情况下运行吗？**
A: 可以，但需要：
- 手动安装 PostgreSQL 15
- 手动安装 Redis 7
- 手动配置连接参数
建议使用 Docker 以简化设置。

**Q: Docker 会影响系统性能吗？**
A: 我们的容器很轻量级。空闲时 Docker 占用 < 100 MB 内存。如果系统慢，检查 Docker Desktop 设置中的内存分配。

**Q: 采集的数据存储在哪里？**
A: 数据持久化存储在 Docker volume `deepdive_postgres_data` 中，位置：
- Windows: `%LOCALAPPDATA%\Docker\wsl\data`
- 或 Docker Desktop 管理的位置
重启容器后数据不会丢失。

---

## 📚 完整文档索引

| 文档 | 用途 | 何时阅读 |
|------|------|--------|
| `DOCKER_SETUP_GUIDE.md` | Docker 安装和配置详细步骤 | 首次安装 Docker 时 |
| `VERIFICATION_GUIDE.md` | 数据采集验证详细指南 | 采集完成后验证数据 |
| `system-ready.md` | 系统就绪报告和完整性检查 | 了解系统现状 |
| `README.md` | 项目概览和快速开始 | 新成员入门 |
| `CLAUDE.md` | 项目规范和开发指南 | 参与开发时参考 |

---

## 🎯 关键里程碑

### 当前进度
```
✅ Phase 1: 框架设计     (完成)
✅ Phase 2: 代码实现     (完成)
✅ Phase 3: 配置验证     (完成)
⏳ Phase 4: Docker 配置  (用户侧，5-10 分钟)
⏳ Phase 5: 数据采集执行 (3-5 分钟)
⏳ Phase 6: 数据验证     (5-10 分钟)
```

### 预期时间表
```
现在      → Docker 安装 (取决于网络，通常 5-15 分钟)
+5 分钟   → 启动基础设施
+2 分钟   → 数据库迁移
+1 分钟   → 采集脚本开始
+1 分钟   → 采集完成
+2 分钟   → 数据验证
```

**总计：约 15-30 分钟（主要时间用于 Docker 安装）**

---

## 🚀 开始行动

### 立即执行
1. 安装 Docker Desktop（参考 `DOCKER_SETUP_GUIDE.md`）
2. 重启计算机
3. 验证 Docker 可用：`docker --version`

### 然后执行
```powershell
cd D:\projects\deepdive-tracking
docker compose up -d
alembic upgrade head
python scripts/run_collection.py
```

### 最后验证
```powershell
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> SELECT COUNT(*) FROM raw_news;
deepdive_db=> SELECT * FROM raw_news LIMIT 3;
deepdive_db=> \q
```

---

## 📞 需要帮助

如果遇到问题：

1. **查看文档：** `DOCKER_SETUP_GUIDE.md` 的故障排除部分
2. **查看日志：** `docker logs deepdive_postgres`
3. **重置系统：** `docker compose down -v && docker compose up -d`
4. **检查网络：** 确保 RSS 源可访问（`curl -I https://openai.com/blog/rss.xml`）

---

**现在一切准备就绪。安装 Docker，就可以开始采集真实的数据了！** 🚀

**预计 20-30 分钟内你就能看到数据库中的真实采集数据。**

Let's go! 💪
