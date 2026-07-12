# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch first so pip never pulls the multi-GB CUDA build
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies from project metadata alone so this layer survives source changes
COPY pyproject.toml .
RUN python -c "import tomllib; [print(d) for d in tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']]" > deps.txt \
    && pip install --no-cache-dir -r deps.txt && rm deps.txt

# Pre-download models so the container serves without network access; the build fails if any
# are unavailable. All bundled models are public — the hf_token build secret is optional and
# only raises rate limits: docker build --secret id=hf_token,env=HF_TOKEN .
RUN --mount=type=secret,id=hf_token \
    if [ -s /run/secrets/hf_token ]; then export HF_TOKEN=$(cat /run/secrets/hf_token); fi \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" \
    && python -c "from huggingface_hub import snapshot_download; snapshot_download('HuggingFaceTB/SmolLM2-135M-Instruct', allow_patterns=['*.json', '*.txt', '*.safetensors'])"
RUN python -m spacy download en_core_web_lg

COPY . .
RUN pip install --no-cache-dir --no-deps -e . \
    && cp config/docker.yaml config/config.yaml

# Bind all interfaces so the published port is reachable; warm up only token-free commands —
# the bundled SmolLM2 model used by desc/ext loads on first request without a token.
# HF_HUB_OFFLINE serves the bundled models without probing huggingface.co; override with
# -e HF_HUB_OFFLINE=0 to download other models at runtime.
ENV HOST=0.0.0.0
ENV WARMUP='["keys", "score"]'
ENV HF_HUB_OFFLINE=1

EXPOSE 8000

# Gated models (Gemma) are loaded at runtime from a mounted HF cache and token:
#   docker run -p 8000:8000 -v $HOME/.cache/huggingface:/root/.cache/huggingface -e HF_TOKEN taggly
CMD ["taggly", "start"]
