#!/bin/bash
# Local CI Pipeline Test Runner Script (TICKET-901)
set -e

echo "========================================================"
echo "🚀 STAGE 1: Backend Unit & Integration Tests (Pytest)"
echo "========================================================"
./.venv/bin/pytest -v

echo ""
echo "========================================================"
echo "🚀 STAGE 2: OpenAPI-to-TypeScript Generation Check"
echo "========================================================"
PYTHONPATH=. ./.venv/bin/python scripts/generate_types.py

echo ""
echo "========================================================"
echo "🚀 STAGE 3: Frontend TypeCheck & Vite Production Build"
echo "========================================================"
cd frontend
npm run build

echo ""
echo "========================================================"
echo "✅ CI PIPELINE EXECUTED SUCCESSFULLY WITH 0 ERRORS!"
echo "========================================================"
