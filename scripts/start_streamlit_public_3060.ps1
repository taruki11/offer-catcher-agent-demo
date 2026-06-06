# Start Offer Catcher Streamlit on the 3060 runtime and keep it alive.
# Usage on 3060:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_streamlit_public_3060.ps1

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$ProjectDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$Port = 8502
$HealthUrl = "http://127.0.0.1:$Port/_stcore/health"
$PythonCandidates = @(
    "D:\anaconda3\envs\pytorch123\python.exe",
    "D:\anaconda3\python.exe",
    "python"
)

function Stop-OldStreamlit {
    try {
        Get-CimInstance Win32_Process -Filter "name = 'python.exe' OR name = 'pythonw.exe'" |
            Where-Object { $_.CommandLine -like "*streamlit*" -and $_.CommandLine -like "*$Port*" } |
            ForEach-Object {
                Write-Output "Stopping old Streamlit PID=$($_.ProcessId)"
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
    } catch {
        Write-Output "WARN: cleanup skipped: $($_.Exception.Message)"
    }
}

function Select-Python {
    foreach ($Candidate in $PythonCandidates) {
        try {
            $probe = & $Candidate -c "import streamlit, sys; print(sys.executable); print(streamlit.__version__)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Python probe OK: $($probe -join ' | ')"
                return $Candidate
            }
        } catch {
        }
    }
    throw "No Python with streamlit found."
}

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}

Set-Location -LiteralPath $ProjectDir
Stop-OldStreamlit
Start-Sleep -Seconds 1

$Python = Select-Python
Write-Output "Selected Python: $Python"

$Args = @(
    "-m", "streamlit", "run", "app.py",
    "--server.address", "0.0.0.0",
    "--server.port", "$Port",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false"
)

$Proc = Start-Process $Python -ArgumentList $Args -WorkingDirectory $ProjectDir -WindowStyle Hidden -PassThru
Write-Output "Started Streamlit PID=$($Proc.Id)"

$Ok = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200 -and "$($resp.Content)".Trim() -eq "ok") {
            $Ok = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $Ok) {
    throw "Streamlit health check failed: $HealthUrl"
}

Write-Output "HEALTH_CHECK_OK $HealthUrl"
Write-Output "Listening:"
netstat -ano | findstr ":$Port"
Write-Output "Candidate URLs:"
Write-Output "  http://10.17.142.185:$Port"
Write-Output "  http://10.15.181.180:$Port"
Write-Output "  http://100.111.91.23:$Port"
