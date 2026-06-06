# Deploy Offer Catcher to a Hugging Face Docker Space.
#
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\deploy_hf_space.ps1 -SpaceId "YOUR_NAME/offer-catcher-agent"
#
# Before running:
#   hf auth login

param(
    [Parameter(Mandatory = $true)]
    [string]$SpaceId
)

$ErrorActionPreference = "Stop"
$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

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

Set-Location -LiteralPath $ProjectDir

Write-Output "=== 1. Check hf login ==="
Invoke-Checked hf auth whoami

Write-Output "=== 2. Local sanity checks ==="
Invoke-Checked python -m py_compile app.py src\llm_client.py src\embedding_client.py src\semantic_retriever.py src\matcher.py
Invoke-Checked python scripts\run_eval.py --split core

Write-Output "=== 3. Create or reuse Docker Space ==="
Invoke-Checked hf repo create $SpaceId --repo-type space --space_sdk docker --exist-ok

Write-Output "=== 4. Build clean staging directory ==="
$StageDir = Join-Path $env:TEMP "offer_catcher_hf_space_clean"
if (Test-Path -LiteralPath $StageDir) {
    Remove-Item -LiteralPath $StageDir -Recurse -Force
}
New-Item -ItemType Directory -Path $StageDir | Out-Null

$Dirs = @("src", "data", "prompts", "eval", "reports")
foreach ($Dir in $Dirs) {
    Copy-Item -LiteralPath (Join-Path $ProjectDir $Dir) -Destination (Join-Path $StageDir $Dir) -Recurse
}

$DocsStage = Join-Path $StageDir "docs"
New-Item -ItemType Directory -Path $DocsStage | Out-Null
$Docs = @(
    "docs\方案说明_提交版.md",
    "docs\演示脚本.md",
    "docs\演示视频分镜.md",
    "docs\比赛提交公网部署步骤.md",
    "docs\公网部署_HuggingFace_DockerSpace.md",
    "docs\模型路线说明.md",
    "docs\AI工具选型与数据策略.md"
)
foreach ($Doc in $Docs) {
    $Src = Join-Path $ProjectDir $Doc
    if (Test-Path -LiteralPath $Src) {
        Copy-Item -LiteralPath $Src -Destination $DocsStage
    }
}

$Files = @("Dockerfile", "requirements-public.txt", "requirements.txt", "README.md", "app.py", ".dockerignore")
foreach ($File in $Files) {
    Copy-Item -LiteralPath (Join-Path $ProjectDir $File) -Destination (Join-Path $StageDir $File)
}

Write-Output "=== 5. Upload clean project files ==="
Invoke-Checked hf upload $SpaceId $StageDir . `
    --repo-type space `
    --commit-message "Deploy Offer Catcher Agent demo" `
    --delete "*"

Write-Output "=== 6. Done ==="
Write-Output "Space page: https://huggingface.co/spaces/$SpaceId"
$DirectId = $SpaceId.Replace("/", "-")
Write-Output "Direct app URL is usually: https://$DirectId.hf.space"
Write-Output "Wait for the Space build to finish, then test the direct app URL."
