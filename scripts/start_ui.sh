#!/bin/sh
# Startup script for the Streamlit UI service on Render.
set -e

exec streamlit run ui/app.py \
    --server.port "${PORT:-8501}" \
    --server.address 0.0.0.0 \
    --server.headless true
