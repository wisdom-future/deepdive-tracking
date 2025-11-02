# 项目根目录整理总结

**完成时间：** 2025-11-02  
**状态：** ✅ 完成

## 问题识别

根目录曾经包含了不应该存在的文件：
- ❌ `deepdive_tracking.db` - 数据库文件（产生物）
- ❌ `database_export.txt` - 临时导出数据
- ❌ `news_summary.txt` - 临时汇总文件

## 改进方案

### 1. 创建数据目录结构

```
data/
├── db/
│   ├── .gitkeep
│   └── deepdive_tracking.db          # SQLite数据库（已添加到.gitignore）
└── exports/
    ├── .gitkeep
    ├── database_export.txt           # 导出数据
    └── news_summary.txt              # 数据汇总
```

### 2. 更新配置文件

**src/config/settings.py**
- 旧：`sqlite:///./deepdive_tracking.db`
- 新：`sqlite:///./data/db/deepdive_tracking.db`

**alembic.ini**
- 旧：`sqlalchemy.url = sqlite:///./deepdive_tracking.db`
- 新：`sqlalchemy.url = sqlite:///./data/db/deepdive_tracking.db`

### 3. 更新 .gitignore

添加了数据目录到忽略列表：
```
# Data and exports
data/
data/db/
data/exports/
```

## 根目录规范

现在根目录仅包含必要的配置文件：

### ✅ 应该在根目录的文件
- `CLAUDE.md` - 项目规范说明
- `README.md` - 项目文档
- `.env.example` - 环境变量模板
- `pyproject.toml` - Python项目配置
- `setup.py` - 安装脚本
- `Dockerfile` - Docker配置
- `docker-compose.yml` - Docker编排
- `Makefile` - 项目命令
- `LICENSE` - 许可证
- `alembic.ini` - 数据库迁移配置

### ❌ 不应该在根目录的文件
- 数据库文件 (`*.db`, `*.sqlite`)
- 导出数据文件
- 临时文件
- 构建产物

## 验证清单

- [x] 移动数据库文件到 `data/db/`
- [x] 移动导出文件到 `data/exports/`
- [x] 更新配置文件中的数据库路径
- [x] 更新 `.gitignore`
- [x] 创建 `.gitkeep` 文件以保持目录结构
- [x] 验证根目录仅包含必要的配置文件

## 后续说明

- 数据库文件不会被提交到 Git（已在 .gitignore 中）
- 导出文件也不会被提交（已在 .gitignore 中）
- 开发者可以在本地生成这些文件，但不会污染Git历史
