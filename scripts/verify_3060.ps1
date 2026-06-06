# Strict 3060 verification for Offer Catcher.
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify_3060.ps1

$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$ProjectDir = "D:\Pycharm_workplace\offer_catcher_agent_demo_20260602"
$SemanticPython = "D:\anaconda3\envs\pytorch123\python.exe"

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

if (-not (Test-Path -LiteralPath $ProjectDir)) {
    throw "Project directory not found: $ProjectDir"
}

Set-Location -LiteralPath $ProjectDir

Write-Output "=== 1. py_compile ==="
Invoke-Checked python -m py_compile `
    app.py `
    src\evidence.py `
    src\matcher.py `
    src\jd_parser.py `
    src\job_intake.py `
    src\llm_client.py `
    src\resume_parser.py `
    src\conversion.py `
    src\strategy_planner.py `
    src\eval_schema.py `
    src\evaluator.py `
    src\public_job_ingestion.py `
    src\semantic_retriever.py `
    scripts\test_evidence.py `
    scripts\test_jd_intake.py `
    scripts\test_llm_fallback.py `
    scripts\test_semantic_retriever.py `
    scripts\test_data_ingestion.py `
    scripts\import_public_jobs.py `
    scripts\build_job_corpus.py `
    scripts\analyze_job_corpus.py `
    scripts\eval_corpus_quality.py `
    scripts\check_remote_data.py `
    scripts\check_deploy_ready.py `
    scripts\run_eval.py

Write-Output "=== 2. evidence tests ==="
Invoke-Checked python scripts\test_evidence.py

Write-Output "=== 3. JD intake tests ==="
Invoke-Checked python scripts\test_jd_intake.py

Write-Output "=== 4. LLM fallback tests ==="
Invoke-Checked python scripts\test_llm_fallback.py

Write-Output "=== 5. deploy-ready checks ==="
Invoke-Checked python scripts\check_deploy_ready.py

Write-Output "=== 6. data ingestion tests ==="
Invoke-Checked python scripts\test_data_ingestion.py

# import_public_jobs.py is intentionally not run here because it can overwrite
# data/jobs_merged.json when explicitly requested.

Write-Output "=== 7. check remote data scale ==="
Invoke-Checked python scripts\check_remote_data.py

Write-Output "=== 8. core eval ==="
Invoke-Checked python scripts\run_eval.py --split core

Write-Output "=== 9. stress eval ==="
Invoke-Checked python scripts\run_eval.py --split stress

Write-Output "=== 10. corpus analysis ==="
Invoke-Checked python scripts\analyze_job_corpus.py

Write-Output "=== 11. corpus eval ==="
Invoke-Checked python scripts\eval_corpus_quality.py

Write-Output "=== 12. semantic retriever smoke (pytorch123) ==="
if (-not (Test-Path -LiteralPath $SemanticPython)) {
    throw "pytorch123 python not found: $SemanticPython"
}
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
Invoke-Checked $SemanticPython scripts\test_semantic_retriever.py

Write-Output "=== 13. Streamlit health check ==="
Invoke-Checked powershell -NoProfile -ExecutionPolicy Bypass -File .\check_health.ps1

Write-Output "=== 14. FINAL: verify data scale (MUST BE >= 500) ==="
Invoke-Checked python scripts\check_remote_data.py

Write-Output "VERIFY_3060_OK"
