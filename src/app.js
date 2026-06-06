const sampleResume = `张同学 | 计算机科学与技术 | 2026届硕士

求职方向：大模型应用算法 / 推荐算法实习生，期望城市深圳或北京。

技能：Python、PyTorch、Transformer、RAG、Agent、Embedding、FAISS、LangChain、推荐系统、召回排序、NDCG、A/B Test、SQL。

项目经历：
1. GenAdRec 生成式广告推荐项目：基于 Transformer 建模用户行为序列，将广告候选集转化为生成式 likelihood rerank 问题；构建 Semantic ID 表示广告 item，结合多兴趣召回提升 NDCG@10。
2. LLM 求职助手 Demo：使用 DeepSeek API 和 bge embedding 实现 JD 检索、简历关键词诊断、Prompt 模板优化，支持输出岗位匹配解释。
3. MIND 多兴趣推荐复现：复现 capsule routing 用户多兴趣建模，在公开数据集上对比召回 HitRate 与 NDCG。

实习经历：
曾参与推荐系统离线评估脚本开发，负责样本构造、特征清洗和模型结果分析。

补充：希望找能结合 LLM、Agent、RAG 和推荐排序的算法岗位。`;

const jobs = [
  {
    id: "llm-agent",
    title: "大模型应用算法实习生",
    company: "腾讯云智能",
    city: "深圳",
    direction: "大模型应用算法",
    stage: "实习",
    skills: ["LLM", "RAG", "Agent", "Embedding", "Python", "Prompt", "LangChain", "FAISS"],
    projectSignals: ["RAG", "Agent", "Embedding", "Prompt", "检索", "简历", "JD"],
    jd: "负责企业知识库问答、RAG 检索增强、Agent 工具调用、多轮对话效果优化，要求熟悉 Python、Embedding、Prompt Engineering 和 LLM 应用评估。",
    interviewThemes: ["RAG 召回与重排", "Agent 工具调用失败兜底", "Prompt 结构化输出", "Embedding 评估指标"]
  },
  {
    id: "rec-llm",
    title: "LLM 推荐算法实习生",
    company: "内容平台事业群",
    city: "北京",
    direction: "推荐算法",
    stage: "实习",
    skills: ["推荐系统", "Transformer", "召回", "排序", "Embedding", "NDCG", "PyTorch", "A/B Test"],
    projectSignals: ["推荐", "Transformer", "Semantic ID", "rerank", "NDCG", "召回"],
    jd: "负责内容推荐召回排序模型优化，探索 LLM 与推荐系统结合，包括语义表征、用户兴趣建模、候选集重排和离线指标评估。",
    interviewThemes: ["召回排序链路", "多兴趣建模", "Semantic ID", "NDCG 与线上指标"]
  },
  {
    id: "search-rag",
    title: "智能搜索算法实习生",
    company: "微信事业群",
    city: "广州",
    direction: "大模型应用算法",
    stage: "实习",
    skills: ["搜索", "RAG", "向量检索", "Embedding", "重排", "Python", "评估"],
    projectSignals: ["检索", "RAG", "Embedding", "FAISS", "重排", "TopK"],
    jd: "建设面向业务知识的智能搜索系统，优化 query 理解、向量召回、cross-encoder 重排和答案生成质量。",
    interviewThemes: ["向量召回 TopK", "重排模型", "搜索相关性评估", "幻觉控制"]
  },
  {
    id: "backend-ai",
    title: "AI 平台后端研发实习生",
    company: "混元平台",
    city: "深圳",
    direction: "后端研发",
    stage: "实习",
    skills: ["Python", "FastAPI", "服务部署", "SQL", "Redis", "API", "Docker"],
    projectSignals: ["API", "后端", "部署", "服务", "SQL"],
    jd: "负责大模型平台后端服务开发、API 编排、任务队列、日志监控和模型服务接入。",
    interviewThemes: ["API 设计", "异步任务", "缓存策略", "服务稳定性"]
  },
  {
    id: "data-analyst",
    title: "校招数据分析实习生",
    company: "HR Tech",
    city: "上海",
    direction: "数据分析",
    stage: "实习",
    skills: ["SQL", "Python", "可视化", "指标体系", "漏斗分析", "A/B Test"],
    projectSignals: ["SQL", "指标", "分析", "A/B", "可视化"],
    jd: "围绕校招转化漏斗、渠道质量和简历初筛效果进行数据分析，建设可视化看板并输出业务洞察。",
    interviewThemes: ["漏斗指标", "归因分析", "SQL 窗口函数", "实验设计"]
  },
  {
    id: "product-ai",
    title: "AI 产品经理实习生",
    company: "企服产品部",
    city: "深圳",
    direction: "产品经理",
    stage: "实习",
    skills: ["用户研究", "Prompt", "产品设计", "数据分析", "原型", "LLM"],
    projectSignals: ["用户", "产品", "Prompt", "Demo", "需求"],
    jd: "负责 AI 助手类产品需求分析、Prompt 配置、原型设计、效果验收和用户反馈闭环。",
    interviewThemes: ["需求拆解", "Prompt 评估", "用户体验", "产品指标"]
  },
  {
    id: "campus-rec",
    title: "校招人岗匹配算法实习生",
    company: "招聘技术中心",
    city: "北京",
    direction: "大模型应用算法",
    stage: "实习",
    skills: ["人岗匹配", "推荐系统", "Embedding", "LLM", "排序", "可解释性", "Python"],
    projectSignals: ["岗位", "简历", "匹配", "推荐", "排序", "Embedding"],
    jd: "基于简历和 JD 构建人岗匹配模型，优化候选人召回、岗位推荐排序、匹配解释和简历优化建议。",
    interviewThemes: ["人岗匹配建模", "冷启动", "特征交叉", "可解释排序"]
  },
  {
    id: "game-ai",
    title: "游戏 AI 算法实习生",
    company: "互动娱乐事业群",
    city: "上海",
    direction: "大模型应用算法",
    stage: "校招",
    skills: ["LLM", "强化学习", "Agent", "Python", "多模态", "评估"],
    projectSignals: ["Agent", "多模态", "评估", "LLM"],
    jd: "探索游戏 NPC Agent、剧情生成、行为决策和多模态内容理解，要求有 LLM Agent 或强化学习项目经验。",
    interviewThemes: ["Agent 记忆机制", "行为决策", "多模态理解", "自动评估"]
  }
];

const agents = [
  ["Resume Parser", "抽取教育、技能、项目、经历"],
  ["JD Understanding", "解析岗位技能与业务要求"],
  ["Matching Ranker", "召回 TopK 并多维排序"],
  ["Gap Analyzer", "定位能力缺口与简历风险"],
  ["Resume Coach", "生成改写建议与面试计划"]
];

const skillCatalog = [
  "LLM", "RAG", "Agent", "Embedding", "FAISS", "LangChain", "Prompt", "Python",
  "PyTorch", "Transformer", "推荐系统", "召回", "排序", "NDCG", "A/B Test",
  "SQL", "FastAPI", "Docker", "Redis", "搜索", "重排", "向量检索", "多模态",
  "强化学习", "产品设计", "可视化", "指标体系"
];

const state = {
  results: [],
  selectedIndex: 0,
  activeTab: "strengths"
};

const el = {
  resumeInput: document.querySelector("#resumeInput"),
  targetRole: document.querySelector("#targetRole"),
  targetCity: document.querySelector("#targetCity"),
  careerStage: document.querySelector("#careerStage"),
  runBtn: document.querySelector("#runBtn"),
  clearBtn: document.querySelector("#clearBtn"),
  sampleBtn: document.querySelector("#sampleBtn"),
  agentStrip: document.querySelector("#agentStrip"),
  jobList: document.querySelector("#jobList"),
  bestTitle: document.querySelector("#bestTitle"),
  bestCompany: document.querySelector("#bestCompany"),
  bestScore: document.querySelector("#bestScore"),
  skillCount: document.querySelector("#skillCount"),
  skillPreview: document.querySelector("#skillPreview"),
  detailTitle: document.querySelector("#detailTitle"),
  detailMeta: document.querySelector("#detailMeta"),
  scoreBreakdown: document.querySelector("#scoreBreakdown"),
  radarCanvas: document.querySelector("#radarCanvas"),
  tabContent: document.querySelector("#tabContent"),
  tabs: Array.from(document.querySelectorAll(".tab"))
};

function normalize(text) {
  return (text || "").toLowerCase();
}

function includesTerm(text, term) {
  return normalize(text).includes(term.toLowerCase());
}

function unique(items) {
  return Array.from(new Set(items)).filter(Boolean);
}

function clampScore(score) {
  return Math.max(0, Math.min(100, Math.round(score)));
}

function extractProfile(resume) {
  const foundSkills = skillCatalog.filter((skill) => includesTerm(resume, skill));
  const projectSignals = unique([
    ...foundSkills,
    ...["Semantic ID", "rerank", "MIND", "简历", "JD", "岗位", "检索", "评估", "Demo"].filter((term) =>
      includesTerm(resume, term)
    )
  ]);

  return {
    foundSkills,
    projectSignals,
    hasMetric: /ndcg|hitrate|auc|准确率|召回率|提升|%|topk/i.test(resume),
    hasLLMProject: /llm|rag|agent|prompt|deepseek|openai|通义|混元/i.test(resume),
    hasRecProject: /推荐|召回|排序|mind|semantic id|rerank|用户兴趣/i.test(resume)
  };
}

function overlapCount(required, actual, resume) {
  return required.filter((term) => actual.includes(term) || includesTerm(resume, term)).length;
}

function scoreJob(job, profile, resume, preferences) {
  const skillHits = overlapCount(job.skills, profile.foundSkills, resume);
  const projectHits = overlapCount(job.projectSignals, profile.projectSignals, resume);

  const skillScore = clampScore((skillHits / job.skills.length) * 100);
  const projectBase = job.projectSignals.length ? (projectHits / job.projectSignals.length) * 100 : 60;
  const projectBonus = profile.hasMetric ? 8 : 0;
  const projectScore = clampScore(projectBase + projectBonus);
  const experienceScore = clampScore(job.stage === preferences.stage ? 86 : 68);
  const directionScore = clampScore(
    job.direction === preferences.role ? 92 : includesTerm(job.direction, preferences.role) ? 80 : 55
  );
  const cityScore = clampScore(
    preferences.city === "不限" ? 88 : job.city === preferences.city ? 96 : 62
  );
  const preferenceScore = clampScore(directionScore * 0.66 + cityScore * 0.34);
  const growthScore = clampScore(
    48 +
      Math.min(profile.foundSkills.length, 10) * 3 +
      (profile.hasLLMProject ? 12 : 0) +
      (profile.hasRecProject ? 8 : 0)
  );

  const total = clampScore(
    0.32 * skillScore +
      0.24 * projectScore +
      0.18 * experienceScore +
      0.16 * preferenceScore +
      0.1 * growthScore
  );

  const matchedSkills = job.skills.filter((term) => includesTerm(resume, term));
  const missingSkills = job.skills.filter((term) => !includesTerm(resume, term));

  return {
    ...job,
    total,
    matchedSkills,
    missingSkills,
    dimensions: {
      "技能匹配": skillScore,
      "项目相关": projectScore,
      "经历阶段": experienceScore,
      "偏好一致": preferenceScore,
      "成长潜力": growthScore
    },
    strengths: buildStrengths(job, matchedSkills, profile),
    gaps: buildGaps(job, missingSkills, profile),
    rewrites: buildRewrites(job, matchedSkills, missingSkills, profile),
    plan: buildPlan(job, missingSkills)
  };
}

function buildStrengths(job, matchedSkills, profile) {
  const strengths = [];
  if (matchedSkills.length) {
    strengths.push(`命中岗位核心关键词：${matchedSkills.slice(0, 6).join("、")}，具备进入精排池的基础。`);
  }
  if (profile.hasLLMProject && job.direction.includes("大模型")) {
    strengths.push("简历中已经出现 LLM/RAG/Agent 相关项目，可直接对齐大模型应用算法岗位。");
  }
  if (profile.hasRecProject && (job.direction.includes("推荐") || job.jd.includes("匹配"))) {
    strengths.push("推荐系统、召回排序和语义表征经历能自然迁移到人岗匹配或内容推荐场景。");
  }
  if (profile.hasMetric) {
    strengths.push("项目描述中包含 NDCG、HitRate、TopK 等指标，便于证明算法效果。");
  }
  if (!strengths.length) {
    strengths.push("简历具备基础技术栈，但需要补充更明确的项目证据和岗位关键词。");
  }
  return strengths;
}

function buildGaps(job, missingSkills, profile) {
  const gaps = [];
  if (missingSkills.length) {
    gaps.push(`岗位还要求 ${missingSkills.slice(0, 5).join("、")}，建议在项目或技能栏补充真实经历。`);
  }
  if (!profile.hasMetric) {
    gaps.push("项目缺少可量化指标，容易被认为只是功能实现，建议补充离线评估或效果提升。");
  }
  if (job.jd.includes("Agent") && !includesTerm(profile.projectSignals.join(" "), "Agent")) {
    gaps.push("Agent 工作流表达不够突出，需要写清任务拆解、工具调用、失败兜底和评估方式。");
  }
  if (job.jd.includes("评估") && !/评估|指标|NDCG|HitRate|A\/B/i.test(profile.projectSignals.join(" "))) {
    gaps.push("岗位强调效果评估，简历需补充准确率、相关性、召回率或人工验收指标。");
  }
  return gaps;
}

function buildRewrites(job, matchedSkills, missingSkills, profile) {
  const mainSkill = matchedSkills[0] || job.skills[0];
  const missing = missingSkills[0] || job.skills[job.skills.length - 1];
  return [
    {
      before: "负责推荐系统建模和模型结果分析。",
      after: `围绕 ${job.direction} 场景，使用 ${mainSkill} 构建候选召回与精排链路，并通过 NDCG@10 / TopK 命中率评估模型收益。`
    },
    {
      before: "做过一个 LLM 求职助手 Demo。",
      after: `设计多 Agent 求职匹配流程，将简历解析、JD 理解、岗位排序、能力缺口诊断和简历优化拆成可解释节点，提升输出稳定性。`
    },
    {
      before: "熟悉大模型相关技术。",
      after: `熟悉 ${job.skills.slice(0, 4).join("、")}；可独立完成 Prompt 模板、结构化输出、检索增强和结果评估配置。`
    },
    {
      before: "技能栏可以继续补充。",
      after: `若确有实践，建议补充 ${missing}，并用一次实验、接口调用或离线评估证明不是仅停留在概念层。`
    }
  ];
}

function buildPlan(job, missingSkills) {
  const focus = missingSkills.slice(0, 3);
  return [
    `第 1 天：复盘 ${job.direction} 岗位 JD，整理岗位关键词和自己项目的对应证据。`,
    `第 2 天：准备 ${job.interviewThemes[0]}，用一个项目讲清输入、模型、输出、指标。`,
    `第 3 天：补齐 ${focus[0] || job.skills[0]} 的实践案例，写成可追问的简历 bullet。`,
    `第 4 天：准备 ${job.interviewThemes[1]}，重点讲失败 case 和优化方案。`,
    `第 5 天：针对 ${job.company} 场景模拟 3 个业务问题，练习算法方案设计。`,
    "第 6 天：做一次 20 分钟项目深挖 mock，覆盖数据、模型、评估、工程落地。",
    "第 7 天：压缩成 1 分钟自我介绍、3 分钟项目介绍和 5 个高频追问答案。"
  ];
}

function runMatch() {
  const resume = el.resumeInput.value.trim();
  if (!resume) {
    renderEmpty("请先粘贴简历文本，或点击“填充示例”。");
    return;
  }

  renderAgents(true);
  const preferences = {
    role: el.targetRole.value,
    city: el.targetCity.value,
    stage: el.careerStage.value
  };
  const profile = extractProfile(resume);
  state.results = jobs
    .map((job) => scoreJob(job, profile, resume, preferences))
    .sort((a, b) => b.total - a.total);
  state.selectedIndex = 0;
  state.activeTab = "strengths";

  renderAll(profile);
}

function renderAll(profile) {
  renderAgents(false);
  renderSummary(profile);
  renderJobList();
  renderDetail();
}

function renderAgents(active) {
  el.agentStrip.innerHTML = agents
    .map(
      ([name, desc], index) => `
        <div class="agent-step ${active || state.results.length ? "active" : ""}">
          <strong>${index + 1}. ${name}</strong>
          <span>${desc}</span>
        </div>
      `
    )
    .join("");
}

function renderSummary(profile) {
  const best = state.results[0];
  el.bestTitle.textContent = best.title;
  el.bestCompany.textContent = `${best.company} · ${best.city} · ${best.stage}`;
  el.bestScore.textContent = `${best.total}/100`;
  el.skillCount.textContent = `${profile.foundSkills.length} 个`;
  el.skillPreview.textContent = profile.foundSkills.slice(0, 5).join("、") || "未命中明显技能词";
}

function renderJobList() {
  el.jobList.innerHTML = state.results
    .map((job, index) => {
      const tags = job.skills
        .slice(0, 5)
        .map((skill) => `<span class="tag ${job.matchedSkills.includes(skill) ? "hit" : ""}">${skill}</span>`)
        .join("");
      return `
        <article class="job-card ${index === state.selectedIndex ? "active" : ""}" data-index="${index}">
          <div class="job-row-top">
            <div class="job-title">${job.title}</div>
            <div class="score-pill">${job.total}</div>
          </div>
          <div class="job-meta">${job.company} · ${job.city} · ${job.direction}</div>
          <div class="job-tags">${tags}</div>
        </article>
      `;
    })
    .join("");

  document.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedIndex = Number(card.dataset.index);
      state.activeTab = "strengths";
      renderJobList();
      renderDetail();
    });
  });
}

function renderDetail() {
  const job = state.results[state.selectedIndex];
  if (!job) {
    renderEmpty("运行匹配后查看岗位诊断。");
    return;
  }

  el.detailTitle.textContent = job.title;
  el.detailMeta.textContent = `${job.company} · ${job.city} · ${job.stage}`;
  renderBreakdown(job);
  drawRadar(job.dimensions);
  updateTabs();
  renderTabContent(job);
}

function renderBreakdown(job) {
  el.scoreBreakdown.innerHTML = Object.entries(job.dimensions)
    .map(
      ([name, value]) => `
        <div class="score-line">
          <span>${name}</span>
          <div class="bar"><span style="width:${value}%"></span></div>
          <strong>${value}</strong>
        </div>
      `
    )
    .join("");
}

function drawRadar(dimensions) {
  const canvas = el.radarCanvas;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const cx = width / 2;
  const cy = height / 2 + 4;
  const radius = 82;
  const entries = Object.entries(dimensions);

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#d9e0e8";
  ctx.fillStyle = "#667085";
  ctx.font = "12px Microsoft YaHei, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  for (let level = 1; level <= 4; level += 1) {
    drawPolygon(ctx, entries.length, cx, cy, (radius * level) / 4, false);
  }

  entries.forEach(([label], index) => {
    const angle = (Math.PI * 2 * index) / entries.length - Math.PI / 2;
    const x = cx + Math.cos(angle) * (radius + 24);
    const y = cy + Math.sin(angle) * (radius + 18);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
    ctx.stroke();
    ctx.fillText(label, x, y);
  });

  const points = entries.map(([, value], index) => {
    const angle = (Math.PI * 2 * index) / entries.length - Math.PI / 2;
    const pointRadius = (radius * value) / 100;
    return [cx + Math.cos(angle) * pointRadius, cy + Math.sin(angle) * pointRadius];
  });

  ctx.beginPath();
  points.forEach(([x, y], index) => {
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(15, 143, 114, 0.18)";
  ctx.strokeStyle = "#0f8f72";
  ctx.lineWidth = 2;
  ctx.fill();
  ctx.stroke();
}

function drawPolygon(ctx, sides, cx, cy, radius, fill) {
  ctx.beginPath();
  for (let i = 0; i < sides; i += 1) {
    const angle = (Math.PI * 2 * i) / sides - Math.PI / 2;
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.closePath();
  if (fill) ctx.fill();
  ctx.stroke();
}

function updateTabs() {
  el.tabs.forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === state.activeTab);
  });
}

function renderTabContent(job) {
  if (state.activeTab === "strengths") {
    el.tabContent.innerHTML = listHtml(job.strengths);
    return;
  }
  if (state.activeTab === "gaps") {
    el.tabContent.innerHTML = listHtml(job.gaps, "warning");
    return;
  }
  if (state.activeTab === "rewrite") {
    el.tabContent.innerHTML = `
      <div class="rewrite-block">
        ${job.rewrites
          .map(
            (item) => `
              <div class="rewrite-card">
                <span>原表达</span>
                <p>${item.before}</p>
              </div>
              <div class="rewrite-card">
                <span>建议改写</span>
                <p>${item.after}</p>
              </div>
            `
          )
          .join("")}
      </div>
    `;
    return;
  }
  el.tabContent.innerHTML = listHtml(job.plan);
}

function listHtml(items, className = "") {
  return `
    <ul class="insight-list">
      ${items.map((item) => `<li class="${className}">${item}</li>`).join("")}
    </ul>
  `;
}

function renderEmpty(message) {
  el.jobList.innerHTML = `<div class="empty-state">${message}</div>`;
  el.tabContent.innerHTML = `<div class="empty-state">${message}</div>`;
}

el.runBtn.addEventListener("click", runMatch);
el.sampleBtn.addEventListener("click", () => {
  el.resumeInput.value = sampleResume;
  runMatch();
});
el.clearBtn.addEventListener("click", () => {
  el.resumeInput.value = "";
  state.results = [];
  el.bestTitle.textContent = "等待分析";
  el.bestCompany.textContent = "填写简历后运行";
  el.bestScore.textContent = "--";
  el.skillCount.textContent = "--";
  el.skillPreview.textContent = "待解析";
  renderAgents(false);
  renderEmpty("请先粘贴简历文本，或点击“填充示例”。");
  drawRadar({ "技能匹配": 0, "项目相关": 0, "经历阶段": 0, "偏好一致": 0, "成长潜力": 0 });
});

el.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    state.activeTab = tab.dataset.tab;
    updateTabs();
    const job = state.results[state.selectedIndex];
    if (job) renderTabContent(job);
  });
});

el.resumeInput.value = sampleResume;
renderAgents(false);
runMatch();
