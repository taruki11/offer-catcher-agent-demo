# 公网部署脚本（在 3060 上本地执行）

## 方案 A：Cloudflare Tunnel（推荐，免费、无需账号）

### 步骤 1：下载 cloudflared

打开 3060 上的 PowerShell，执行：

```powershell
$url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$out = "$env:USERPROFILE\cloudflared.exe"
Invoke-WebRequest -Uri $url -OutFile $out -ErrorAction Stop
Write-Host "[OK] cloudflared 下载完成：$out"
```

如果 GitHub 下载慢，用国内镜像：

```powershell
$url = "https://ghproxy.com/https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$out = "$env:USERPROFILE\cloudflared.exe"
Invoke-WebRequest -Uri $url -OutFile $out -ErrorAction Stop
```

### 步骤 2：启动 Streamlit

在 **新的** PowerShell 窗口中执行：

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

等待看到 `Local URL: http://localhost:8501` 表示启动成功。

### 步骤 3：启动 Cloudflare Tunnel

在 **另一个** PowerShell 窗口中执行：

```powershell
& "$env:USERPROFILE\cloudflared.exe" tunnel --url http://localhost:8501
```

等待看到类似输出：

```
Your quick Tunnel has been created! Visit it at:
https://xxxx-xxxx-xxxx.trycloudflare.com
```

这个 `https://xxxx-xxxx-xxxx.trycloudflare.com` URL 就是公网访问地址。

---

## 方案 B：ngrok（需要注册账号获取 authtoken）

### 步骤 1：下载 ngrok

```powershell
$url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
$out = "$env:USERPROFILE\ngrok.zip"
Invoke-WebRequest -Uri $url -OutFile $out
Expand-Archive -Path $out -DestinationPath "$env:USERPROFILE\ngrok" -Force
Write-Host "[OK] ngrok 解压完成"
```

### 步骤 2：配置 authtoken

去 https://dashboard.ngrok.com/get-started/your-authtoken 获取 authtoken，然后执行：

```powershell
& "$env:USERPROFILE\ngrok\ngrok.exe" config add-authtoken <YOUR_AUTHTOKEN>
```

### 步骤 3：启动 Streamlit + ngrok

窗口 1（启动 Streamlit）：

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

窗口 2（启动 ngrok）：

```powershell
& "$env:USERPROFILE\ngrok\ngrok.exe" http 8501
```

等待看到 `Forwarding  https://xxxx.ngrok-free.app -> http://localhost:8501`

---

## 方案 C：3060 直接开端口（如果 3060 有公网 IP 或校园网可直接访问）

### 步骤 1：检查 3060 是否已有公网可访问 IP

让同一校园网内的其他电脑访问：

```
http://10.17.142.185:8501
```

或

```
http://10.15.181.180:8501
```

如果能访问，直接用这个地址。

### 步骤 2：启动 Streamlit（绑定到 0.0.0.0）

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 推荐顺序

1. **Cloudflare Tunnel**（最快，不需要账号，免费）
2. **直接开端口**（如果校园网允许）
3. **ngrok**（需要注册，但最稳定）

## 验证部署成功

部署后，用手机（切换 4G/5G，不在校园网内）访问公网 URL，应该能看到 Offer 捕手 Streamlit 界面。
