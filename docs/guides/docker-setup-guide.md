# Docker 设置指南 - 数据采集系统启动

**状态：** Docker 尚未安装或不在 PATH 中
**环境：** Windows (PowerShell)
**目标：** 启动 PostgreSQL + Redis 基础设施

---

## 🔍 当前环境检查

```
✓ Python: 已安装 (Python 3.13)
✓ PostgreSQL 客户端库 (psycopg2): 已安装
✗ Docker: 未安装或不在 PATH 中
✗ Docker Compose: 不可用
```

---

## 📦 Docker 安装步骤

### 步骤 1: 下载 Docker Desktop

访问 https://www.docker.com/products/docker-desktop 下载 Windows 版本。

**推荐配置：**
- Docker Desktop for Windows (最新版本)
- 需要 Windows 10 或更高版本
- 推荐 4GB+ 内存分配给 Docker

### 步骤 2: 安装 Docker Desktop

1. 运行下载的安装程序
2. 勾选 "Install required Windows components for WSL 2 backend"
3. 完成安装后**重启计算机**
4. Docker Desktop 将在后台自动启动

### 步骤 3: 验证 Docker 安装

**打开 PowerShell 并运行：**

```powershell
# 检查 Docker 版本
docker --version
# 预期输出: Docker version 26.0.0 (或更新版本)

# 检查 Docker Compose 版本
docker compose version
# 预期输出: Docker Compose version 2.26.0 (或更新版本)

# 验证 Docker 守护进程运行
docker ps
# 预期输出: 容器列表（可能为空）
```

### 步骤 4: 解决常见问题

**问题 1: "Docker daemon is not running"**
- 检查 Docker Desktop 是否在后台运行（任务栏右下角）
- 如果没有，手动启动 Docker Desktop
- 等待 Docker 完全启动（约 30 秒）

**问题 2: "command not found: docker"**
- Docker Desktop 安装后需要重启电脑
- 重启后在新的 PowerShell 窗口中重试
- 如果仍然不行，检查系统 PATH 环境变量是否包含 Docker 路径

**问题 3: WSL 2 安装失败**
- 下载 WSL 2 Linux Kernel 更新包：
  https://docs.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package
- 运行更新包
- 重启 Docker Desktop

---

## 🚀 一旦 Docker 安装完成

在验证 Docker 可用后，运行以下命令启动我们的系统：

### 启动数据库基础设施

**打开 PowerShell，进入项目目录：**

```powershell
# 进入项目目录
cd D:\projects\deepdive-tracking

# 启动 PostgreSQL 和 Redis
docker compose up -d

# 验证容器是否运行
docker ps

# 预期输出：
# CONTAINER ID   IMAGE             COMMAND                  STATUS
# abc12345       postgres:15-alpine "docker-entrypoint..."   Up 2 seconds
# def67890       redis:7-alpine    "redis-server"           Up 2 seconds
```

### 初始化数据库

```powershell
# 运行数据库迁移
alembic upgrade head

# 预期输出：
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl
# INFO  [alembic.runtime.migration] Will assume transactional DDL
# INFO  [alembic.runtime.migration] Running upgrade  -> 001_init..., create all tables
```

### 执行数据采集

```powershell
# 运行真实数据采集脚本
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
#     (这可能需要30-60秒)
#
# [4] 采集结果统计
# ================================================================================
# 总采集数量: 15
# 新增数量:   15
# 重复数量:   0
# ...
```

---

## ✅ Docker 快速参考

### 常用命令

```bash
# 查看容器状态
docker ps

# 查看容器日志
docker logs deepdive_postgres
docker logs deepdive_redis

# 停止所有容器
docker compose down

# 完全删除容器和数据（重新开始）
docker compose down -v

# 重启容器
docker compose restart

# 进入 PostgreSQL 容器的 shell
docker exec -it deepdive_postgres psql -U deepdive -d deepdive_db

# 查看容器详细信息
docker inspect deepdive_postgres
```

### 故障排除

**容器无法启动：**
```bash
# 查看具体错误
docker compose logs postgres

# 完全重置
docker compose down -v
docker compose up -d
```

**PostgreSQL 无法连接：**
```bash
# 检查容器是否运行
docker ps | grep postgres

# 检查健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"

# 等待容器完全启动（20-30 秒）
# 然后重试连接
```

**磁盘空间不足：**
```bash
# 清理 Docker 资源
docker system prune -a

# 重新启动系统
docker compose up -d
```

---

## 📊 系统配置检查清单

- [ ] Docker Desktop 已安装
- [ ] Docker 命令可用：`docker --version` 返回版本号
- [ ] Docker Compose 可用：`docker compose version` 返回版本号
- [ ] Docker 守护进程运行：`docker ps` 无错误
- [ ] PostgreSQL 容器运行：`docker ps | grep postgres`
- [ ] Redis 容器运行：`docker ps | grep redis`
- [ ] 数据库迁移完成：`alembic current` 显示版本
- [ ] 采集脚本成功运行：显示采集统计
- [ ] 数据已保存到数据库：SQL 查询返回结果

---

## 🎯 下一步

1. **安装 Docker Desktop** - 按照上面的步骤安装
2. **验证 Docker 安装** - 运行 `docker --version`
3. **启动容器** - 运行 `docker compose up -d`
4. **初始化数据库** - 运行 `alembic upgrade head`
5. **执行采集** - 运行 `python scripts/run_collection.py`
6. **验证数据** - 使用 SQL 或 GUI 工具查看采集结果

---

## 📞 常见问题解答

**Q: 为什么需要 Docker？**
A: Docker 提供了一个隔离的、可重复的 PostgreSQL 环境。无需手动安装 PostgreSQL 和 Redis，只需一个命令即可启动完整的数据库系统。

**Q: Docker Desktop 会占用很多资源吗？**
A: 默认分配 2-4 GB 内存。可以在 Docker Desktop 设置中调整。我们的 PostgreSQL 和 Redis 容器非常轻量级。

**Q: 可以不用 Docker，直接安装 PostgreSQL 吗？**
A: 可以，但需要手动安装和配置 PostgreSQL 15。建议使用 Docker 以保持环境一致性。

**Q: Docker 启动后占用什么端口？**
A:
- PostgreSQL: `5432`（宿主机）
- Redis: `6379`（宿主机）

**Q: 可以同时运行多个 docker-compose 项目吗？**
A: 可以，只要端口不冲突。建议修改 docker-compose.yml 中的端口号。

---

## 🔗 参考资源

- Docker 官方文档：https://docs.docker.com/
- Docker Desktop for Windows：https://docs.docker.com/desktop/install/windows-install/
- Docker Compose 文档：https://docs.docker.com/compose/
- PostgreSQL Docker 镜像：https://hub.docker.com/_/postgres
- Redis Docker 镜像：https://hub.docker.com/_/redis

---

**一旦 Docker 安装完成，整个系统可以通过 4 个命令启动：**

```powershell
docker compose up -d
alembic upgrade head
python scripts/run_collection.py
# 验证数据在数据库中
```

**现在请安装 Docker Desktop，然后执行这些命令来启动真实的数据采集系统！** 🚀
