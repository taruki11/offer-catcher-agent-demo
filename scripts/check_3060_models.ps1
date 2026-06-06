# check_models.ps1 - 探测 3060 本地大模型
Write-Host "=== Checking D:\models ===" -ForegroundColor Cyan
Get-ChildItem D:\models -Directory -ErrorAction SilentlyContinue | Select-Object Name, FullName | Format-Table -AutoSize

Write-Host "=== Checking D:\hf_models ===" -ForegroundColor Cyan
Get-ChildItem D:\hf_models -Directory -ErrorAction SilentlyContinue | Select-Object -First 20 Name, FullName | Format-Table -AutoSize

Write-Host "=== Checking D:\LLM ===" -ForegroundColor Cyan
Get-ChildItem D:\LLM -Directory -ErrorAction SilentlyContinue | Select-Object Name, FullName | Format-Table -AutoSize

Write-Host "=== Checking HuggingFace cache ===" -ForegroundColor Cyan
Get-ChildItem "C:\Users\29451\.cache\huggingface\hub" -Directory -ErrorAction SilentlyContinue | Select-Object -First 20 Name | Format-Table -AutoSize

Write-Host "=== Checking running processes (port 11434 Ollama?) ===" -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 11434 -ErrorAction SilentlyContinue | Select-Object LocalPort, State

Write-Host "=== Checking port 8000 (vLLM?) ===" -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object LocalPort, State

Write-Host "=== DONE ===" -ForegroundColor Green
