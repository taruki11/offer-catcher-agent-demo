# WorkBuddy 路径纠偏与 3060 同步提示词

请先停一下，纠正项目路径规则。你之前在本地 `D:\Pycharm_workplace\offer_catcher_agent_demo_20260602` 里开发，这是不符合用户当前要求的。

## 一、最新路径规则

本地唯一工作区是：

```text
D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统
```

以后本地开发、写文档、生成提示词、查看代码，都必须在这个中文工作区根目录里进行。

这个中文工作区根目录现在已经直接包含项目代码：

```text
app.py
requirements.txt
.env.example
README.md
index.html
styles.css
run_server.py
data\
docs\
prompts\
src\
```

请不要再在本地 sibling 目录里开发：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

这个本地英文目录以后只视为旧镜像/历史副本，不要继续编辑，不要把它当作本地工作区，不要再新建同名目录。

## 二、请先阅读这些 Codex 已写好的交接文件

这些文件都在本地中文工作区根目录：

```text
D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统
```

请优先阅读以下文件，再继续开发：

```text
WORKBUDDY_PROMPT.md
WORKBUDDY_NEXT_PROMPT.md
WORKBUDDY_BUSINESS_PIVOT_PROMPT.md
WORKBUDDY_TOP50_MULTI_AGENT_PROMPT.md
WORKBUDDY_PATH_AND_3060_PROMPT.md
```

每个文件的作用：

### 1. `WORKBUDDY_PROMPT.md`

这是最早的项目总提示词，说明了 Offer 捕手的基础目标：

- 腾讯青科实训营作业一
- 大模型应用算法 / Agent 算法项目沉淀
- 远程 3060 运行
- 本地只留档
- 初始技术路线：LLM + RAG + 推荐排序 + 多 Agent

### 2. `WORKBUDDY_NEXT_PROMPT.md`

这是第一版 MVP 后的接手提示词，说明当前已经有：

- 静态网页 MVP
- Streamlit Python MVP
- `app.py`
- `data/jobs.json`
- `src/resume_parser.py`
- `src/matcher.py`
- `src/llm_client.py`
- `prompts/`

并要求继续做：

- 参赛级页面
- 雷达图
- 报告导出
- PDF 简历解析
- LLM 接入

### 3. `WORKBUDDY_BUSINESS_PIVOT_PROMPT.md`

这是差异化定位提示词。用户已有一个很完整的 RAG 项目：

```text
D:\Pycharm_workplace\llm_for_rec_agent
```

所以 Offer 捕手不要再做成另一个重 RAG 项目，而要突出：

- 求职转化率优化
- 岗位投递决策
- 简历版本管理
- MatchScore / PassScore / RiskScore / ApplyPriority

### 4. `WORKBUDDY_TOP50_MULTI_AGENT_PROMPT.md`

这是当前最重要的产品/技术提示词。请重点阅读。

它明确了 Offer 捕手的最终方向：

```text
Offer 捕手：基于多 Agent 协作的学生岗位匹配与简历转化率优化系统
```

核心要求：

- 不做普通聊天机器人
- 不只做语义匹配
- 不只做 RAG
- 要做成“Agent 决策驾驶舱”
- 目标是冲腾讯青科实训营前 50
- 同时沉淀为大模型应用算法 / Agent 应用算法简历项目

它定义了 7 个 Agent：

1. Profile Builder Agent
2. JD Intelligence Agent
3. Opportunity Scout Agent
4. Application Ranker Agent
5. Gap Diagnosis Agent
6. Resume Conversion Agent
7. Strategy Planner Agent

### 5. `WORKBUDDY_PATH_AND_3060_PROMPT.md`

就是当前这份文件，用来纠正路径和同步规则：

- 本地唯一工作区是中文目录
- 3060 远端运行目录是英文目录
- 不要再使用本地英文 sibling 目录
- 本地完成不等于最终完成
- 最终完成必须同步到 3060 并远程验证

## 三、3060 远端运行目录

3060 远程 Windows 机器上的运行目录仍然是：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

注意：

- 本地：中文目录
- 远端 3060：英文目录

这是故意这样分工的，不要试图把远端也改成中文目录，也不要把本地又改回英文目录。

## 四、如何连接 3060

即使你没有所谓“3060 连接器权限”，只要你能运行终端命令，就可以用 SSH 别名连接：

```powershell
ssh 3060 "hostname"
```

如果能返回远程主机名，说明 3060 可用。

检查远程项目目录：

```powershell
ssh 3060 "powershell -NoProfile -Command ""Get-ChildItem -Force -LiteralPath 'D:\Pycharm_workplace\offer_catcher_agent_demo_20260602'"""
```

如果你的终端对引号处理不稳定，可以先只做简单命令：

```powershell
ssh 3060 "cmd /c dir D:\Pycharm_workplace\offer_catcher_agent_demo_20260602 /a"
```

## 五、本地改完后如何同步到 3060

请在本地中文工作区根目录执行同步命令。

先进入本地中文工作区：

```powershell
cd "D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统"
```

然后同步这些项目文件到 3060：

```powershell
scp -r app.py requirements.txt .env.example README.md index.html styles.css run_server.py data docs prompts src 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602/
```

不要从本地英文 sibling 目录同步。

## 六、3060 上的验证命令

同步后必须在 3060 上验证，不能只说“本地完成”。

语法检查：

```powershell
ssh 3060 "powershell -NoProfile -Command ""cd 'D:\Pycharm_workplace\offer_catcher_agent_demo_20260602'; python -m py_compile app.py src\matcher.py src\conversion.py src\strategy_planner.py src\report_generator.py"""
```

核心工作流检查：

```powershell
ssh 3060 "powershell -NoProfile -Command ""cd 'D:\Pycharm_workplace\offer_catcher_agent_demo_20260602'; python -c \""from pathlib import Path; from src.resume_parser import parse_resume; from src.matcher import rank_jobs; from src.strategy_planner import gen_strategy_package; from src.report_generator import generate_report; resume='Python RAG Agent Embedding FAISS 推荐系统 Transformer NDCG 简历 JD 岗位匹配 A/B Test'; profile=parse_resume(resume); jobs=rank_jobs(resume, profile, '大模型应用算法', '深圳', '实习', 5, Path('data/jobs.json')); strategy=gen_strategy_package(jobs, profile); report=generate_report(profile, jobs, strategy); print('REMOTE_WORKFLOW_OK'); print([(j.get('title'), j.get('match_score'), j.get('pass_score'), j.get('risk_score'), j.get('growth_score'), j.get('apply_priority')) for j in jobs[:3]]); print('REPORT_LEN', len(report))\"" """
```

如果上面这条因为 PowerShell 引号复杂而失败，不要判断代码失败；请改用更简单的远程验证，或者让 Codex 代为远程验证。

Streamlit 运行命令：

```powershell
ssh 3060 "powershell -NoProfile -Command ""cd 'D:\Pycharm_workplace\offer_catcher_agent_demo_20260602'; streamlit run app.py --server.address 0.0.0.0 --server.port 8502"""
```

访问：

```text
http://localhost:8502
```

如果你是从本机浏览器访问远程 3060，需要使用 3060 的可访问 IP 或端口转发方式。

## 七、完成状态怎么汇报

以后请严格区分：

### 只能说“本地开发完成”的情况

如果你只在本地中文工作区改了代码，但没有成功同步和验证 3060，请这样汇报：

```text
我已在本地中文工作区完成开发，但尚未完成 3060 远程同步和运行验证。
请使用 scp 同步到 3060，并在 3060 上执行 py_compile 和 streamlit 验证。
```

### 可以说“最终完成”的情况

只有满足以下条件，才能说最终完成：

1. 本地中文工作区代码已更新
2. 已同步到 3060 远端目录
3. 3060 上 `py_compile` 通过
4. 3060 上核心工作流测试通过
5. 3060 上 Streamlit 能启动
6. 测试后没有留下无关后台进程

## 八、当前项目目标不要变

继续做的是：

```text
Offer 捕手：基于多 Agent 协作的学生岗位匹配与简历转化率优化系统
```

重点不是普通语义匹配，也不是另一个 RAG 项目，而是：

- 7 个 Agent 的协作流程
- Agent 决策驾驶舱
- MatchScore / PassScore / RiskScore / GrowthScore / ApplyPriority
- 简历改写对照
- 7 天投递策略
- Markdown 报告导出
- 腾讯青科实训营作业前 50 质量

请先确认你当前工作目录是本地中文工作区，再继续工作。
