$ErrorActionPreference = "Stop"
$port = 8502
$workDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"

Write-Output "=== Starting Streamlit on port $port ==="
$proc = Start-Process -FilePath "streamlit" `
    -ArgumentList "run", "app.py", "--server.address", "0.0.0.0", "--server.port", $port, "--server.headless", "true" `
    -WorkingDirectory $workDir `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 10

try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$port/_stcore/health"
    Write-Output "Health StatusCode: $($resp.StatusCode)"
    Write-Output "Health Content: $($resp.Content)"
} catch {
    Write-Output "Health check failed: $_"
}

Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Output "=== Streamlit health check done ==="
