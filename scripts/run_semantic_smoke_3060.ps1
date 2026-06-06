# Strict semantic retriever smoke test for the 3060 runtime.
# Uses pytorch123 so FAISS + sentence-transformers + CUDA are aligned.

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

$ProjectDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$Python = "D:\anaconda3\envs\pytorch123\python.exe"

Write-Output "=== 3060 semantic retriever smoke ==="
Write-Output "ProjectDir: $ProjectDir"
Write-Output "Python: $Python"

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}
if (-not (Test-Path -LiteralPath $Python)) {
    throw "pytorch123 python not found: $Python"
}

Set-Location -LiteralPath $ProjectDir

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Args
    )
    & $Exe @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Exe $($Args -join ' ')"
    }
}

Write-Output "=== 1. env check ==="
Invoke-Checked $Python -c "import torch, sentence_transformers, faiss, numpy; print('torch', torch.__version__); print('cuda', torch.cuda.is_available()); print('faiss ok')"

Write-Output "=== 2. corpus size check ==="
Invoke-Checked $Python -c "import json; from pathlib import Path; p=Path('data/jobs_corpus.json'); q=Path('data/jobs_merged.json'); n=len(json.loads(p.read_text(encoding='utf-8'))); m=len(json.loads(q.read_text(encoding='utf-8'))); print('jobs_corpus', n); print('jobs_merged', m); assert n>=500 and m>=500"

Write-Output "=== 3. py_compile semantic files ==="
Invoke-Checked $Python -m py_compile src\semantic_retriever.py scripts\test_semantic_retriever.py

Write-Output "=== 4. strict semantic smoke ==="
Invoke-Checked $Python scripts\test_semantic_retriever.py

Write-Output "=== 5. no-regression eval ==="
Invoke-Checked $Python scripts\run_eval.py --split core
Invoke-Checked $Python scripts\run_eval.py --split stress

Write-Output "SEMANTIC_SMOKE_3060_OK"
