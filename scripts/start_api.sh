#!/bin/sh
# Startup script for the FastAPI service on Render.
# The pre-seeded data (data/issues.db, data/chroma/) is baked into the Docker image,
# so no seed step is needed here.
set -e

exec uvicorn material_quality_agent.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}"
