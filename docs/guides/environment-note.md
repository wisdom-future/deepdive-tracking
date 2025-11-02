# 环境说明 - 关于 Bash vs PowerShell

## 当前开发环境

- **环境**：MINGW64 bash（Git Bash）
- **使用场景**：代码开发、Git 操作、Python 开发
- **局限**：Docker 不在此环境可用

## 数据采集执行环境

- **环境**：Windows PowerShell
- **使用场景**：Docker 容器管理、数据库操作
- **优势**：与 Windows Docker Desktop 无缝集成

---

## 为什么需要两个环境？

### Bash 环境（当前）
```
优势：
✓ Git 集成好
✓ Unix/Linux 风格命令
✓ Python 开发流畅
✓ 代码编辑方便

局限：
✗ Docker 与 Windows 隔离
✗ 无法访问 Docker 守护进程
```

### PowerShell 环境（执行采集）
```
优势：
✓ Windows 原生环境
✓ Docker Desktop 无缝集成
✓ 与系统深度整合
✓ 网络访问最佳

使用场景：
✓ docker compose up/down
✓ psql 连接
✓ 系统级操作
```

---

## 执行流程

### 开发阶段（Bash）
```bash
# 在 Git Bash 中
code scripts/run_collection.py    # 编辑代码
python -m pytest                  # 运行测试
git commit -am "feat: ..."        # 提交更改
```

### 执行阶段（PowerShell）
```powershell
# 在 Windows PowerShell 中
docker compose up -d              # 启动数据库
alembic upgrade head              # 迁移数据库
python scripts/run_collection.py  # 运行采集
psql -h localhost -U deepdive -d deepdive_db  # 查询数据
```

---

## 如何在 PowerShell 中执行

### 打开 PowerShell

1. **方式 1**：按 `Win + X`，选择 `Windows PowerShell` 或 `PowerShell`
2. **方式 2**：在开始菜单搜索 `PowerShell`
3. **方式 3**：在文件管理器中 `Shift + 右键`，选择 `在此处打开 PowerShell`

### 完整执行命令

```powershell
# 进入项目目录
cd D:\projects\deepdive-tracking

# 1. 启动 Docker 容器
docker compose up -d

# 2. 等待 PostgreSQL 启动
Start-Sleep -Seconds 30

# 3. 初始化数据库
alembic upgrade head

# 4. 运行采集
python scripts/run_collection.py

# 5. 验证数据
psql -h localhost -U deepdive -d deepdive_db -c "SELECT COUNT(*) FROM raw_news;"
```

---

## 验证安装

在 PowerShell 中检查必要工具：

```powershell
# 检查 Docker
docker --version
# 预期：Docker version 26.0.0 (或更新)

# 检查 Python
python --version
# 预期：Python 3.10 或更新

# 检查 psql
psql --version
# 预期：psql (PostgreSQL) 15.0 (或相近版本)

# 检查 alembic
alembic --version
# 预期：alembic 1.12.0 (或更新)
```

---

## 快速导航

- **快速开始**：`docs/guides/execution-instructions.md`
- **详细指南**：`docs/guides/execution-guide.md`
- **Docker 安装**：`docs/guides/docker-setup-guide.md`
- **故障排查**：`docs/guides/execution-guide.md#常见问题排查`

---

## 一句话总结

**在 Bash 中开发，在 PowerShell 中执行。**

---
