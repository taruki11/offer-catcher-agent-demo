import sys, os
sys.path.insert(0, os.path.abspath('.'))
from pathlib import Path

from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.conversion import attach_conversion_scores

# 模拟 case_13
resume_text = "赵同学 | 电子信息 | 2026 届硕士\n技能：Python、PyTorch、OpenCV、YOLO、目标检测、图像分类、模型部署、TensorRT。\n项目：1. 基于 YOLO-v8 的工业缺陷检测：自制数据集 mAP@0.5=89.2%。2. ResNet 作物病害识别：PlantVillage 准确率 94.7%。3. 模型边缘部署：使用 TensorRT 优化 YOLO 推理速度，FPS 从 15 提升到 45。"

profile = parse_resume(resume_text)
profile['_city'] = '上海'
profile['_stage'] = '实习'
profile['_target_role'] = '大模型应用算法'

print('profile:', profile)

scored = rank_jobs(
    resume_text=resume_text,
    profile=profile,
    target_role='大模型应用算法',
    target_city='上海',
    stage='实习',
    top_k=3,
    jobs_path=Path('data/jobs.json')
)

for j in scored[:3]:
    print('Title:', j['title'])
    print('  pass_score:', j.get('pass_score'))
    print('  risk_score:', j.get('risk_score'))
    print('  growth_score:', j.get('growth_score'))
    print('  action would be based on these values')
    print()
