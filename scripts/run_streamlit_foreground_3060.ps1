# Run Streamlit in the foreground for an SSH tunnel session.
# This script intentionally does not detach. Keep the SSH process alive.

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$ProjectDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$Python = "D:\anaconda3\envs\pytorch123\python.exe"
$Port = 8502

function Stop-OldStreamlit {
    try {
        Get-CimInstance Win32_Process -Filter "name = 'python.exe' OR name = 'pythonw.exe'" |
            Where-Object { $_.CommandLine -like "*streamlit*" -and $_.CommandLine -like "*$Port*" } |
            ForEach-Object {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
    } catch {
    }
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python not found: $Python"
}

Set-Location -LiteralPath $ProjectDir
Stop-OldStreamlit

& $Python -m streamlit run app.py `
    --server.address 127.0.0.1 `
    --server.port $Port `
    --server.headless true `
    --browser.gatherUsageStats false
