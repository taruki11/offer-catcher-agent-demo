# 3060 公网部署一键脚本
# 在 3060 上直接运行此脚本（管理员 PowerShell）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Offer 捕手 - 3060 公网部署脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 步骤 1：检查 Python / Streamlit
# ---------------------------------------------------------------------------
Write-Host "`n[1/5] 检查 Python / Streamlit..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Python 未安装或不在 PATH" -ForegroundColor Red
    exit 1
}

$streamlitOk = python -c "import streamlit; print('OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Streamlit 未安装，正在安装..." -ForegroundColor Yellow
    pip install streamlit
}

# ---------------------------------------------------------------------------
# 步骤 2：检查项目文件
# ---------------------------------------------------------------------------
Write-Host "`n[2/5] 检查项目文件..." -ForegroundColor Yellow

$projectDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
if (-not (Test-Path $projectDir)) {
    Write-Host "  [FAIL] 项目目录不存在: $projectDir" -ForegroundColor Red
    Write-Host "  请先从本地同步文件到 3060" -ForegroundColor Yellow
    exit 1
}

$appPy = Join-Path $projectDir "app.py"
if (-not (Test-Path $appPy)) {
    Write-Host "  [FAIL] app.py 不存在: $appPy" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] 项目文件检查通过: $appPy" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 步骤 3：下载 cloudflared（免费公网穿透，无需账号）
# ---------------------------------------------------------------------------
Write-Host "`n[3/5] 检查 cloudflared..." -ForegroundColor Yellow

$cloudflared = "$env:USERPROFILE\cloudflared.exe"
$useCloudflare = $false

if (Test-Path $cloudflared) {
    Write-Host "  [OK] cloudflared 已存在: $cloudflared" -ForegroundColor Green
    $useCloudflare = $true
} else {
    Write-Host "  正在下载 cloudflared（公网穿透工具）..." -ForegroundColor Yellow
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    try {
        Invoke-WebRequest -Uri $url -OutFile $cloudflared -ErrorAction Stop
        Write-Host "  [OK] cloudflared 下载完成" -ForegroundColor Green
        $useCloudflare = $true
    } catch {
        Write-Host "  [WARN] GitHub 下载失败，尝试国内镜像..." -ForegroundColor Yellow
        $url2 = "https://ghproxy.com/https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        try {
            Invoke-WebRequest -Uri $url2 -OutFile $cloudflared -ErrorAction Stop
            Write-Host "  [OK] cloudflared 下载完成（国内镜像）" -ForegroundColor Green
            $useCloudflare = $true
        } catch {
            Write-Host "  [WARN] cloudflared 下载失败，将使用直接端口方式" -ForegroundColor Yellow
        }
    }
}

# ---------------------------------------------------------------------------
# 步骤 4：启动 Streamlit（后台）
# ---------------------------------------------------------------------------
Write-Host "`n[4/5] 启动 Streamlit..." -ForegroundColor Yellow

# 检查 8501 端口是否被占用
$portInUse = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "  [WARN] 端口 8501 已被占用，正在停止旧进程..." -ForegroundColor Yellow
    $oldPid = $portInUse.OwningProcess
    Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 启动 Streamlit（后台）
$streamlitLog = "$projectDir\streamlit.log"
$streamlitCmd = "cd '$projectDir'; streamlit run app.py --server.port 8501 --server.address 127.0.0.1"
Start-Process powershell -ArgumentList "-NoProfile", "-Command", $streamlitCmd `
    -RedirectStandardOutput $streamlitLog -RedirectStandardError $streamlitLog

Start-Sleep -Seconds 8

# 验证 Streamlit 是否启动
$streamlitRunning = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
if (-not $streamlitRunning) {
    Write-Host "  [FAIL] Streamlit 启动失败，请查看日志: $streamlitLog" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Streamlit 已启动: http://localhost:8501" -ForegroundColor Green

# ---------------------------------------------------------------------------
# 步骤 5：启动公网穿透
# ---------------------------------------------------------------------------
Write-Host "`n[5/5] 启动公网穿透..." -ForegroundColor Yellow

if ($useCloudflare -and (Test-Path $cloudflared)) {
    Write-Host "  使用 Cloudflare Tunnel（免费，无需注册）..." -ForegroundColor Cyan
    Write-Host "  公网地址将在下方显示，请等待..." -ForegroundColor Yellow
    Write-Host "  （按 Ctrl+C 停止）" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    
    & $cloudflared tunnel --url http://localhost:8501
} else {
    Write-Host "  未安装 cloudflared，使用直接端口方式..." -ForegroundColor Yellow
    Write-Host "  请在校园网内访问以下地址之一：" -ForegroundColor Cyan
    
    Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^127|^169|^10\.111' } | ForEach-Object {
        Write-Host "    http://$($_.IPAddress):8501" -ForegroundColor Green
    }
    
    Write-Host "`n  如果需要在公网访问，请手动安装 cloudflared：" -ForegroundColor Yellow
    Write-Host "    https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Cyan
    
    Write-Host "`n  按任意键退出..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  部署脚本执行完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
