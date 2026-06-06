# Error Analysis (v2: Match/Priority split)

Generated: 2026-06-06 01:36:32

## Error Ranking

[OK] No errors.

## Root Cause: Matcher vs Label

- Pass rate: 8/8 (100.0%)
- Match Top1 Acc: 100.0%
- Priority Top1 Acc: 100.0%

## E4 Recall Miss Analysis

[OK] No recall issues.

## E5 Rank Misorder Analysis

[OK] No rank issues.

## Case_02 (Recommendation Algorithm) Analysis

- Expected: ['推荐算法实习生']
- Match Top1: 推荐算法实习生
- Match Top5: ['推荐算法实习生', 'LLM 推荐算法实习生', '推荐算法实习生-头条', '推荐数据分析实习生', '校招人岗匹配算法实习生']
- Errors: none
- [OK] No recall/rank issues for case_02 after fixing job title alignment.

## Case_03/08 (NLP/CV -> LLM Transfer) Analysis

**case_03**: Errors=none, Match Top1=NLP 大模型实习生, Priority Top1=NLP 大模型实习生
**case_08**: Errors=none, Match Top1=大模型应用算法实习生, Priority Top1=计算机视觉算法实习生（检测方向）

**Diagnosis:**
- case_03 (NLP -> LLM): Has NLP fundamentals but missing RAG/Agent skills. match_score may be reasonable but mismatched roles could rank higher.
- case_08 (CV -> LLM): No LLM skills at all. Expected labels are empty (no good match). If system still suggests an LLM role, it means the ranking is over-optimistic for untransferable skill sets.
- **Recommendation**: Adjust GrowthScore/RiskScore to reflect transfer difficulty more aggressively for case_08.

## Next Steps

1. If E5_MATCH errors persist: tune SKILL_KEYWORDS or match weight in matcher.py
2. If E5_PRIORITY errors persist: review whether expected_top_priorities should be about pure match (then fix labels) or risk-adjusted priority (then matcher is correct)
3. Expand jobs.json with more diverse roles (pure rec, pure CV) to test edge cases better
4. Add more golden cases for transfer-learning scenarios (X background -> LLM role)
