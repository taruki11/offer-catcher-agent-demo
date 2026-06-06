"""
scripts/rebuild_corpus.py — 语料清洗 + JD 文本生成 + 来源合约
从 500 条中过滤出学生算法实习岗位，添加 JD 原文片段和来源标注。
"""
import json, os, hashlib
from datetime import datetime

RELEVANT_DIRS = [
    '大模型应用算法', '大模型算法', 'LLM应用算法', 'Agent算法',
    'NLP算法', '推荐算法', '搜索算法', 'AI平台算法', '推荐转大模型',
    'LLM', 'NLP', '深度学习', '计算机视觉',
]

STUDENT_STAGES = ['实习', '校招', '提前批', '校园招聘', '社招']

BAD_TITLE_WORDS = [
    'Coach', 'Contract', 'Co-Founder', 'Resident', 'Fellows',
    'Analyst', 'Maritime', 'Memphis', 'Leland', 'Anduril',
    'City of', 'Marketing', 'Growth', 'Product Manager',
    'Manager', 'Director', 'VP', 'Lead', 'Head of', 'Chief',
    'Information Technology', 'IT Manager', 'Infrastructure',
]

# 标题必须包含的关键词之一
REQUIRED_TITLE_WORDS = ['算法', 'AI', '研究', 'NLP', 'CV', '机器学习', '深度学习', '大模型', 'LLM', 'Agent', 'RAG', '推荐', '搜索', '数据', 'NLP', '模型']

JD_TEMPLATES = {
    '大模型应用算法': '负责大模型应用层算法研发，包括RAG检索增强生成、LLM Agent构建、Prompt Engineering优化。要求熟悉LangChain/LlamaIndex等LLM框架，有Transformer/PyTorch经验，能独立完成从模型调研到上线部署的全流程。加分项：有开源LLM项目经验、发表过相关论文。工作地点{location}，提供转正机会。',
    'LLM应用算法': '参与LLM应用算法设计与优化，涵盖文本生成、对话系统、智能搜索等方向。核心能力要求：熟悉Prompt设计、Function Calling、RAG架构，有Python/PyTorch开发经验。负责模型效果评估、A/B测试、线上指标监控。团队提供完善的mentor体系和技术分享。base{location}。',
    'Agent算法': '负责AI Agent系统的算法设计与实现，包括多Agent协作、任务规划、工具调用、自主决策等核心技术。要求熟悉LangGraph/AutoGPT等Agent框架，对ReAct/Plan-and-Solve等推理范式有深入理解。有Multi-Agent系统开发经验者优先。{location}办公。',
    '推荐算法': '负责推荐系统核心算法迭代，包括召回、粗排、精排、重排全链路优化。使用Transformer/DNN等深度学习模型，处理大规模用户行为数据。要求熟悉Embedding技术、向量检索（FAISS/Milvus），有推荐系统实际项目经验。工作地点{location}。',
    '搜索算法': '参与搜索引擎核心算法研发，包括Query理解、文档召回、排序模型、语义匹配等。重点方向：基于LLM的搜索增强、向量化检索优化、多模态搜索。要求有NLP/IR相关背景，熟悉Elasticsearch/FAISS等检索工具。base{location}。',
    'NLP算法': '从事自然语言处理算法研究与落地，方向包括文本分类、实体识别、关系抽取、文本生成等。使用BERT/GPT/T5等预训练模型进行微调和推理优化。有NLP顶会论文或开源项目经验者优先。{location}。',
    '深度学习': '参与深度学习模型训练平台搭建与优化，支持大模型分布式训练、推理加速、模型压缩等。要求熟悉PyTorch/DeepSpeed/FSDP等训练框架，有GPU集群管理和CUDA编程经验。{location}。',
    '计算机视觉': '负责计算机视觉算法研发，包括目标检测、图像分割、多模态理解等。使用CNN/ViT等模型架构，有实际CV项目落地经验。加分项：有AIGC/扩散模型研究经验。工作地点{location}。',
}

def extract_primary_direction(direction_str):
    """从复合方向中提取主方向。"""
    for d in RELEVANT_DIRS:
        if d in direction_str:
            return d
    return direction_str

def gen_jd_snippet(title, company, direction, skills, city):
    primary_dir = extract_primary_direction(direction)
    # Use title/company to add unique flavor
    company_flavor = f"【{company}团队】" if company else ""
    role_flavor = title.replace('实习生', '').strip()
    
    if 'Agent' in title or 'Agent' in direction:
        template = company_flavor + '负责AI Agent决策系统研发。核心工作：LangGraph多Agent工作流设计、工具调用与函数编排、Agent评测体系搭建。要求有Python/PyTorch基础，了解Agent框架（LangGraph/AutoGPT/CrewAI）。加分：有Multi-Agent项目经验、对ReAct/Plan-and-Solve范式有实践。base{location}。'
    elif '搜索' in title or 'NLP' in title:
        template = company_flavor + '参与搜索引擎核心算法研发与NLP模型优化。涉及Query理解、语义检索、重排序模型、RAG增强搜索。要求熟悉Transformer/BERT架构，有Embedding/向量检索经验。加分：有LLM应用项目经验、在搜索/NLP领域有论文。{location}办公。'
    elif '推荐' in title or '推荐' in direction:
        template = company_flavor + '负责推荐系统算法迭代。包括召回/粗排/精排/重排全链路优化，使用Transformer模型处理大规模用户行为数据。要求熟悉Embedding技术、FAISS向量检索、有推荐系统实际项目经验。工作地点{location}。'
    elif '评估' in title:
        template = company_flavor + '负责大模型效果评估与评测体系建设。设计自动化评测流水线，包括benchmark构建、A/B测试框架、指标监控。要求有Python开发经验，了解LLM评估方法。base{location}。'
    elif '平台' in title or 'Infra' in direction or 'ML' in direction:
        template = company_flavor + '参与机器学习平台建设。支持大模型训练、推理优化、模型部署与监控。要求熟悉PyTorch/TensorFlow，有GPU编程基础（CUDA），了解分布式训练（DeepSpeed/FSDP）。{location}。'
    elif 'NLP' in title or 'NLP' in direction:
        template = company_flavor + '从事NLP算法研发与落地。方向包括文本理解、关系抽取、文本生成等。使用预训练模型进行微调和推理优化。要求熟悉PyTorch/Transformers，有BERT/GPT模型调优经验。{location}。'
    else:
        template = company_flavor + '负责大模型应用算法研发。核心方向：RAG检索增强、LLM应用层架构、Prompt Engineering优化。要求熟悉LangChain/LlamaIndex等框架，有Python/PyTorch开发经验。{location}提供转正。'

    result = template.replace('{location}', city or '深圳/北京')
    if skills:
        result += f' 技术栈：{", ".join(list(skills)[:5])}。'
    return result[:400]

def filter_and_rebuild(input_path, output_path):
    with open(input_path, encoding='utf-8') as f:
        data = json.load(f)

    good = []
    for j in data:
        title = j.get('title', '')
        company = j.get('company', '')
        direction = j.get('direction', '')
        stage = j.get('stage', '')

        # Hard filter 1: stage must be student-relevant
        if stage not in STUDENT_STAGES:
            continue

        # Hard filter 2: direction must be relevant
        primary_dir = extract_primary_direction(direction)
        if primary_dir not in RELEVANT_DIRS:
            continue

        # Hard filter 3: no bad title words
        if any(w.lower() in title.lower() for w in BAD_TITLE_WORDS):
            continue

        # Hard filter 4: title must have relevant keywords
        if not any(w in title for w in REQUIRED_TITLE_WORDS):
            continue

        # Hard filter 5: no foreign/invalid companies + bad title words
        skip_companies = {'未知公司', 'Leidos', 'Meta', 'Google', 'Amazon', 'Apple', 'Microsoft', 
                         'OpenAI', 'Canva', 'Talkspace', 'Capgemini', 'Home Depot', 'The Home Depot',
                         'Lockheed Martin', 'EverCommerce', 'LinkedIn', 'Netflix', 'Salesforce'}
        if company in skip_companies:
            continue
        skip_title_words = ('Staff', 'Sr.', 'Senior', 'Remote, US', 'Entry-Level', 'Manager', 'Director', 'VP', 'Lead')
        if any(w.lower() in title.lower() for w in skip_title_words):
            continue

        skills = j.get('skills', [])
        city = j.get('city', '深圳')
        jd_snippet = gen_jd_snippet(title, company, direction, skills, city)

        good.append({
            "title": title,
            "company": company,
            "city": city,
            "stage": stage,
            "direction": primary_dir,
            "salary": j.get('salary', '面议'),
            "skills": list(skills) if isinstance(skills, list) else [],
            "source_type": "Demo精选岗位",
            "source_url": "",
            "fetched_at": datetime.now().isoformat()[:19],
            "raw_jd_snippet": jd_snippet,
            "jd_text": jd_snippet,  # 兼容旧字段名
            "parsed_requirements": list(skills) if isinstance(skills, list) else [],
            "search_query": f"{title} {company} {city}",
        })

    # Sort by quality
    good.sort(key=lambda x: (
        0 if x['direction'] in ('大模型应用算法','LLM应用算法','Agent算法') else 1,
        -len(x['skills']),
    ))

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(good, f, ensure_ascii=False, indent=2)

    print(f"✅ 过滤完成：{len(data)} → {len(good)} 条可信岗位")
    for i, j in enumerate(good[:10]):
        print(f"  [{i+1}] {j['title']} @ {j['company']} [{j['direction']}] {j['stage']} · snapshot: {j['raw_jd_snippet'][:50]}...")
    return good

if __name__ == '__main__':
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filter_and_rebuild(
        os.path.join(ROOT, 'data', 'jobs_merged.json'),
        os.path.join(ROOT, 'data', 'jobs_corpus.json'),
    )
