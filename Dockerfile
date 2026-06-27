FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -e .

# Pre-download non-gated models so the container starts without network access
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
RUN python -m spacy download en_core_web_sm

EXPOSE 8000

# Gated models (Gemma) are loaded at runtime from the mounted HF cache:
#   docker run -v $HOME/.cache/huggingface:/root/.cache/huggingface -e HF_TOKEN taggly
CMD ["taggly", "start"]
