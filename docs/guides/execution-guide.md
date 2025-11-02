# 系统执行指南 - 完整步骤

**最后更新：** 2025-11-02
**状态：** 系统完全就绪，等待用户执行
**预计耗时：** 20-30 分钟

---

## 总体流程图

```
步骤 1: 安装 Docker
    ↓
    (重启计算机 - 可选但推荐)
    ↓
步骤 2: 启动系统 & 运行采集
    ↓
步骤 3: 验证数据
    ↓
采集完成！数据已保存到 PostgreSQL
```

---

## 详细执行步骤

### 步骤 1️⃣: 安装 Docker (5-15 分钟)

#### 方式 A: 使用自动化脚本（推荐）

1. **打开 PowerShell**
   - 按 `Win + X`
   - 选择 `Windows PowerShell (管理员)`

2. **运行安装脚本**
   ```powershell
   cd D:\projects\deepdive-tracking
   powershell -ExecutionPolicy Bypass -File scripts/setup/install-docker.ps1
   ```

3. **等待安装完成**
   - 脚本会自动下载并安装 Docker Desktop
   - 预计 5-15 分钟（取决于网络速度）

4. **重启计算机**（可选但推荐）
   ```powershell
   Restart-Computer
   ```

#### 方式 B: 手动安装

1. 访问：https://www.docker.com/products/docker-desktop
2. 点击 `Download for Windows`
3. 下载完成后，运行安装程序
4. 按默认选项完成安装
5. 重启计算机

#### 验证 Docker 安装成功

```powershell
docker --version
# 预期输出: Docker version 26.0.0 (或更新)

docker compose version
# 预期输出: Docker Compose version 2.26.0 (或更新)
```

---

### 步骤 2️⃣: 启动系统 & 运行采集 (3-5 分钟)

#### 方式 A: 使用自动化脚本（推荐）

1. **打开 PowerShell**（如果重启过，打开新窗口）

2. **运行采集脚本**
   ```powershell
   cd D:\projects\deepdive-tracking
   powershell -ExecutionPolicy Bypass -File scripts/setup/run-collection.ps1
   ```

3. **等待脚本完成**
   - 脚本会依次执行：
     - [1/4] 检查 Docker 状态
     - [2/4] 启动 PostgreSQL 和 Redis 容器
     - [3/4] 初始化数据库架构
     - [4/4] 运行真实数据采集
   - 总耗时：3-5 分钟

4. **查看输出结果**
   ```
   ================================================================================
   DeepDive Tracking - Real Data Collection
   ================================================================================

   [1] 连接到PostgreSQL数据库...
       OK - Connected to postgresql://deepdive:***@localhost:5432/deepdive_db

   [2] 检查数据源配置...
       OK - Found 2 enabled sources:
       + OpenAI Blog (rss)
       + Anthropic News (rss)

   [3] 开始采集数据...
       时间: 2025-11-02T15:30:45.123456
       (这可能需要30-60秒)

   [4] 采集结果统计
   ================================================================================
   总采集数量: 15
   新增数量:   15
   重复数量:   0

   [5] 采集到的数据样本 (最新10条)
   ================================================================================

   1. [raw] GPT-4 Turbo with vision capabilities
      来源: OpenAI Blog
      URL: https://openai.com/blog/gpt-4-turbo-vision
      发布时间: 2024-11-06 10:30:00+00:00
      采集时间: 2025-11-02 15:30:45.123456
      ...
   ```

#### 方式 B: 手动执行（用于调试）

```powershell
# 1. 启动容器
docker compose up -d

# 2. 等待 PostgreSQL 初始化（20-30 秒）
docker compose logs postgres | tail -5
# 应看到: "database system is ready to accept connections"

# 3. 运行数据库迁移
alembic upgrade head

# 4. 运行采集
python scripts/run_collection.py
```

---

### 步骤 3️⃣: 验证采集数据 (2-3 分钟)

#### 查询采集的数据

```powershell
# 连接到 PostgreSQL
psql -h localhost -U deepdive -d deepdive_db

# 在 psql 提示符下：
deepdive_db=> SELECT COUNT(*) FROM raw_news;
 count
-------
    15
(1 row)

# 查看具体数据
deepdive_db=> SELECT id, title, source_name, published_at FROM raw_news LIMIT 3;
 id |                        title                        | source_name   |       published_at
----+------------------------------------------------------+---------------+------------------------
  1 | GPT-4 Turbo with vision capabilities               | OpenAI Blog   | 2024-11-06 10:30:00+00
  2 | Introducing Claude 3.5 Sonnet                      | Anthropic     | 2024-11-05 14:20:00+00
  3 | Google DeepMind announces new research breakthrough | DeepMind      | 2024-11-04 09:15:00+00
(3 rows)

# 查看采集统计
deepdive_db=> SELECT
  source_name,
  COUNT(*) as total,
  COUNT(CASE WHEN is_duplicate THEN 1 END) as duplicates
FROM raw_news
GROUP BY source_name;
 source_name   | total | duplicates
---------------+-------+------------
 OpenAI Blog   |     8 |          0
 Anthropic     |     7 |          0
(2 rows)

# 退出 psql
deepdive_db=> \q
```

#### 使用 GUI 工具查看数据（可选）

**推荐工具：DBeaver（免费）**

1. 下载：https://dbeaver.io/download/
2. 新建连接，配置如下：
   - Host: localhost
   - Port: 5432
   - Database: deepdive_db
   - Username: deepdive
   - Password: deepdive_password
3. 连接后可以浏览 raw_news 表中的所有数据

---

## 常见问题排查

### ❌ Docker 安装脚本失败

**现象：** 脚本说 "ERROR: 无法下载 Docker Desktop"

**解决：**
```powershell
# 1. 手动下载
# 访问: https://www.docker.com/products/docker-desktop
# 下载 "Docker Desktop Installer.exe"

# 2. 运行安装程序
# 双击下载的 installer，按默认选项安装

# 3. 重启计算机

# 4. 验证
docker --version
```

### ❌ 采集脚本说 Docker 未运行

**现象：**
```
ERROR - 无法连接数据库: connection to server at "localhost" port 5432 failed
```

**解决：**
```powershell
# 1. 检查 Docker Desktop 是否在任务栏运行
# (右下角看是否有 Docker 图标)

# 2. 如果没有，手动启动 Docker Desktop
# (在开始菜单搜索 "Docker")

# 3. 等待 Docker 完全启动（30-60 秒）

# 4. 重试采集脚本
powershell -ExecutionPolicy Bypass -File scripts/setup/run-collection.ps1
```

### ❌ 迁移脚本失败

**现象：**
```
sqlalchemy.exc.OperationalError: connection to server... refused
```

**解决：**
```powershell
# 1. 检查 PostgreSQL 容器
docker compose logs postgres

# 2. 重启容器
docker compose restart postgres

# 3. 等待 30 秒
Start-Sleep -Seconds 30

# 4. 重试迁移
alembic upgrade head
```

### ❌ 采集没有数据

**现象：**
```
采集结果统计
总采集数量: 0
```

**解决：**
```powershell
# 1. 检查网络连接
# 打开浏览器访问 RSS 源：
# https://openai.com/blog/rss.xml

# 2. 检查数据源是否创建
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> SELECT * FROM data_sources;
# 应该显示 2 条记录

# 3. 如果为空，脚本会自动创建
# 重新运行采集脚本即可
python scripts/run_collection.py
```

### ❌ psql 命令找不到

**现象：** "psql: command not found"

**解决：**
```powershell
# psql 是 PostgreSQL 客户端，需要单独安装

# 选项 1: 使用 Docker 中的 psql
docker compose exec postgres psql -U deepdive -d deepdive_db

# 选项 2: 安装 PostgreSQL 客户端
# 下载: https://www.postgresql.org/download/windows/
# 安装时只需选择 "PostgreSQL Client"

# 或使用 GUI 工具 DBeaver 代替 psql
```

---

## 预期时间表

| 步骤 | 任务 | 耗时 |
|------|------|------|
| 1 | Docker 安装 | 5-15 分钟 |
| 1 | 重启计算机 | 2-3 分钟（可选） |
| 2 | 启动容器 | 30 秒 |
| 2 | 数据库迁移 | 10 秒 |
| 2 | 运行采集 | 1-2 分钟 |
| 3 | 数据验证 | 1 分钟 |
| **总计** | **完整流程** | **20-30 分钟** |

---

## 系统要求检查清单

- [ ] Windows 10 或更高版本
- [ ] 4GB+ RAM（推荐 8GB）
- [ ] 10GB+ 可用磁盘空间
- [ ] 网络连接（用于下载 Docker 和 RSS 源）
- [ ] PowerShell（Windows 内置）
- [ ] 管理员权限（用于安装 Docker）

---

## 成功指标

✅ **Docker 安装成功：**
```powershell
docker --version
# Docker version 26.0.0 (或更新)
```

✅ **容器运行成功：**
```powershell
docker ps
# 应显示 2 个容器（postgres 和 redis）
```

✅ **数据库迁移成功：**
```powershell
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> \dt
# 应显示 12 张表
```

✅ **采集成功：**
```powershell
python scripts/run_collection.py
# 显示 "总采集数量: 15" 或更多
```

✅ **数据验证成功：**
```powershell
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> SELECT COUNT(*) FROM raw_news;
# count: 15 (或更多)
```

---

## 下一步

采集完成后，你可以：

1. **查看更多数据**
   ```sql
   SELECT * FROM raw_news WHERE source_name = 'OpenAI Blog' LIMIT 10;
   ```

2. **导出数据**
   ```sql
   \copy (SELECT * FROM raw_news) TO 'export.csv' WITH CSV HEADER;
   ```

3. **停止容器**
   ```powershell
   docker compose down
   ```

4. **开发后续功能**
   - AI 评分服务（下一个 Phase）
   - 内容编辑服务
   - 多渠道发布

---

## 技术支持

遇到问题？

1. **查看详细指南**
   - `docs/guides/docker-setup-guide.md` - Docker 安装细节
   - `.claude/handoff/next-steps.md` - 完整执行流程

2. **查看日志**
   ```powershell
   docker logs deepdive_postgres
   docker logs deepdive_redis
   ```

3. **重置系统**
   ```powershell
   docker compose down -v
   docker compose up -d
   ```

---

**现在开始！按照上面的步骤，20-30 分钟内你就能看到采集的真实数据。** 🚀

**开始：右键打开 PowerShell（管理员）→ 运行 `scripts/setup/install-docker.ps1`**
