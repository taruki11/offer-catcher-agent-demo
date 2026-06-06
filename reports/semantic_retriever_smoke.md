# Semantic Retriever Smoke Test Report

**Model**: `sentence-transformers/all-MiniLM-L6-v2` or `SEMANTIC_MODEL_PATH` override

**Mode**: read-only cached embedding model + FAISS, no LLM API, no training.

| Case | Expected Top1 Contains | Actual Top1 | Score | Status |
|------|------------------------|-------------|-------|--------|
| llm_rag_agent | 大模型应用算法实习生 / 大模型算法实习生 | 大模型算法实习生 | 0.8244 | PASS |
| recommendation | 推荐系统工程师 | 推荐系统工程师 | 0.7038 | PASS |
| computer_vision | 计算机视觉算法实习生 | 计算机视觉算法实习生（检测方向） | 0.7017 | PASS |

## Top5 Details

### llm_rag_agent
- 1. 大模型算法实习生 (0.8244)
- 2. 大模型应用算法实习生 (0.7878)
- 3. 大模型 Agent 应用实习生 (0.6902)
- 4. 大模型评估算法实习生 (0.6718)
- 5. 游戏 AI 算法实习生 (0.6640)

### recommendation
- 1. 推荐系统工程师 (0.7038)
- 2. 推荐算法实习生 (0.6408)
- 3. 搜索推荐算法工程师 (0.5444)
- 4. 推荐数据分析实习生 (0.5304)
- 5. LLM 推荐算法实习生 (0.5169)

### computer_vision
- 1. 计算机视觉算法实习生（检测方向） (0.7017)
- 2. 图像识别算法实习生 (0.6937)
- 3. Computer Vision Engineer (0.4498)
