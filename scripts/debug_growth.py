import json, sys, os
sys.path.insert(0, os.path.abspath('.'))
from pathlib import Path

from src.resume_parser import parse_resume
from src.matcher import rank_jobs
from src.conversion import attach_conversion_scores, calc_growth_score

# 用 case_13 测试
case_text = "赵同学 | 电子信息 | 2026 届硕士\n技能：Python、PyTorch、OpenCV、YOLO、目标检测、图像分类、模型部署、TensorRT。\n项目：1. 基于 YOLO-v8 的工业缺陷检测：自制数据集 mAP@0.5=89.2%。2. ResNet 作物病害识别：PlantVillage 准确率 94.7%。3. 模型边缘部署：使用 TensorRT 优化 YOLO 推理速度，FPS 从 15 提升到 45。"

profile = parse_resume(case_text)
profile['_city'] = '上海'
profile['_stage'] = '实习'
profile['_target_role'] = '大模型应用算法'

print('profile has_llm_project:', profile.get('has_llm_project'))
print('profile has_metrics:', profile.get('has_metrics'))

# 手动测试 attach_conversion_scores
test_job = {
    "title": "计算机视觉算法实习生（检测方向）",
    "company": "测试",
    "skills": ["Python", "PyTorch", "OpenCV", "YOLO"],
    "project_signals": ["检测", "分类"],
    "direction": "计算机视觉",
    "stage": "实习",
    "city": "上海",
    "jd": "CV 检测岗位",
}

result = attach_conversion_scores(
    profile=profile,
    job=test_job,
    resume_text=case_text,
    target_role='大模型应用算法',
    target_city='上海',
    stage='实习',
)
print('attach_conversion_scores result:')
print('  pass_score:', result.get('pass_score'))
print('  risk_score:', result.get('risk_score'))
print('  growth_score:', result.get('growth_score'))
print('  keyword_coverage:', result.get('keyword_coverage'))

# 再测试 calc_growth_score 直接调用
gs = calc_growth_score(profile, test_job)
print('calc_growth_score direct result:', gs)
