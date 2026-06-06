# 在 3060 上后台启动 Streamlit
$logPath = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602\streamlit.log"
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "D:\anaconda3\envs\pytorch123\python.exe"
$psi.Arguments = "-m streamlit run app.py --server.address 0.0.0.0 --server.port 8502 --server.headless true"
$psi.WorkingDirectory = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

$process = [System.Diagnostics.Process]::Start($psi)
Write-Output "Streamlit started with PID: $($process.Id)"
Write-Output "Log file: $logPath"
Start-Sleep -Seconds 5
Get-Content $logPath -Tail 20
