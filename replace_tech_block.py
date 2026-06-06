import pathlib

fp = pathlib.Path(r"D:\Pycharm_workplace\Offer 捕手：基于 LLM Agent 的学生岗位匹配与简历优化系统\app.py")
content = fp.read_text(encoding="utf-8")

old_start = '        # ---- 技术选型说明（底部折叠）----'
old_end = '            st.markdown("""\n**当前系统没有盲目微调'

idx_start = content.find(old_start)
idx_end = content.find(old_end)

if idx_start == -1:
    print(f"❌ 未找到 old_start，尝试查找相似内容")
    for marker in ["技术选型说明", "底部折叠", "为什么这样做"]:
        i = content.find(marker)
        if i >= 0:
            print(f"  找到 '{marker}' 位置：{i}")
            print(f"  上下文：{repr(content[max(0,i-50):i+100])}")
    exit(1)

if idx_end == -1:
    print(f"❌ 未找到 old_end")
    exit(1)

# 找到旧块的结束位置（下一个 st. 或文件末尾）
rest_idx = content.find("\n        st.", idx_end)
if rest_idx == -1:
    rest_idx = len(content)

old_block = content[idx_start:rest_idx]
print(f"✅ 找到旧块，长度：{len(old_block)} 字符")
print(f"旧块开头：{repr(old_block[:100])}")

new_block = '''        # ---- 技术选型说明（底部折叠，算法视角）----
        with st.expander("📖 技术选型说明（算法视角）", expanded=False):
            st.markdown("""
**项目定位：基于多 Agent 协作的大模型应用算法系统**（不是商业 HR 工具）。

---

### 一、多 Agent 如何分工

| Agent | 职责 | LLM 是否参与 |
|---|---|---|
| Profile Builder | 简历 → 结构化画像 | 可选（理解非结构化文本） |
| JD Intelligence | JD → 结构化岗位画像 | 可选（归一化技能表述） |
| Opportunity Scout | 关键词/TF-IDF 召回候选池 | 否（保证稳定可解释） |
| Application Ranker | 多维度加权公式计算排序 | 否（**排序必须可解释**） |
| Gap Diagnosis | 规则检测能力缺口 | 可选（生成可读解释） |
| Resume Conversion | 规则约束的简历改写 | 可选（语言优化） |
| Strategy Planner | 规则策略 + 自然语言总结 | 可选（总结生成） |

**核心设计：LLM 是"可选增强层"，非依赖项。无 API Key 时所有 Agent 仍可完整运行。**

---

### 二、为什么排序/决策用可解释公式，而不是黑盒 LLM 打分？

1. **可解释性约束**：面试官/用户需要知道"为什么推荐这个岗位"，黑盒 LLM 打分无法回答
2. **权重可调试**：`ApplyPriority = 0.40×Match + 0.30×Pass - 0.15×Risk + 0.15×Growth`，每个权重都有业务含义
3. **稳定性**：LLM API 可能抖动，排序公式稳定可复现
4. **数据效率**：公式不需要标注数据，LLM 微调才需要

---

### 三、为什么当前不做微调？

| 原因 | 说明 |
|---|---|
| 没有真实标注数据 | 需要"简历 → JD → 初筛结果"的大规模标注，当前没有 |
| 没有 HR 评价偏好数据 | PassScore 的核心是"这位 HR 会筛掉哪些简历"，需要企业级数据 |
| 样本量不足 | 当前 30-80 条岗位数据远不够做可靠微调 |
| 硬做容易变成伪实验 | 数据不足时微调，结果不可复现、不可解释 |

**正确做法（算法演进路径）：**
1. 当前：LLM structured output + 可解释公式 + 小型岗位库验证
2. 后续若有真实投递反馈：训练 **PassScore 预测模型**（XGBoost/LightGBM 或微调分类器）
3. 后续若有 HR 反馈：做 **简历改写偏好优化**（RLHF 方向）

---

### 四、与已有项目 `llm_for_rec_agent` 的区分

| 项目 | 证明的能力 |
|---|---|
| `llm_for_rec_agent` | RAG、检索、SFT/DPO、幻觉评估（**技术深度**） |
| `Offer 捕手` | 多 Agent 协作、可解释排序、决策闭环（**算法落地能力**） |

**一句话区分**：前者证明你会做 RAG/Agent 技术系统；后者证明你能把 Agent 技术做成可解释的决策算法系统。

---

### 五、未来演进方向

```
当前（Demo 验证，算法框架搭建）
  → 接入校招官网 JD（扩大岗位库，提升召回覆盖率）
  → 接入学生投递反馈（优化 ApplyPriority 权重，数据驱动）
  → 训练 PassScore 预测模型（XGBoost/LightGBM 或微调分类器）
  → 简历改写偏好优化（获得 HR 反馈后做 RLHF 方向）
```

**商业闭环是落地价值补充，不是主线。** 主叙事仍然是"基于多 Agent 协作的大模型应用算法系统"。
""")

'''

new_content = content[:idx_start] + new_block + content[rest_idx:]
fp.write_text(new_content, encoding="utf-8")
print(f"✅ 替换完成！旧块长度：{len(old_block)}，新块长度：{len(new_block)}")
print(f"文件总行数：{len(new_content.splitlines())}")
