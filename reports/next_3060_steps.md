# 3060 同步准备步骤

Generated: 2026-06-05
Updated: 2026-06-05

## 当前本地状态

```
核心指标：
  - core eval: 8/8 [PASS]
  - stress eval: 7/7 [PASS]
  - JD intake: PASS [PASS]
  - LLM fallback: PASS [PASS]
  - Evidence: 6/6 [PASS]
  - Data ingestion: PASS [PASS]
  - Deploy ready: 13/13 [PASS]

数据规模：
  - data/jobs_corpus.json: 240 条 [PASS]
  - data/jobs_merged.json: 240 条 [PASS]
  - empty_skills: 0 [PASS]
  - empty_jd: 0 [PASS]

新增文件：
  - scripts/analyze_job_corpus.py [PASS]
  - scripts/eval_corpus_quality.py [PASS]
  - reports/job_corpus_analysis.md [PASS]
  - reports/corpus_eval_report.md [PASS]
  - reports/data_ingestion_run.md [PASS]

修改文件：
  - app.py (P2: 数据透明度展示) [PASS]
  - docs/岗位数据层升级说明.md (P1/P4) [PASS]
  - docs/方案说明_提交版.md (P4) [PASS]
  - docs/演示脚本.md (P4) [PASS]
  - README.md (P4) [PASS]
```

---

## 3060 恢复后执行步骤

### 1. 同步代码到 3060

```powershell
# 本地执行（在本地中文目录运行）
scp -r app.py check_health.ps1 requirements.txt .env.example README.md data docs prompts src eval scripts reports 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/
```

**说明**：
- 目标目录：`D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/`（英文目录）
- 不要覆盖中文目录（用户明确禁止编辑英文目录）

---

### 2. 3060 上验证

```powershell
# SSH 到 3060 后执行
ssh 3060 "powershell -NoProfile -ExecutionPolicy Bypass -File D:\Pycharm_workplace\offer_catcher_agent_demo_20260602\scripts\verify_3060.ps1"
```

**如果 `verify_3060.ps1` 不存在**，手动运行：

```powershell
# 3060 上手动验证
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602

# 1. 语法检查
python -m py_compile app.py src/*.py scripts/*.py

# 2. Core eval
python scripts\run_eval.py --split core

# 3. Stress eval
python scripts\run_eval.py --split stress

# 4. 其他测试
python scripts\test_jd_intake.py
python scripts\test_llm_fallback.py
python scripts\test_evidence.py
python scripts\test_data_ingestion.py
python scripts\check_deploy_ready.py

# 5. 启动 Streamlit（测试部署）
streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true
```

---

### 3. 公网部署（可选）

```powershell
# 3060 上执行
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602

# 启动公网可访问的 Streamlit
streamlit run app.py --server.address 0.0.0.0 --server.port 8502

# 如果有公网 IP，配置防火墙放行 8502 端口
# 否则使用 ngrok：
ngrok http 8502
```

---

### 4. 网络恢复后数据扩容（可选）

```powershell
# 本地执行（网络恢复后）
cd "D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统"

# 拉取真实公开数据
python scripts\build_job_corpus.py --target-size 500 --try-hf --hf-limit-per-source 300

# 重新分析扩大后的语料库
python scripts\analyze_job_corpus.py

# 验证 empty_skills = 0
python -c "import json; jobs=json.load(open('data/jobs_corpus.json', encoding='utf-8')); empty=[j for j in jobs if not j.get('skills')]; print(f'empty_skills: {len(empty)}')"

# 同步扩大后的数据到 3060
scp data/jobs_corpus.json data/jobs_merged.json data/job_corpus_stats.json 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/data/
```

---

## 验证清单

3060 恢复后，确认以下各项：

- [ ] `python scripts\run_eval.py --split core` → 8/8 PASS
- [ ] `python scripts\run_eval.py --split stress` → 7/7 PASS
- [ ] `python scripts\test_jd_intake.py` → PASS
- [ ] `python scripts\test_llm_fallback.py` → PASS
- [ ] `python scripts\test_evidence.py` → 6/6 PASS
- [ ] `python scripts\test_data_ingestion.py` → PASS
- [ ] `python scripts\check_deploy_ready.py` → 13/13 PASS
- [ ] Streamlit 启动成功（`http://3060-ip:8502` 可访问）
- [ ] 数据透明度展示正常显示（侧边栏折叠区）

---

## 回滚计划

如果 3060 上测试失败：

```powershell
# 1. 回滚到上一个稳定版本
ssh 3060 "cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602 && git checkout app.py src/ scripts/"

# 2. 或者使用本地稳定版本重新同步
scp -r app.py src/ scripts/ 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/
```

---

## 联系信息

- 本地项目路径：`D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统`
- 3060 项目路径：`D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/`
- 网络恢复检测：`python -c "import urllib.request; urllib.request.urlopen('https://huggingface.co', timeout=10)"`

---

**最后更新**: 2026-06-05
**状态**: 等待 3060 网络恢复
