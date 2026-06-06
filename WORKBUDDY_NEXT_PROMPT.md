# WorkBuddy 接手提示词：Offer 捕手下一阶段

请接手继续开发「Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统」。

这个项目不是普通网页，也不是 ChatGPT 套壳。用户的真实目标是：用腾讯青科实训营作业一冲 Demo 前 50，同时沉淀成以后求职“大模型算法 / LLM 应用算法 / Agent 算法”岗位时能写进简历、经得起面试追问的项目。

## 一、路径和运行约束

请严格遵守：

- 主要开发和运行机器：3060 远程 Windows 机器
- 远程运行目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

- 本地同步/留档目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

- 本地只用于留档、提交、打包、写汇报，不要默认在本地跑 Demo。
- 不要使用 C 盘旧目录，`C:\Users\29451\offer_catcher_agent_demo_20260602` 已废弃/删除。
- 每次完成重要开发后，把远程项目同步回本地。

## 二、项目定位

项目名：

```text
Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统
```

核心定位：

> 本 Demo 不是简单让大模型给建议，而是先用语义召回找到候选岗位，再用多维度匹配模型进行排序，最后由 LLM Agent 生成可解释的简历优化和面试准备建议。

请始终围绕这个方向做，不要改成普通求职助手。

## 三、当前已完成状态

远程和本地都已有两套 MVP：

### 1. 静态网页 MVP

文件：

```text
index.html
styles.css
src/app.js
run_server.py
```

能力：

- 简历输入
- 求职偏好选择
- 岗位推荐榜
- 五维雷达图
- 匹配优势、能力缺口、简历优化、7 天面试计划

运行：

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
python run_server.py
```

访问：

```text
http://localhost:8501
```

### 2. Python Streamlit MVP

文件：

```text
app.py
requirements.txt
.env.example
data/jobs.json
src/resume_parser.py
src/matcher.py
src/llm_client.py
prompts/resume_parser.md
prompts/jd_understanding.md
prompts/match_analysis.md
```

能力：

- 粘贴简历
- 选择目标方向、城市、求职阶段
- Resume Parser Agent 规则版解析学生画像
- 从 `data/jobs.json` 读取岗位库
- TopK 岗位推荐
- 多维评分
- 能力缺口分析
- 简历改写建议
- 7 天面试准备计划
- 可选 LLM 精排解释，配置 `.env` 后启用

远程已验证：

- `py_compile` 通过
- 示例简历 Top3：大模型应用算法实习生、校招人岗匹配算法实习生、智能搜索算法实习生
- Streamlit 临时启动返回 HTTP 200

运行：

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

访问：

```text
http://localhost:8502
```

## 四、下一阶段任务

请优先做这些，不要推翻已有结构：

1. 优化 `app.py` 的 Streamlit 页面，让它更像完整参赛 Demo：
   - 顶部项目介绍
   - 左侧简历和求职偏好输入
   - 中间岗位推荐榜
   - 右侧/下方匹配详情
   - 五维雷达图
   - 简历改写对照
   - 面试准备计划

2. 加雷达图：
   - 展示技能匹配、项目匹配、经历匹配、方向匹配、成长潜力
   - 可以用 `plotly` 或 Streamlit 原生图表

3. 加报告导出：
   - 一键生成 Markdown 报告
   - 内容包括：学生画像、TopK 岗位、匹配分、能力缺口、简历优化建议、面试计划
   - 后续可转 PDF / DOCX

4. 加 PDF 简历解析：
   - 可以先支持 `pdfplumber` 或 `pypdf`
   - 保留粘贴文本入口
   - PDF 失败时优雅提示用户粘贴文本

5. 改进 LLM 接入：
   - 不要把 API Key 写进代码
   - 继续使用 `.env.example`
   - 没有 Key 时规则版正常可跑
   - 有 Key 时 LLM 负责生成更自然的诊断解释、简历改写和面试问题

6. 准备汇报材料：
   - 更新 `docs/方案说明.md`
   - 控制在 1000 字以内
   - 强调 LLM Agent、语义召回、多维排序、简历优化闭环
   - 更新 `docs/演示脚本.md`

## 五、算法表达必须保留

岗位看成 item，学生画像看成 user profile。

召回阶段：

```text
u = f_embed(resume)
v_i = f_embed(JD_i)
s_i = cos(u, v_i)
```

精排阶段：

```text
Score = 0.30*S_skill
      + 0.25*S_project
      + 0.20*S_experience
      + 0.15*S_direction
      + 0.10*S_growth
```

五个 Agent：

- Resume Parser Agent：解析简历，抽取教育、技能、项目、实习、指标
- JD Understanding Agent：解析岗位 JD，抽取技能、业务方向、加分项
- Matching Ranker Agent：语义召回 + 多维排序
- Gap Analyzer Agent：分析能力缺口和简历风险
- Resume Coach Agent：生成简历改写建议和面试准备计划

## 六、验收标准

完成后请确保：

- 3060 远程能运行 Streamlit Demo
- `http://localhost:8502` 能打开
- 示例简历一键运行能得到合理 TopK
- 至少一个“大模型应用算法实习生”岗位能展示完整诊断
- 页面有雷达图或等价可视化
- 能导出一份岗位匹配报告
- 汇报材料和实际功能一致
- 项目已同步回本地留档目录

请先检查当前远程目录状态，再继续实现。不要从零重写；在已有 MVP 上迭代。
