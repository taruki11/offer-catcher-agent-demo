# 启动 Streamlit（后台 Job）
$jobName = "Streamlit3060"

# 如果已有同名 Job，先删掉
Get-Job -Name $jobName -ErrorAction SilentlyContinue | Remove-Job -Force

# 启动后台 Job
$job = Start-Job -Name $jobName -ScriptBlock {
    Set-Location "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
    $python = "D:\anaconda3\envs\pytorch123\python.exe"
    & $python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502 --server.headless true 2>&1 | Out-File "streamlit.log" -Encoding utf8
}

Start-Sleep -Seconds 6

# 检查 Job 状态
$jobStatus = Get-Job -Name $jobName
Write-Output "Job State: $($jobStatus.State)"
Write-Output "Job ID: $($jobStatus.Id)"

# 检查端口
$tcp = Test-NetConnection -ComputerName localhost -Port 8502 -InformationLevel Quiet -ErrorAction SilentlyContinue
Write-Output "Port 8502 listening: $tcp"

# 读取最新日志
if (Test-Path "streamlit.log") {
    Get-Content "streamlit.log" -Tail 20
}
