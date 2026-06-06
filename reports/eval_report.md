# Eval Report (v2: Match/Priority split)

Generated: 2026-06-06 01:36:32

## Summary

| Metric | Value |
|---|---|
| Eval split | core |
| Total cases | 8 |
| Pass cases | 8 |
| Pass rate | 100.0% |
| Match Top1 Acc | 100.0% |
| Priority Top1 Acc | 100.0% |
| Action Acc | 100.0% |
| Match Recall@5 | 100.0% |
| Priority Recall@5 | 100.0% |

## Per-Case Results

### Case 1: case_01

- Target: 大模型应用算法 | City: 深圳 | Stage: 实习
- Match Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Priority Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Action: actual=立即投递, expected=立即投递
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 2: case_02

- Target: 推荐算法 | City: 北京 | Stage: 实习
- Match Top1: 推荐算法实习生 | Expected: ['推荐算法实习生']
- Priority Top1: 推荐算法实习生 | Expected: ['推荐算法实习生']
- Action: actual=先优化再投, expected=先优化再投
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 3: case_03

- Target: 大模型应用算法 | City: 上海 | Stage: 实习
- Match Top1: NLP 大模型实习生 | Expected: ['NLP 大模型实习生']
- Priority Top1: NLP 大模型实习生 | Expected: ['NLP 大模型实习生']
- Action: actual=先优化再投, expected=先优化再投
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 4: case_04

- Target: 大模型应用算法 | City: 杭州 | Stage: 实习
- Match Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Priority Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Action: actual=先优化再投, expected=先优化再投
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 5: case_05

- Target: 大模型应用算法 | City: 成都 | Stage: 实习
- Match Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Priority Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Action: actual=冲刺岗位, expected=冲刺岗位
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 6: case_06

- Target: 大模型应用算法 | City: 深圳 | Stage: 实习
- Match Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Priority Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Action: actual=先优化再投, expected=先优化再投
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 7: case_07

- Target: 大模型应用算法 | City: 北京 | Stage: 实习
- Match Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生']
- Priority Top1: 大模型应用算法实习生 | Expected: ['大模型应用算法实习生', '大模型 Agent 应用实习生']
- Action: actual=冲刺岗位, expected=冲刺岗位
- Match Top1 Hit: True | Priority Top1 Hit: True
- Errors(0): none

### Case 8: case_08

- Target: 大模型应用算法 | City: 广州 | Stage: 实习
- Match Top1: 大模型应用算法实习生 | Expected: []
- Priority Top1: 计算机视觉算法实习生（检测方向） | Expected: []
- Action: actual=暂缓, expected=暂缓
- Match Top1 Hit: None | Priority Top1 Hit: None
- Errors(0): none
