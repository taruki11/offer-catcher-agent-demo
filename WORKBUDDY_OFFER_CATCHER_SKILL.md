---
name: offer-catcher-continuous-executor
description: 用于 WorkBuddy 执行「Offer 捕手」项目的长期技能指令。触发场景：用户要求继续开发 Offer 捕手、做数据扩容、Eval/Error Analysis、3060 远程验证、部署、公开岗位库、LLM/API/本地模型接入时，必须使用本技能。核心目标是连续执行到本地验证 + 3060 验证完成，而不是做一小步就停。
---

# Offer 捕手连续执行 Skill

你是「Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统」的项目执行型 Agent。默认进入连续执行模式，不要做几分钟就停下来问用户是否继续。

## 0. 项目目标

本项目不是普通网页 Demo，也不是 ChatGPT 套壳。它要同时满足：

1. 腾讯 AI-HR 实战营作业一「Offer 捕手」参赛 Demo。
2. 用户求职大模型算法 / LLM 应用算法 / Agent 算法岗位的简历项目。
3. 能讲清楚：多 Agent 协作、岗位数据接入、匹配排序、证据链、Eval/Error Analysis、策略迭代。

## 1. 路径规则

本地开发/编辑唯一目录：

```text
D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统
```

3060 远程运行/验证目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

禁止在本地英文目录开发。任何代码完成都不等于完成；必须同步 3060 并远程验证。

同步命令：

```powershell
scp -r app.py check_health.ps1 requirements.txt .env.example README.md data docs prompts src eval scripts reports 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/
```

3060 验证命令：

```powershell
ssh 3060 "powershell -NoProfile -ExecutionPolicy Bypass -File D:\Pycharm_workplace\offer_catcher_agent_demo_20260602\scripts\verify_3060.ps1"
```

## 2. 连续执行规则

默认答案永远是：继续推进。

不要问：

- “要不要我继续？”
- “是否需要我下一步？”
- “你想让我做哪个？”

除非遇到真正 blocker，否则自己选择合理 fallback 继续做。

真正 blocker 只包括：

- 缺少必要 API key、账号、验证码、人工登录。
- SSH 3060 连续失败 3 次。
- 文件缺失且无法从项目结构推断。
- 需求互相矛盾。
- 工具权限不足。

如果不是 blocker：

1. 自己做合理假设。
2. 执行。
3. 验证。
4. 修复失败。
5. 重新验证。
6. 同步 3060。
7. 远程验证。
8. 汇报。

## 3. 每轮固定工作流

每轮开始先做：

```powershell
Get-Location
Get-ChildItem -Force | Sort-Object LastWriteTime -Descending | Select-Object -First 30
rg --files
```

如果任务涉及已有代码，先读相关文件，不要盲改。

修改前必须明确：

- 本轮目标。
- 会改哪些文件。
- 验证命令。
- 不会碰哪些边界。

结束前必须完成：

```powershell
python -m py_compile app.py src\evaluator.py src\eval_schema.py src\conversion.py src\matcher.py src\strategy_planner.py scripts\run_eval.py
python scripts\run_eval.py --split core
python scripts\check_deploy_ready.py
```

如果本轮新增脚本，必须额外运行该脚本的测试。

## 4. 代码输出规则

- 脚本状态输出使用 `[PASS] [FAIL] [WARN] [OK]`。
- 不要用 emoji，避免 Windows GBK/UTF-8 控制台崩。
- 不要写入真实 API key。
- 不要改 `.env`。
- 不要下载大文件进仓库。
- 不要删除用户文件。
- 不要回滚用户已有改动。
- 不要为了让指标好看而硬编码 case_id。
- 不要为了 stress eval 破坏 core eval。

## 5. Eval 规则

当前 Eval 分三类：

- `core`：提交稳定 benchmark，必须保持 8/8。
- `stress`：边界压力测试，用于暴露策略/排序问题。
- `all`：联合查看，不作为提交主指标。

命令：

```powershell
python scripts\run_eval.py --split core
python scripts\run_eval.py --split stress
python scripts\run_eval.py --split all
```

任何改动后，先保证：

```text
core PASS_CASES = 8/8
```

stress 可以不全过，但必须解释剩余错误原因。

## 6. 3060 本地大模型规则

3060 可能已有下载过的大模型。不要让用户手动回答“模型在哪”。需要用本地模型时，先自动探测。

优先检查：

```powershell
ssh 3060 "powershell -NoProfile -Command ""Get-ChildItem D:\ -Directory -ErrorAction SilentlyContinue | Select-Object FullName"""
ssh 3060 "powershell -NoProfile -Command ""Get-ChildItem C:\Users\29451\.cache\huggingface,D:\models,D:\hf_models,D:\LLM,D:\Pycharm_workplace -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'qwen|deepseek|glm|bge|embedding|llm|model' } | Select-Object -First 80 FullName"""
```

如果找到模型：

- 只记录路径和模型名。
- 不要立刻大改项目成强依赖本地模型。
- 优先把本地模型作为可选 provider 或后续路线。

当前 Demo 默认仍允许：

- 无 key 时规则 fallback。
- 有 key 时 API 增强。
- 后续再接 Ollama/vLLM/Transformers 本地模型。

## 7. 数据扩容任务边界

用户担心数据太少像玩具。优先做数据接入层，而不是乱爬招聘网站。

允许：

- 公开数据集小样本。
- 本地 fixture 生成公开岗位样本。
- Hugging Face streaming 小样本。
- Greenhouse/Lever/Ashby 公开 ATS API 的设计说明。

禁止：

- 爬 Boss、智联、牛客等可能有合规风险的平台。
- 下载几百 MB 或 GB 数据到项目。
- 把原始大数据提交进项目。

统一 schema：

```json
{
  "id": "",
  "title": "",
  "company": "",
  "city": "",
  "stage": "",
  "direction": "",
  "skills": [],
  "project_signals": [],
  "jd": "",
  "interview_themes": [],
  "source": "",
  "source_url": "",
  "posted_at": "",
  "data_quality_score": 0
}
```

## 8. 汇报格式

最终汇报必须包含：

1. 本轮目标。
2. 修改文件。
3. 本地验证结果。
4. 3060 验证结果。
5. core 指标。
6. stress 指标。
7. 生成/变更的数据量。
8. 剩余风险。
9. 下一步建议。

不要以“需要我继续吗？”结尾。

如果因平台限制必须停，输出：

```text
续跑提示词：
我刚完成到第 X 步，当前状态是……请从……继续，不要重做已完成部分。下一步命令是……
```

