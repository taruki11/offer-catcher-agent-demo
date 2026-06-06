# WorkBuddy 70% 数据扩容任务表

把这张表和 `WORKBUDDY_OFFER_CATCHER_SKILL.md` 一起发给 WorkBuddy。要求它按行执行，不要跳步，不要中途问“是否继续”。

## 总目标

把 Offer 捕手从 20 条内置样例岗位，升级为“有公开岗位库接入层的小型可扩展系统”。本轮只做 70%：离线 fixture + 标准化 + 合并 + App 选择 + 本地/3060 验证。

不做：

- 大规模爬虫。
- Boss/智联/牛客爬取。
- 本地大模型强接入。
- 大文件下载。
- stress 策略大调参。

## 执行表

| 步骤 | 目标 | 输入 | 输出文件 | 验证命令 | 完成标准 | 失败 fallback |
|---|---|---|---|---|---|---|
| 1 | 确认工作区 | 当前目录 | 无 | `Get-Location`; `rg --files` | 位于本地中文目录 | 若不在中文目录，切换到正确目录 |
| 2 | 修复遗留诊断脚本 | `scripts/diag_stress.py`, `scripts/diag_stress_v2.py` | 修改这两个脚本 | `python scripts\diag_stress.py`; `python scripts\diag_stress_v2.py` | 两个脚本不报错 | 如果脚本价值低，改成读取 evaluator trace 的简单诊断脚本 |
| 3 | 新建公开岗位接入模块 | 无 | `src/public_job_ingestion.py` | `python -m py_compile src\public_job_ingestion.py` | 模块语法通过 | 先只支持 fixture，不接 HF |
| 4 | 实现标准化函数 | raw job dict | `src/public_job_ingestion.py` | `python scripts\test_data_ingestion.py` | title/company/jd/skills/direction/stage/source 字段齐全 | 缺字段用默认值，但 quality_score 降低 |
| 5 | 实现技能抽取 | title + jd | `src/public_job_ingestion.py` | `python scripts\test_data_ingestion.py` | LLM/RAG/Agent/推荐/后端/数据分析等技能可抽出 | 使用关键词规则，不调用 API |
| 6 | 实现方向推断 | title + jd + skills | `src/public_job_ingestion.py` | `python scripts\test_data_ingestion.py` | 可推断 大模型应用算法/推荐算法/后端研发/数据分析/产品经理 | 无法推断则 `其他技术岗` |
| 7 | 实现去重 | builtin + public jobs | `src/public_job_ingestion.py` | `python scripts\test_data_ingestion.py` | title+company+city/source_url 去重 | 没 url 时用 title+company+city |
| 8 | 新建离线测试脚本 | fixture raw jobs | `scripts/test_data_ingestion.py` | `python scripts\test_data_ingestion.py` | 至少 8 条 fixture，测试通过 | fixture 写在脚本内部，避免外部依赖 |
| 9 | 新建导入脚本 | fixture / jsonl / csv | `scripts/import_public_jobs.py` | `python scripts\import_public_jobs.py --from-fixture --limit 100` | 生成 public/merged 数据文件 | 如果 CSV/HF 来不及，先 fixture 完整跑通 |
| 10 | 生成公开岗位样本 | fixture | `data/public_jobs_sample.json` | `python -c "import json; print(len(json.load(open('data/public_jobs_sample.json',encoding='utf-8'))))"` | 50-100 条即可，不超过 300 | fixture 不足则复制模板变体，但 source_url/id 要不同 |
| 11 | 生成合并岗位库 | `data/jobs.json` + public sample | `data/jobs_merged.json` | 同上 | merged 数量 > builtin 数量 | 若重复过多，检查去重 key |
| 12 | App 增加岗位来源 | `app.py` | 修改 app.py | `python -m py_compile app.py` | UI 有 公开岗位库 / 内置+公开 | 文件不存在时 warning 不崩溃 |
| 13 | Matcher 兼容大岗位库 | `matcher.py` / app 数据加载 | 可能修改 app.py | `python scripts\run_eval.py --split core` | core 仍 8/8 | 不改 matcher，只在 app 侧传 jobs list |
| 14 | 文档说明 | 无 | `docs/数据扩容与公开岗位库说明.md` | 文件存在且说明完整 | 写清数据来源、schema、清洗、合规 | 简短也可以，先覆盖关键点 |
| 15 | 本地完整验证 | 全项目 | 无 | 见下方命令块 | 全部通过 | 失败则修复后重跑 |
| 16 | 更新 3060 验证脚本 | `scripts/verify_3060.ps1` | 修改脚本 | 本地读文件确认包含 `test_data_ingestion.py` | 远程会跑数据接入测试 | 若脚本过长，至少加 test + import |
| 17 | 同步 3060 | 本地项目 | 远程目录 | `scp -r ...` | 无报错 | scp 失败重试一次 |
| 18 | 3060 验证 | 远程目录 | reports | `ssh 3060 "powershell ... verify_3060.ps1"` | `VERIFY_3060_OK`, health 200 ok | 若 health 失败，跑 `check_health.ps1` 单独定位 |
| 19 | 最终汇报 | 验证日志 | 无 | 无 | 按固定格式汇报 | 不要问是否继续 |

## 本地验证命令

```powershell
$env:PYTHONIOENCODING="utf-8"
python -m py_compile app.py src\public_job_ingestion.py src\job_intake.py src\matcher.py src\evaluator.py src\eval_schema.py scripts\import_public_jobs.py scripts\test_data_ingestion.py scripts\run_eval.py scripts\check_deploy_ready.py
python scripts\test_data_ingestion.py
python scripts\import_public_jobs.py --from-fixture --limit 100
python scripts\run_eval.py --split core
python scripts\run_eval.py --split stress
python scripts\check_deploy_ready.py
```

## 同步 3060

```powershell
scp -r app.py check_health.ps1 requirements.txt .env.example README.md data docs prompts src eval scripts reports 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/
```

## 3060 验证

```powershell
ssh 3060 "powershell -NoProfile -ExecutionPolicy Bypass -File D:\Pycharm_workplace\offer_catcher_agent_demo_20260602\scripts\verify_3060.ps1"
```

## 汇报模板

```text
本轮目标：

修改文件：

新增数据：
- public_jobs_sample.json: X 条
- jobs_merged.json: Y 条

本地验证：
- py_compile: PASS/FAIL
- test_data_ingestion: PASS/FAIL
- import_public_jobs: PASS/FAIL
- core eval: X/8
- stress eval: X/7
- check_deploy_ready: PASS/FAIL

3060 验证：
- verify_3060.ps1: PASS/FAIL
- Streamlit health: 200 ok / fail

剩余问题：

下一步建议：
```

