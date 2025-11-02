# 执行说明 - 在 Windows PowerShell 中运行

**重要：** 这个项目在 MINGW64 bash 环境中开发，但数据采集需要在 **Windows PowerShell** 中执行。

---

## 🎯 快速执行（PowerShell）

在 **Windows PowerShell** 中运行以下命令：

```powershell
# 进入项目目录
cd D:\projects\deepdive-tracking

# 1. 启动数据库容器 (2 分钟)
docker compose up -d
Start-Sleep -Seconds 30

# 2. 初始化数据库 (30 秒)
alembic upgrade head

# 3. 运行采集 (2-3 分钟)
python scripts/run_collection.py

# 4. 验证数据 (1 分钟)
psql -h localhost -U deepdive -d deepdive_db -c "SELECT COUNT(*) FROM raw_news;"
```

---

## ✅ 预期输出

### 步骤 1: Docker 启动
```
Creating deepdive_postgres ... done
Creating deepdive_redis ... done
```

### 步骤 2: 数据库迁移
```
INFO  [alembic.runtime.migration] Running upgrade -> 001_init..., create all tables
```

### 步骤 3: 数据采集
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

[4] 采集结果统计
================================================================================
总采集数量: 15
新增数量:   15
重复数量:   0
```

### 步骤 4: 验证数据
```
 count
-------
    15
(1 row)
```

---

## 📊 查看完整数据

```powershell
# 连接到数据库
psql -h localhost -U deepdive -d deepdive_db

# 在 psql 提示符下：

# 查看新闻列表
deepdive_db=> SELECT id, title, source_name FROM raw_news LIMIT 5;

# 查看统计
deepdive_db=> SELECT source_name, COUNT(*) FROM raw_news GROUP BY source_name;

# 查看具体内容
deepdive_db=> SELECT title, content FROM raw_news WHERE id = 1;

# 退出
deepdive_db=> \q
```

---

## 🛑 前置条件

- ✅ Docker Desktop 已安装
- ✅ Docker Desktop 正在运行
- ✅ Python 3.10+ 已安装
- ✅ PostgreSQL 客户端 (psql) 已安装

如果缺少条件，参考：`docs/guides/docker-setup-guide.md`

---

## 🔧 故障排查

参考完整指南：`docs/guides/execution-guide.md`

---

**总耗时：5-10 分钟**
