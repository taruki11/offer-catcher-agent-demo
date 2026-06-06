"""
岗位库扩容脚本：从 48 条扩展到 200+ 条
生成真实感的校招岗位，标注来源、质量分、方向标签
"""
import json
import random
import os

# 真实感的岗位模板
JOB_TEMPLATES = [
    # ========== 大模型/LLM 方向 ==========
    {
        "direction": "大模型应用算法",
        "titles": [
            "大模型应用算法实习生", "LLM算法实习生", "大模型研发实习生",
            "AIGC算法实习生", "大模型推理优化实习生", "Prompt Engineering实习生",
            "大模型训练实习生", "LLM应用开发实习生"
        ],
        "companies": ["腾讯云智能", "阿里达摩院", "百度智能云", "字节跳动AI Lab", 
                     "商汤科技", "旷视科技", "华为诺亚", "美团AI平台"],
        "cities": ["北京", "上海", "深圳", "杭州"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["LLM", "RAG", "Agent", "Embedding", "Python", "Prompt", "LangChain", "FAISS"],
            ["PyTorch", "Transformer", "SFT", "RLHF", "DeepSpeed", "vLLM"],
            ["Prompt Engineering", "Few-shot", "Chain-of-Thought", "ReAct", "Function Calling"],
            ["向量数据库", "Milvus", "Chroma", "Hybrid Search", "Rerank"],
        ],
        "project_signals_pool": [
            ["RAG", "Agent", "Embedding", "检索"],
            ["SFT", "微调", "LoRA", "QLoRA"],
            ["推理优化", "量化", "vLLM", "TensorRT"],
        ],
        "jd_templates": [
            "负责大模型应用开发，包括 RAG 检索增强、Agent 工具调用、Prompt 优化等。",
            "参与大模型训练与微调，负责数据清洗、SFT/RLHF 训练、模型评估。",
            "负责 LLM 推理优化，包括量化、蒸馏、vLLM 部署等加速技术。",
        ],
        "interview_themes_pool": [
            ["RAG 召回与重排", "Agent 工具调用", "Prompt 工程"],
            ["SFT vs RLHF", "LoRA 微调", "模型评估指标"],
            ["推理优化", "量化算法", "部署架构"],
        ],
        "base_pass": 55,
        "base_risk": 45,
        "base_growth": 75,
    },
    # ========== 推荐算法方向 ==========
    {
        "direction": "推荐算法",
        "titles": [
            "推荐算法实习生", "推荐系统开发实习生", "排序算法实习生",
            "召回算法实习生", "推荐策略实习生", "信息流推荐实习生"
        ],
        "companies": ["字节跳动", "快手", "美团", "阿里妈妈", "腾讯广告", "京东零售", "网易云音乐"],
        "cities": ["北京", "上海", "深圳", "杭州"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["推荐系统", "Transformer", "召回", "排序", "Embedding", "NDCG", "PyTorch"],
            ["DeepFM", "DIN", "DIEN", "Multi-task", "MMOE", "PLE"],
            ["协同过滤", "矩阵分解", "Item-CF", "User-CF", "图神经网络"],
            ["在线学习", "Bandit", "强化学习", "DQN", "Slate推荐"],
        ],
        "project_signals_pool": [
            ["召回", "排序", "Embedding", "评估"],
            ["DeepFM", "DIN", "多任务"],
            ["在线学习", "Bandit"],
        ],
        "jd_templates": [
            "负责推荐系统召回/排序算法研发，包括模型设计、特征工程、在线实验等。",
            "参与多目标排序模型优化，负责 MMOE/PLE 模型改进与在线 A/B 测试。",
            "负责推荐策略优化，包括多样性、新颖性、长期价值建模等。",
        ],
        "interview_themes_pool": [
            ["召回算法", "排序模型", "Embedding 技术"],
            ["DeepFM/DIN", "多任务学习", "评估指标"],
            ["在线实验", "A/B 测试", "因果推断"],
        ],
        "base_pass": 58,
        "base_risk": 42,
        "base_growth": 72,
    },
    # ========== 计算机视觉方向 ==========
    {
        "direction": "计算机视觉",
        "titles": [
            "计算机视觉算法实习生", "CV算法实习生", "图像算法实习生",
            "视频理解实习生", "目标检测实习生", "图像分割实习生"
        ],
        "companies": ["商汤科技", "旷视科技", "云从科技", "依图科技", "腾讯优图", "阿里达摩院", "百度视觉"],
        "cities": ["北京", "上海", "深圳", "杭州", "成都"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["ResNet", "CNN", "Vision Transformer", "Swin Transformer", "PyTorch"],
            ["YOLO", "Faster R-CNN", "Mask R-CNN", "DETR", "目标检测"],
            ["U-Net", "DeepLab", "Mask2Former", "图像分割"],
            ["时序模型", "SlowFast", "Video Transformer", "视频理解"],
        ],
        "project_signals_pool": [
            ["分类", "检测", "分割", "CNN"],
            ["ViT", "Transformer", "注意力机制"],
            ["视频理解", "时序建模"],
        ],
        "jd_templates": [
            "参与目标检测/图像分割算法研发，负责模型训练、推理优化、数据增强等。",
            "负责视频理解算法研发，包括动作识别、时序建模、多模态融合等。",
            "参与 CV 模型压缩与加速，包括剪枝、量化、蒸馏、TensorRT 部署等。",
        ],
        "interview_themes_pool": [
            ["CNN 架构", "ViT 原理", "检测算法"],
            ["分割算法", "实例分割", "全景分割"],
            ["模型压缩", "推理优化", "部署方案"],
        ],
        "base_pass": 60,
        "base_risk": 40,
        "base_growth": 70,
    },
    # ========== NLP 方向 ==========
    {
        "direction": "自然语言处理",
        "titles": [
            "NLP算法实习生", "自然语言处理实习生", "文本挖掘实习生",
            "信息抽取实习生", "机器翻译实习生", "文本生成实习生"
        ],
        "companies": ["阿里达摩院", "百度NLP", "腾讯AI Lab", "字节跳动AI Lab", "华为诺亚", "科大讯飞"],
        "cities": ["北京", "上海", "深圳", "杭州", "合肥"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["BERT", "RoBERTa", "GPT", "T5", "Transformer", "PyTorch"],
            ["命名实体识别", "关系抽取", "事件抽取", "信息抽取"],
            ["机器翻译", "文本摘要", "文本生成", "对话系统"],
            ["句向量", "文本相似度", "文本分类", "情感分析"],
        ],
        "project_signals_pool": [
            ["NER", "抽取", "BERT"],
            ["翻译", "生成", "GPT"],
            ["分类", "情感", "句向量"],
        ],
        "jd_templates": [
            "参与 NLP 模型研发，包括预训练模型微调、信息抽取、文本分类等。",
            "负责机器翻译/文本生成算法优化，包括模型改进、数据增强、评估指标设计等。",
            "参与对话系统研发，包括意图识别、槽位填充、多轮对话管理等。",
        ],
        "interview_themes_pool": [
            ["BERT/GPT", "微调方法", "Prompt 设计"],
            ["信息抽取", "序列标注", "关系抽取"],
            ["生成模型", "解码策略", "评估指标"],
        ],
        "base_pass": 57,
        "base_risk": 43,
        "base_growth": 73,
    },
    # ========== 后端开发方向 ==========
    {
        "direction": "后端开发",
        "titles": [
            "后端开发实习生", "Python后端实习生", "Java后端实习生",
            "Go后端实习生", "服务端开发实习生", "分布式系统实习生"
        ],
        "companies": ["字节跳动", "阿里", "腾讯", "美团", "快手", "网易", "京东", "小米"],
        "cities": ["北京", "上海", "深圳", "杭州", "广州"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["Python", "Flask", "Django", "FastAPI", "MySQL", "Redis"],
            ["Java", "Spring Boot", "MyBatis", "MySQL", "Redis", "Kafka"],
            ["Go", "Gin", "Beego", "gRPC", "etcd", "Kubernetes"],
            ["微服务", "分布式系统", "负载均衡", "缓存", "消息队列"],
        ],
        "project_signals_pool": [
            ["后端", "API", "数据库"],
            ["微服务", "分布式", "缓存"],
            ["gRPC", "K8s", "容器化"],
        ],
        "jd_templates": [
            "负责后端服务设计与开发，包括 API 设计、数据库优化、缓存策略等。",
            "参与微服务架构升级，负责服务拆分、RPC 通信、服务治理等。",
            "负责系统性能优化，包括慢查询优化、缓存设计、异步处理等。",
        ],
        "interview_themes_pool": [
            ["数据结构", "算法", "系统设计"],
            ["MySQL 索引", "Redis 缓存", "消息队列"],
            ["微服务架构", "分布式一致性", "CAP 理论"],
        ],
        "base_pass": 65,
        "base_risk": 35,
        "base_growth": 68,
    },
    # ========== 前端开发方向 ==========
    {
        "direction": "前端开发",
        "titles": [
            "前端开发实习生", "React前端实习生", "Vue前端实习生",
            "大前端实习生", "跨端开发实习生", "UI开发实习生"
        ],
        "companies": ["字节跳动", "阿里", "腾讯", "美团", "快手", "网易", "百度"],
        "cities": ["北京", "上海", "深圳", "杭州", "广州"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["React", "Vue", "TypeScript", "Next.js", "Webpack", "Vite"],
            ["HTML", "CSS", "JavaScript", "ES6+", "Sass", "Less"],
            ["性能优化", "SSR", "SSG", "PWA", "Web Vitals"],
            ["跨端开发", "React Native", "Flutter", "Taro", "Uni-app"],
        ],
        "project_signals_pool": [
            ["React", "Vue", "组件化"],
            ["性能优化", "SSR", "PWA"],
            ["跨端", "移动端", "小程序"],
        ],
        "jd_templates": [
            "负责前端页面开发，包括组件设计、状态管理、性能优化等。",
            "参与前端工程化建设，包括构建优化、CI/CD、代码规范等。",
            "负责跨端方案落地，包括 React Native/Flutter 开发、性能调优等。",
        ],
        "interview_themes_pool": [
            ["React/Vue 原理", "虚拟DOM", "Diff算法"],
            ["前端性能优化", "Web Vitals", "缓存策略"],
            ["工程化", "Webpack/Vite", "CI/CD"],
        ],
        "base_pass": 68,
        "base_risk": 32,
        "base_growth": 65,
    },
    # ========== 数据工程方向 ==========
    {
        "direction": "数据工程",
        "titles": [
            "数据开发实习生", "数据仓库实习生", "ETL开发实习生",
            "数据平台实习生", "大数据开发实习生", "数据分析实习生"
        ],
        "companies": ["字节跳动", "阿里", "腾讯", "美团", "快手", "京东", "网易"],
        "cities": ["北京", "上海", "深圳", "杭州"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["SQL", "Hive", "Spark", "Hadoop", "数据仓库", "ETL"],
            ["Python", "Pandas", "NumPy", "数据清洗", "数据可视化"],
            ["Kafka", "Flink", "实时计算", "流处理", "消息队列"],
            ["Tableau", "Power BI", "数据可视化", "BI报表"],
        ],
        "project_signals_pool": [
            ["SQL", "Hive", "数据仓库"],
            ["Spark", "Flink", "实时计算"],
            ["数据清洗", "ETL", "数据质量"],
        ],
        "jd_templates": [
            "负责数据仓库建设，包括维度建模、ETL 开发、数据质量检测等。",
            "参与实时数据平台建设，包括流计算、消息队列、实时报表等。",
            "负责数据分析与可视化，包括 OLAP 分析、BI 报表、数据产品等。",
        ],
        "interview_themes_pool": [
            ["SQL 优化", "Hive 原理", "数据仓库建模"],
            ["Spark 原理", "Flink 流计算", "实时计算"],
            ["数据治理", "数据质量", "元数据管理"],
        ],
        "base_pass": 62,
        "base_risk": 38,
        "base_growth": 70,
    },
    # ========== 产品方向 ==========
    {
        "direction": "产品经理",
        "titles": [
            "产品经理实习生", "AI产品经理实习生", "数据产品经理实习生",
            "后台产品实习生", "策略产品实习生", "用户产品实习生"
        ],
        "companies": ["字节跳动", "阿里", "腾讯", "美团", "快手", "网易", "京东"],
        "cities": ["北京", "上海", "深圳", "杭州"],
        "stages": ["实习", "校招"],
        "skills_pool": [
            ["产品设计", "需求分析", "原型设计", "Axure", "Figma"],
            ["数据分析", "SQL", "AB测试", "用户调研", "竞品分析"],
            ["AI产品", "LLM应用", "Prompt Engineering", "AI产品设计"],
            ["项目管理", "敏捷开发", "PRD文档", "路线图规划"],
        ],
        "project_signals_pool": [
            ["产品", "需求", "原型"],
            ["数据分析", "AB测试"],
            ["AI", "LLM", "产品化"],
        ],
        "jd_templates": [
            "负责产品需求分析与设计，包括用户调研、竞品分析、原型设计、PRD 撰写等。",
            "参与数据驱动的产品迭代，包括数据分析、AB 测试、效果评估等。",
            "负责 AI 产品落地，包括 LLM 应用设计、Prompt 优化、效果评估等。",
        ],
        "interview_themes_pool": [
            ["产品思维", "需求分析", "竞品分析"],
            ["数据分析", "AB 测试", "指标设计"],
            ["AI 产品", "LLM 应用", "产品设计"],
        ],
        "base_pass": 70,
        "base_risk": 30,
        "base_growth": 60,
    },
]

def generate_jobs(target_count=200, output_path="data/jobs_expanded.json"):
    """生成目标数量的岗位"""
    
    # 先读取现有岗位（如果存在）
    existing_jobs = []
    if os.path.exists("data/jobs.json"):
        with open("data/jobs.json", "r", encoding="utf-8") as f:
            existing_jobs = json.load(f)
    
    if os.path.exists("data/public_jobs_sample.json"):
        with open("data/public_jobs_sample.json", "r", encoding="utf-8") as f:
            existing_jobs += json.load(f)
    
    print(f"[INFO] 已有岗位数: {len(existing_jobs)}")
    
    # 生成新岗位
    new_jobs = []
    job_id_counter = len(existing_jobs)
    
    while len(existing_jobs) + len(new_jobs) < target_count:
        # 随机选择一个方向模板
        template = random.choice(JOB_TEMPLATES)
        
        # 生成岗位
        job = {
            "id": f"expanded-{job_id_counter}",
            "title": random.choice(template["titles"]),
            "company": random.choice(template["companies"]),
            "city": random.choice(template["cities"]),
            "direction": template["direction"],
            "stage": random.choice(template["stages"]),
            "source": "synthetic",  # 标注来源
            "quality_score": random.randint(70, 95),  # 标注质量分
            "skills": random.choice(template["skills_pool"]),
            "project_signals": random.choice(template["project_signals_pool"]),
            "jd": random.choice(template["jd_templates"]),
            "interview_themes": random.choice(template["interview_themes_pool"]),
            # 评分加入随机扰动
            "pass_score": max(0, min(100, template["base_pass"] + random.randint(-10, 10))),
            "risk_score": max(0, min(100, template["base_risk"] + random.randint(-10, 10))),
            "growth_score": max(0, min(100, template["base_growth"] + random.randint(-10, 10))),
        }
        
        new_jobs.append(job)
        job_id_counter += 1
    
    # 合并
    all_jobs = existing_jobs + new_jobs
    
    # 保存
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 生成完成: {len(all_jobs)} 条岗位")
    print(f"  - 已有: {len(existing_jobs)} 条")
    print(f"  - 新增: {len(new_jobs)} 条")
    print(f"  - 保存至: {output_path}")
    
    # 统计方向分布
    direction_counts = {}
    for job in all_jobs:
        d = job.get("direction", "未知")
        direction_counts[d] = direction_counts.get(d, 0) + 1
    
    print(f"\n[INFO] 方向分布:")
    for d, count in sorted(direction_counts.items(), key=lambda x: -x[1]):
        print(f"  - {d}: {count} 条")
    
    return all_jobs

if __name__ == "__main__":
    generate_jobs(target_count=200)
