# 3060 Streamlit Health Check
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File check_health.ps1

$ErrorActionPreference = "Stop"
$ProjectDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$HealthUrl = "http://127.0.0.1:8502/_stcore/health"
$Proc = $null

function Stop-StreamlitByWmi {
    try {
        Get-CimInstance Win32_Process -Filter "name = 'python.exe' OR name = 'pythonw.exe'" |
            Where-Object { $_.CommandLine -like "*streamlit*" -and $_.CommandLine -like "*8502*" } |
            ForEach-Object {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
    } catch {
        Write-Output "WARN: WMI cleanup skipped: $($_.Exception.Message)"
    }
}

try {
    Write-Output "=== Step 1: Clean old streamlit on port 8502 ==="
    Stop-StreamlitByWmi
    Start-Sleep -Seconds 1

    Write-Output "=== Step 2: Start streamlit ==="
    Set-Location $ProjectDir
    $Args = @(
        "-m", "streamlit", "run", "app.py",
        "--server.address", "127.0.0.1",
        "--server.port", "8502",
        "--server.headless", "true"
    )
    $Proc = Start-Process python -ArgumentList $Args -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 8

    Write-Output "=== Step 3: Health check ==="
    $resp = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 15
    Write-Output "HTTP Status: $($resp.StatusCode)"
    Write-Output "Content: $($resp.Content)"
    if ($resp.StatusCode -eq 200 -and "$($resp.Content)".Trim() -eq "ok") {
        Write-Output "HEALTH_CHECK_OK"
        exit 0
    }

    Write-Output "HEALTH_CHECK_FAIL: unexpected response"
    exit 1
} catch {
    Write-Output "HEALTH_CHECK_FAIL: $($_.Exception.Message)"
    exit 1
} finally {
    Write-Output "=== Step 4: Stop streamlit ==="
    if ($null -ne $Proc) {
        Stop-Process -Id $Proc.Id -Force -ErrorAction SilentlyContinue
    }
    Stop-StreamlitByWmi
    Write-Output "CLEANED"
}
