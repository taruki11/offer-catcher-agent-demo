# 在 3060 上后台启动 Streamlit（无窗口）
$python = "D:\anaconda3\envs\pytorch123\pythonw.exe"
if (-not (Test-Path $python)) {
    $python = "D:\anaconda3\envs\pytorch123\python.exe"
}

$workingDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$arguments = "-m streamlit run app.py --server.address 0.0.0.0 --server.port 8502 --server.headless true"

# 启动进程（无窗口）
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $python
$psi.Arguments = $arguments
$psi.WorkingDirectory = $workingDir
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true

try {
    $process = [System.Diagnostics.Process]::Start($psi)
    Write-Output "Streamlit started with PID: $($process.Id)"
    Write-Output "Python: $python"
    Write-Output "Working Dir: $workingDir"
    
    # 等待 5 秒让服务启动
    Start-Sleep -Seconds 5
    
    # 检查端口是否监听
    $tcpTest = Test-NetConnection -ComputerName localhost -Port 8502 -InformationLevel Quiet -ErrorAction SilentlyContinue
    if ($tcpTest) {
        Write-Output "SUCCESS: Port 8502 is listening!"
    } else {
        Write-Output "WARNING: Port 8502 not yet listening, checking process..."
        $proc = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Output "Process is running: $($proc.Name) (PID: $($proc.Id))"
        } else {
            Write-Output "Process may have died, checking recent logs..."
        }
    }
} catch {
    Write-Output "ERROR: $_"
}
