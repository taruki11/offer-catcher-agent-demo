# Offer 捕手公网部署方案：Hugging Face Docker Space

目标：生成一个长期可访问的公网 Demo 链接，用于比赛提交。不要提交 `127.0.0.1`、3060 内网 IP、SSH 隧道或任何临时链接。

## 推荐方案

使用 Hugging Face Spaces 的 Docker Space：

- 公网 URL 稳定，适合比赛提交。
- 不依赖本机、3060、SSH 会话或校园网端口。
- 项目已提供 `Dockerfile` 和 `requirements-public.txt`。
- 公网版使用 CPU 托管；语义召回使用 `sentence-transformers/all-MiniLM-L6-v2 + FAISS`，不读取 3060 上任何旧模型或微调权重。

## 文件清单

必须上传到 Space 仓库：

```text
Dockerfile
requirements-public.txt
app.py
README.md
src/
data/
prompts/
eval/
reports/
```

不要上传：

```text
.env
.streamlit/secrets.toml
*.log
本地隧道工具
streamlit_3060_tunnel.*.log
```

## 创建 Space

1. 打开 Hugging Face，创建 New Space。
2. Space SDK 选择 `Docker`。
3. Visibility 建议先选 `Public`，方便评委访问。
4. Space 名建议：`offer-catcher-agent`。

创建后，把本项目文件推送到 Space 仓库。

## 配置 API Key（可选）

Demo 无 API Key 也能完整运行规则版流程。若要启用 LLM 解析增强，不要把 key 写进代码或 `.env`，在 Space 的 Settings -> Variables and secrets 中添加：

```text
LLM_PROVIDER=deepseek
LLM_API_KEY=<set-in-space-secrets>
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

没有 key 时，系统会自动 fallback 到规则版解析。

## 验收标准

Space Build 完成后，打开公网链接并检查：

```text
1. 首页能打开
2. 粘贴简历后能生成岗位推荐
3. 岗位详情能展开证据链
4. Eval 诊断面板能展示指标
5. 语义召回面板不报错
```

公网 URL 形态一般是：

```text
https://huggingface.co/spaces/<你的用户名>/offer-catcher-agent
https://<你的用户名>-offer-catcher-agent.hf.space
```

提交比赛时优先填写 `*.hf.space` 这个可直接打开的运行链接。

## 备选方案

Streamlit Community Cloud 也可以部署，但需要 GitHub 仓库，并且对大模型依赖和缓存控制不如 Docker Space 自由。

临时隧道只适合现场演示，不建议作为最终提交链接，因为它依赖本机或 3060 持续在线。
