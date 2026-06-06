# 数据导入运行记录

Generated: 2026-06-05

## 网络状态

[FAIL] Hugging Face 网络连接超时

```
Command: python -c "import urllib.request; ..."
Error: urllib.error.URLError: <urlopen error timed out>
```

**结论**: 当前网络环境无法访问 Hugging Face datasets-server API。

---

## 影响范围

- `scripts/build_job_corpus.py --try-hf` 无法拉取公开数据
- 无法完成"把岗位库从 240 条推进到 500 条（真实公开数据占比更高）"的目标

---

## 切换策略

按用户指令：**不要卡住，记录失败原因，然后继续做本地数据质量分析。**

### 立即执行：

1. ✅ 创建 `scripts/analyze_job_corpus.py` - 本地数据质量分析脚本
2. ✅ 运行 `python scripts/build_job_corpus.py --target-size 240` - 确保当前 240 条数据质量
3. ✅ 运行 `python scripts/analyze_job_corpus.py` - 生成数据质量报告
4. ✅ 验证 `jobs_corpus.json >= 240` 且 `empty_skills = 0`

### 后续本地任务（P2-P5）：

5. P2: UI 数据可信度展示
6. P3: Corpus Eval 脚本
7. P4: 文档和参赛材料升级
8. P5: 3060 恢复后的同步准备

---

## 网络恢复后手动执行

```powershell
# 拉取真实公开数据
python scripts\build_job_corpus.py --target-size 500 --try-hf --hf-limit-per-source 300

# 重新分析扩大后的语料库
python scripts\analyze_job_corpus.py
```

---

## 当前数据状态

```
data/jobs_corpus.json: 240 条
data/jobs_merged.json: 240 条
data/job_corpus_stats.json: 已生成

来源分布:
  - curated_seed:v1: 192 条 (80%)
  - unknown (内置): 20 条 (8.3%)
  - fixture: 16 条 (6.7%)
  - greenhouse: 5 条 (2.1%)
  - lever: 5 条 (2.1%)
  - ashby: 2 条 (0.8%)
```

**注意**: curated_seed 是离线覆盖库，不能冒充真实爬取数据。

---

## 下次运行建议

网络恢复后，优先运行：

```powershell
# 1. 拉取真实数据
python scripts\build_job_corpus.py --target-size 500 --try-hf --hf-limit-per-source 300

# 2. 验证数据质量
python scripts\analyze_job_corpus.py

# 3. 确认 empty_skills = 0
python -c "import json; jobs=json.load(open('data/jobs_corpus.json', encoding='utf-8')); empty=[j for j in jobs if not j.get('skills')]; print(f'empty_skills: {len(empty)}')"

# 4. 运行完整测试套件
python scripts\run_eval.py --split core
python scripts\run_eval.py --split stress
```
