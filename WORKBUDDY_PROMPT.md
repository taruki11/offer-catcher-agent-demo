# 给 WorkBuddy 的项目提示词

你要继续开发一个名为「Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统」的腾讯青科实训营作业一 Demo。

## 一、项目目标

目标不是做一个普通求职聊天机器人，而是做成一个能体现「大模型应用算法 / Agent 算法 / 推荐排序」能力的完整 Demo：

> Offer 捕手将学生求职问题建模为“用户画像-岗位推荐-能力缺口诊断-简历优化-面试准备”的闭环，通过 LLM Agent、语义检索、推荐排序和多 Agent 工作流，帮助学生快速找到高匹配岗位，并提升简历初筛命中率。

最终要交付：

1. 可运行完整 Demo，并部署到公网。
2. 1000 字以内方案说明，支持 DOC / PDF。
3. 可选 3 分钟演示视频脚本。
4. 项目代码需要从远程机器同步回本地留档和提交，但不要默认在本地运行。

## 二、运行与同步约束

请严格遵守路径规则：

1. 主要开发和运行环境：3060 远程 Windows 机器。
2. 远程开发/运行目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

3. 本地同步/备份目录：

```text
D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
```

4. 本地只用于留档、查看、打包、写汇报，不要默认在本地跑 Demo。
5. 每次完成重要开发后，都要把远程项目同步回本地。
6. 不要再使用 C 盘项目目录；之前的 C 盘目录已经删除。

推荐同步命令，从本机执行：

```powershell
scp -r 3060:D:/Pycharm_workplace/offer_catcher_agent_demo_20260602 D:/Pycharm_workplace/
```

如果本地目录已经存在，优先使用非破坏式同步；不要删除用户本地文件，除非明确确认。

## 三、当前项目状态

远程目录里已经有第一版无外部 API 依赖 MVP：

```text
index.html
styles.css
src/app.js
run_server.py
README.md
docs/方案说明.md
docs/演示脚本.md
```

当前版本功能：

- 简历文本输入
- 求职方向、城市、阶段选择
- 五个 Agent 流程展示
- 岗位 TopK 推荐榜
- 五维匹配雷达图
- 匹配优势、能力缺口、简历改写建议、7 天面试计划
- 前端内置岗位库和可解释规则，模拟 LLM + RAG + 推荐排序 + 多 Agent 流程

当前运行方式，在 3060 远程机器执行：

```powershell
cd D:\Pycharm_workplace\offer_catcher_agent_demo_20260602
python run_server.py
```

然后访问：

```text
http://localhost:8501
```

## 四、下一阶段开发目标

优先把项目从“静态规则 Demo”升级为“真实 LLM/RAG/Agent Demo”，但要保持简单、稳定、可演示。

建议实现顺序：

1. 保留现有前端页面和交互，不要大改 UI。
2. 增加 Python 后端，例如 FastAPI 或 Flask。
3. 将岗位库从 `src/app.js` 抽离为 `data/jobs.json`。
4. 后端提供 `/api/match` 接口，输入简历、目标方向、城市、阶段，输出岗位排序和诊断结果。
5. 先用规则版后端复刻当前前端逻辑，确保行为不回退。
6. 再接入可选 LLM API：
   - 简历结构化解析
   - JD 理解
   - 缺口分析
   - 简历改写
   - 面试计划生成
7. 增加 Embedding 召回接口：
   - 可先用轻量 TF-IDF / 关键词向量模拟
   - 有模型条件时再接 bge-small-zh / bge-m3 / OpenAI embedding / 其他兼容 embedding API
8. 增加 `.env.example`，不要把 API Key 写进代码。
9. 补充 README 中的部署方式。
10. 更新 `docs/方案说明.md` 和 `docs/演示脚本.md`，让汇报材料和实际 Demo 一致。

## 五、推荐系统和 Agent 设计要求

方案里一定要强调这几个算法点：

1. 简历和 JD 不是直接丢给模型聊天，而是先结构化解析。
2. 岗位匹配分成召回和精排两个阶段。
3. 召回阶段使用 Embedding / 语义检索获得 TopK 岗位。
4. 精排阶段使用多维度加权评分：

```text
Score = 0.32 * S_skill
      + 0.24 * S_project
      + 0.18 * S_experience
      + 0.16 * S_preference
      + 0.10 * S_growth
```

5. 多 Agent 工作流包括：

- Resume Parser Agent：解析简历，抽取教育、项目、技能、实习、指标
- JD Understanding Agent：解析岗位 JD，抽取硬技能、业务方向、能力要求
- Matching Ranker Agent：做人岗匹配召回、排序和解释
- Gap Analyzer Agent：分析能力缺口、简历风险和短板
- Resume Coach Agent：生成简历改写建议和面试准备计划

## 六、汇报材料要求

需要写一份 1000 字以内方案说明，建议结构：

1. 问题诊断：学生岗位筛选效率低、简历和 JD 差距不清晰。
2. 方案设计：简历解析、岗位召回、匹配精排、缺口诊断、简历优化、面试准备。
3. AI 工具选型：LLM 负责理解和生成，Embedding 负责语义匹配，Agent 负责任务拆解。
4. 关键配置：岗位库、Prompt 模板、评分公式、结构化输出、RAG 检索流程。
5. 迭代记录：从单轮问答升级到多 Agent，从单一相似度升级到多维排序。
6. 效果评估：推荐是否符合方向，解释是否具体，简历建议是否可直接改写。

汇报里必须出现一句核心定位：

> 本 Demo 不是简单让大模型给建议，而是先用语义召回找到候选岗位，再用多维度匹配模型进行排序，最后由 LLM Agent 生成可解释的简历优化和面试准备建议。

## 七、验收标准

完成后请确保：

1. 远程 3060 能运行 Demo。
2. 首页、CSS、JS、后端接口均能正常访问。
3. 示例简历一键运行能得到合理岗位排序。
4. 至少能展示一个大模型应用算法岗位的完整诊断。
5. 方案说明不超过 1000 字。
6. 项目已经同步回本地目录。
7. README 写清楚远程运行、本地同步、部署方式。

