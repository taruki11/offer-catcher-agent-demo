# start_and_check.ps1 - Start Streamlit and health check on 3060
$ErrorActionPreference = "Continue"

Set-Location "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"

# Kill any existing streamlit python processes
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.MainWindowTitle -like "*streamlit*") {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

# Start Streamlit in background
$argList = "-m", "streamlit", "run", "app.py", "--server.address", "127.0.0.1", "--server.port", "8502", "--server.headless", "true"
Start-Process -FilePath python -ArgumentList $argList -WindowStyle Hidden

Write-Output "Waiting for streamlit to start..."
Start-Sleep 8

# Health check
try {
    $r = Invoke-WebRequest -Uri http://127.0.0.1:8502/_stcore/health -UseBasicParsing -TimeoutSec 10
    Write-Output "HEALTH_OK $($r.StatusCode)"
    Write-Output $r.Content
} catch {
    Write-Output "HEALTH_FAIL $_"
}
