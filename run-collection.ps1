# 启动完整的数据采集流程
# 使用方法: powershell -ExecutionPolicy Bypass -File run-collection.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DeepDive Tracking - 完整数据采集流程" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = "D:\projects\deepdive-tracking"
cd $projectPath

# 步骤 1: 验证 Docker
Write-Host "[1/4] 检查 Docker 状态..." -ForegroundColor Green
try {
    $dockerVersion = & docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✓ $dockerVersion" -ForegroundColor Green
    } else {
        throw "Docker 不可用"
    }
} catch {
    Write-Host "      ✗ Docker 未安装或未运行" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先运行: powershell -ExecutionPolicy Bypass -File install-docker.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 步骤 2: 启动容器
Write-Host "[2/4] 启动 PostgreSQL 和 Redis 容器..." -ForegroundColor Green
Write-Host "      运行: docker compose up -d" -ForegroundColor Gray

try {
    & docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up 失败"
    }
    Write-Host "      ✓ 容器启动成功" -ForegroundColor Green
} catch {
    Write-Host "      ✗ 容器启动失败: $_" -ForegroundColor Red
    exit 1
}

# 等待 PostgreSQL 准备好
Write-Host "      等待数据库初始化..." -NoNewline
$maxRetries = 30
for ($i = 0; $i -lt $maxRetries; $i++) {
    try {
        $containerStatus = & docker compose exec postgres pg_isready -U deepdive 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " 完成!" -ForegroundColor Green
            break
        }
    } catch {
        # 继续等待
    }
    Start-Sleep -Seconds 1
    Write-Host "." -NoNewline
}
Write-Host ""

# 验证容器状态
Write-Host "      验证容器状态:" -ForegroundColor Gray
$containers = & docker compose ps --format "table {{.Names}}\t{{.Status}}"
Write-Host $containers | Select-Object -First 3
Write-Host ""

# 步骤 3: 运行迁移
Write-Host "[3/4] 初始化数据库架构..." -ForegroundColor Green
Write-Host "      运行: alembic upgrade head" -ForegroundColor Gray

try {
    & alembic upgrade head
    if ($LASTEXITCODE -ne 0) {
        throw "alembic upgrade 失败"
    }
    Write-Host "      ✓ 数据库架构初始化成功" -ForegroundColor Green
} catch {
    Write-Host "      ✗ 迁移失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "故障排除:" -ForegroundColor Yellow
    Write-Host "1. 检查 PostgreSQL 日志: docker logs deepdive_postgres" -ForegroundColor Gray
    Write-Host "2. 尝试重置: docker compose down -v && docker compose up -d" -ForegroundColor Gray
    exit 1
}
Write-Host ""

# 步骤 4: 执行采集
Write-Host "[4/4] 执行真实数据采集..." -ForegroundColor Green
Write-Host "      运行: python scripts/run_collection.py" -ForegroundColor Gray
Write-Host ""

try {
    & python scripts/run_collection.py
    if ($LASTEXITCODE -ne 0) {
        throw "采集脚本失败"
    }
} catch {
    Write-Host "      ✗ 采集执行失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "数据采集完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 验证数据
Write-Host "验证采集结果..." -ForegroundColor Green
Write-Host "运行以下命令查看采集的数据:" -ForegroundColor Gray
Write-Host ""
Write-Host "  psql -h localhost -U deepdive -d deepdive_db" -ForegroundColor White
Write-Host "  deepdive_db=> SELECT COUNT(*) FROM raw_news;" -ForegroundColor White
Write-Host "  deepdive_db=> SELECT id, title, source_name FROM raw_news LIMIT 5;" -ForegroundColor White
Write-Host ""

Write-Host "✓ 完成！你的数据已保存到 PostgreSQL 数据库。" -ForegroundColor Green
Write-Host ""
