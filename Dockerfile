FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    ENABLE_EMBEDDING_CLIENT=0 \
    ENABLE_LOCAL_SEMANTIC_MATCHER=0 \
    SEMANTIC_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2 \
    HF_HOME=/home/user/.cache/huggingface \
    TRANSFORMERS_CACHE=/home/user/.cache/huggingface/transformers \
    SENTENCE_TRANSFORMERS_HOME=/home/user/.cache/huggingface/sentence-transformers

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 user

COPY requirements-public.txt /app/requirements-public.txt
RUN pip install --upgrade pip \
    && pip install -r /app/requirements-public.txt

COPY --chown=user:user app.py README.md requirements.txt /app/
COPY --chown=user:user src /app/src
COPY --chown=user:user data /app/data
COPY --chown=user:user scripts /app/scripts

RUN mkdir -p /home/user/.cache/huggingface /app/reports \
    && chown -R user:user /home/user /app

USER user

# Do NOT pre-cache models during build — HF abuse-handler flags downloads.
# Semantic model will be loaded at runtime if ENABLE_SEMANTIC=1 and network allows.
# With HF_HUB_OFFLINE=1 the model must be pre-cached manually via build args.

EXPOSE 7860

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=7860", "--server.headless=true", "--browser.gatherUsageStats=false"]
# v2 rebuild trigger 1780739629
