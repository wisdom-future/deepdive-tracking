# Docker 自动安装脚本 for Windows
# 使用方法: 在 PowerShell 中以管理员身份运行
# powershell -ExecutionPolicy Bypass -File install-docker.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop 自动安装脚本" -ForegroundColor Cyan
Write-Host "Windows 10/11" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否是管理员
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "ERROR: 此脚本需要管理员权限运行!" -ForegroundColor Red
    Write-Host "请以管理员身份运行 PowerShell，然后再次运行此脚本。" -ForegroundColor Yellow
    exit 1
}

# 检查 Windows 版本
Write-Host "[1/5] 检查 Windows 版本..." -ForegroundColor Green
$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Write-Host "ERROR: 需要 Windows 10 或更高版本" -ForegroundColor Red
    exit 1
}
Write-Host "      Windows 版本: $osVersion" -ForegroundColor Green
Write-Host ""

# 检查 Docker 是否已安装
Write-Host "[2/5] 检查 Docker 是否已安装..." -ForegroundColor Green
$dockerPath = "C:\Program Files\Docker\Docker\Docker.exe"
if (Test-Path $dockerPath) {
    Write-Host "      Docker 已安装在: $dockerPath" -ForegroundColor Green
    & $dockerPath --version
    Write-Host ""
    Write-Host "Docker 已安装。跳过下载..." -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "      Docker 未安装" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "[3/5] 下载 Docker Desktop..." -ForegroundColor Green
    $downloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $downloadPath = "$env:TEMP\DockerInstaller.exe"

    Write-Host "      下载链接: $downloadUrl" -ForegroundColor Gray
    Write-Host "      保存位置: $downloadPath" -ForegroundColor Gray

    try {
        # 显示进度
        $ProgressPreference = 'Continue'
        Write-Host "      下载中..." -NoNewline

        # 使用 System.Net.ServicePointManager 处理 HTTPS
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($downloadUrl, $downloadPath)

        Write-Host " 完成!" -ForegroundColor Green
    } catch {
        Write-Host " 失败!" -ForegroundColor Red
        Write-Host "ERROR: 无法下载 Docker Desktop" -ForegroundColor Red
        Write-Host "请手动访问: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        Write-Host "下载后，请运行安装程序。" -ForegroundColor Yellow
        exit 1
    }
    Write-Host ""

    Write-Host "[4/5] 安装 Docker Desktop..." -ForegroundColor Green
    Write-Host "      运行安装程序..." -NoNewline

    try {
        # 静默安装
        & $downloadPath install --quiet --accept-license
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            Write-Host " 完成!" -ForegroundColor Green
        } else {
            Write-Host " 进行中..." -ForegroundColor Yellow
            Write-Host "      安装程序可能在运行。请等待完成..." -ForegroundColor Yellow
            Write-Host "      (这可能需要 5-10 分钟)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host " (手动安装)" -ForegroundColor Yellow
        Write-Host "      请运行: $downloadPath" -ForegroundColor Yellow
        Write-Host "      然后重新运行此脚本。" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "[5/5] 验证 Docker 安装..." -ForegroundColor Green

# 等待 Docker 启动
Write-Host "      等待 Docker 初始化..." -NoNewline
$maxRetries = 30
$retryCount = 0

while ($retryCount -lt $maxRetries) {
    try {
        $dockerVersion = & docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host " 成功!" -ForegroundColor Green
            Write-Host "      $dockerVersion" -ForegroundColor Green
            break
        }
    } catch {
        # 继续等待
    }

    Start-Sleep -Seconds 1
    $retryCount++
    Write-Host "." -NoNewline
}

if ($retryCount -ge $maxRetries) {
    Write-Host " 超时!" -ForegroundColor Yellow
    Write-Host "      Docker 初始化可能需要更长时间。" -ForegroundColor Yellow
    Write-Host "      请手动运行: docker --version" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ""

# 验证 Docker Compose
Write-Host "验证 Docker Compose..." -ForegroundColor Green
try {
    $composeVersion = & docker compose version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker Compose 尚未可用（可能需要重启）" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ 无法验证 Docker Compose" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装步骤完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "后续步骤:" -ForegroundColor Green
Write-Host "1. 重启计算机 (推荐)" -ForegroundColor White
Write-Host "   或者等待 Docker Desktop 完全启动 (5-10 分钟)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 验证 Docker 可用:" -ForegroundColor White
Write-Host "   docker ps" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 启动数据采集系统:" -ForegroundColor White
Write-Host "   cd D:\projects\deepdive-tracking" -ForegroundColor Gray
Write-Host "   docker compose up -d" -ForegroundColor Gray
Write-Host "   alembic upgrade head" -ForegroundColor Gray
Write-Host "   python scripts/run_collection.py" -ForegroundColor Gray
Write-Host ""

Write-Host "💡 提示:" -ForegroundColor Cyan
Write-Host "  - Docker Desktop 需要后台运行" -ForegroundColor Gray
Write-Host "  - 首次启动可能需要 30-60 秒" -ForegroundColor Gray
Write-Host "  - 如果遇到问题，重启计算机试试" -ForegroundColor Gray
Write-Host ""

Write-Host "✓ 脚本执行完成！" -ForegroundColor Green
