FROM python:3.11-slim

# Build-time system deps for sentence-transformers (gcc needed for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv --no-cache-dir

WORKDIR /app

# ── Dependency layer (cached unless pyproject.toml / uv.lock changes) ──
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Activate venv for subsequent RUN / CMD
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Pin the Hugging Face cache inside the image so the model survives
ENV HF_HOME="/app/.cache/huggingface"

# ── Pre-download the embedding model (baked into the image layer) ──
# This avoids a ~460 MB download on every cold start.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# ── Application code + pre-seeded data ──
COPY src/      ./src/
COPY scripts/  ./scripts/
COPY data/     ./data/
COPY ui/       ./ui/

# Make startup scripts executable
RUN chmod +x scripts/start_api.sh scripts/start_ui.sh

EXPOSE 8000
