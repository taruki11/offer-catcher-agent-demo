# Offer 捕手 - 访问指南

## 🌐 访问地址

### 3060 机器上运行：
```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
conda activate pytorch123
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

### 访问地址（在 3060 本机）：
- http://localhost:8502
- http://127.0.0.1:8502

### 访问地址（从其他机器）：
- http://100.111.91.23:8502
- http://10.17.142.185:8502
- http://10.15.181.180:8502

## 🔍 排查步骤

### 1. 检查 Streamlit 是否启动
在 3060 上运行：
```powershell
Get-Process -Name python | Where-Object {$_.CommandLine -like '*streamlit*'}
```

### 2. 检查端口是否监听
在 3060 上运行：
```powershell
netstat -ano | findstr :8502
```

### 3. 检查防火墙
在 3060 上运行：
```powershell
Get-NetFirewallRule -DisplayName '*Streamlit*' | Select-Object DisplayName, Enabled, Direction, Action
```

### 4. 手动启动 Streamlit（前台运行，看日志）
在 3060 上运行：
```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
conda activate pytorch123
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```
**注意**：这个命令会阻塞，Streamlit 在前台运行。如果有错误，会直接显示在终端上。

## 📋 当前状态

- **Streamlit 版本**：1.50.0
- **Python 环境**：D:\anaconda3\envs\pytorch123\python.exe
- **工作目录**：D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
- **防火墙规则**：已添加（Streamlit 8502，Inbound，TCP，Allow）

## 🚨 可能的问题

1. **Streamlit 没成功启动** —— 端口没监听
2. **防火墙没放行** —— 虽然加了规则，但可能没生效
3. **--server.address 没生效** —— Streamlit 只监听了 localhost
4. **端口被占用** —— 8502 可能被其他进程占用

## 💡 建议

**最可靠的方式**：请在 3060 上**手动运行**以下命令，然后把输出发给我：

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
conda activate pytorch123
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

这样你就能看到 Streamlit 的启动日志，如果有错误也能看到。
