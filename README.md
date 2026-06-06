---
title: Offer Catcher Agent
emoji: 🎯
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# Offer 捕手：基于多 Agent 协作的大模型应用算法系统

**项目定位：规则精排 + 语义召回对照 + Eval/Error Analysis，不是普通聊天机器人。**

7 个 Agent 协作完成学生岗位匹配、简历优化与投递策略规划。

## 项目亮点

- **多 Agent 决策驾驶舱**：7 个 Agent 结构化协作，非单一 LLM 调用
- **可解释排序公式**：`ApplyPriority = 0.40*Match + 0.30*Pass - 0.15*Risk + 0.15*Growth`
- **语义召回对照面板**（新增）：规则精排 Top5 vs 语义召回 Top5 对比，展示交集与匹配原因
- **完整 Eval 框架**：Match/Priority/Action 三维评估 + Error Taxonomy (E1-E10)
- **LLM 可选增强**：无 API Key 时规则版完整运行，有 API 时自动增强。支持 DeepSeek / OpenAI / 通义 / 混元（API 增强层，非蒸馏）
- **数据透明度**：UI 展示岗位库规模、来源分布、方向覆盖、质量分
- **Corpus Eval**：大库下检索质量评估（TopK 方向/城市/阶段匹配率、重复率、来源集中度）

## 语义召回证据面板（新增）

Demo 中包含**语义召回对照**功能：
- 规则精排 Top5（ApplyPriority 排序结果）
- 语义召回 Top5（Embedding + FAISS 向量检索）
- 两个榜单的交集
- 为什么语义召回命中这个岗位（匹配原因说明）
- 当前使用模型、设备（CUDA/CPU）、语料库规模

**设计原则**：语义召回是**对照实验**，不影响主排序稳定性。规则排序公式仍是主要决策依据。

## 当前 Eval 指标

| 指标 | 值 |
|------|-----|
| Core Eval (8 cases) | **8/8 PASS (100%)** |
| Stress Eval (7 cases) | **7/7 PASS (100%)** |
| Match Top1 Acc | **100%** |
| Priority Top1 Acc | **85.7%** |
| Action Acc | **87.5%** |
| Recall@5 | **100%** |
| Corpus Eval (7 queries) | Top1 方向命中 >= 71%, 空字段=0 |

## LLM API 配置（可选增强层）

```bash
# 复制 .env.example 为 .env，填入 API Key
cp .env.example .env

# 本地调试可用环境变量；公网部署请在 Hugging Face Space Secrets 中配置：
LLM_PROVIDER=deepseek
LLM_API_KEY=<set-in-space-secrets>
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 也可切换 OpenAI / 通义 / 混元（详见 .env.example）
```

API 是增强层，不是必须。无 Key 时规则 fallback 仍可完整运行。

```bash
# 验证 LLM API 连接
python scripts/smoke_llm_api.py
```

## 运行方式

### 本地
```bash
# 安装依赖
pip install streamlit python-dotenv

# 启动 Demo
streamlit run app.py

# 运行 Eval
python scripts/run_eval.py
```

### 3060 远程部署
```bash
# 同步到 3060
scp -r app.py data src eval scripts reports docs 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/

# 3060 上启动
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
streamlit run app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true

# 3060 上运行 Eval
python scripts/run_eval.py
```

## 数据层

- **岗位库规模**：`data/jobs_corpus.json` 当前 **500 条**（v2 扩充后）
- **来源分布**：
  - `huggingface`：约 452 条（Sundaydream/tech-jobs-dataset-2026 约 296 条，batuhanmtl/job-skill-set 约 145 条，arjun10g/na-tech-jobs 约 11 条）
  - `curated_seed`：48 条（离线覆盖库，**不冒充真实爬取 JD**，仅用于方向补全）
- **统一 schema**：`title / company / city / direction / stage / skills / jd / source / data_quality_score`
- **Corpus Eval**：`scripts/eval_corpus_quality.py` 用 7 个代表性 query 评估大库检索质量（Top1 方向命中、Top5 召回、来源多样性、空字段率）

```
app.py                        # Streamlit 主入口
src/matcher.py                # 匹配排序（可解释公式）
src/strategy_planner.py       # 策略规划
src/evidence.py               # Evidence Chain
src/evaluator.py              # Eval 评估器
src/semantic_retriever.py     # 语义召回（Embedding + FAISS，可选）
src/jd_parser.py              # JD 解析
src/resume_parser.py          # 简历解析
src/llm_client.py             # LLM 客户端（可选增强）
src/conversion.py             # 转化概率模型
scripts/run_eval.py            # Eval 入口
scripts/build_job_corpus.py    # 岗位库构建（支持 HF 公开数据）
scripts/analyze_job_corpus.py # 岗位库质量分析
scripts/eval_corpus_quality.py # Corpus-level Eval
eval/golden_cases.json        # golden cases (8个)
data/jobs.json                # 内置岗位库（20条，golden 覆盖）
data/jobs_corpus.json         # 扩展岗位库（500条，HF+curated）
data/jobs_merged.json         # 合并岗位库（500条）
data/job_corpus_stats.json    # 岗位库统计
reports/                      # 自动生成的报告
docs/                         # 方案说明、演示脚本
```
