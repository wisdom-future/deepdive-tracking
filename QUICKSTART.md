# 快速开始 - 5 分钟启动数据采集

## 三步启动系统

### 步骤 1: 安装 Docker (5-10 分钟)

在 PowerShell 中以**管理员身份**运行：

```powershell
powershell -ExecutionPolicy Bypass -File install-docker.ps1
```

这个脚本会：
- ✅ 检查 Windows 版本
- ✅ 下载 Docker Desktop
- ✅ 自动安装
- ✅ 验证安装成功

安装完成后**重启计算机**（可选但推荐）。

### 步骤 2: 启动采集系统 (3 分钟)

Docker 安装完成后，在 PowerShell 中运行：

```powershell
cd D:\projects\deepdive-tracking
powershell -ExecutionPolicy Bypass -File run-collection.ps1
```

这个脚本会：
- ✅ 启动 PostgreSQL 和 Redis 容器
- ✅ 初始化数据库架构
- ✅ 运行真实数据采集
- ✅ 显示采集统计

### 步骤 3: 验证数据 (1 分钟)

采集完成后，查看采集的数据：

```powershell
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> SELECT COUNT(*) FROM raw_news;
deepdive_db=> \q
```

---

## 常见问题

### Q: 脚本说需要管理员权限怎么办？

**A:** 右键点击 PowerShell，选择"以管理员身份运行"。

### Q: Docker 安装后仍然找不到命令？

**A:** 重启计算机，Docker 需要重新注册环境变量。

### Q: 下载 Docker 太慢？

**A:** 可以手动下载：https://www.docker.com/products/docker-desktop

### Q: 采集没有数据怎么办？

**A:** 检查 RSS 源是否可访问：
```powershell
curl -I https://openai.com/blog/rss.xml
```

### Q: 怎么停止容器？

**A:** 运行：
```powershell
docker compose down
```

---

## 详细文档

- **Docker 安装指南**: `docs/guides/docker-setup-guide.md`
- **系统就绪报告**: `.claude/handoff/system-ready.md`
- **下一步执行**: `.claude/handoff/next-steps.md`
- **交付总结**: `.claude/handoff/deliverable-summary.md`

---

## 系统要求

- Windows 10 或更高版本
- 4GB+ RAM (推荐 8GB)
- 10GB+ 可用磁盘空间
- 网络连接

---

## 成功指标

✅ 安装成功：
```powershell
docker --version
# 输出: Docker version 26.0.0 (或更新)
```

✅ 采集成功：
```powershell
psql -h localhost -U deepdive -d deepdive_db
deepdive_db=> SELECT COUNT(*) FROM raw_news;
# 输出: 15 (或更多)
```

---

**预计总耗时：15-30 分钟**

**现在开始：右键运行 PowerShell 以管理员身份，然后执行上面的命令！** 🚀
