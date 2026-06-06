# 在 3060 上启动 Streamlit（前台运行，方便看日志）
Write-Output "=== 启动 Streamlit ==="
Write-Output "Python: D:\anaconda3\envs\pytorch123\python.exe"
Write-Output "工作目录: D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
Write-Output ""

# 切换到工作目录并启动
Set-Location "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
& "D:\anaconda3\envs\pytorch123\python.exe" -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502 --server.headless true
