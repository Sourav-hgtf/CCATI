# Backend Component — Telecom Churn Platform

FastAPI REST service layer handling routing, RBAC permissions, PII masking, and DB interactions.

## Directory Structure
- `app/api/v1/` — Endpoint controllers (`health`, `customers`, `segments`, `models`, `scoring`, `export`, `admin`)
- `app/core/` — Security, JWT auth, RBAC dependency guards, audit logging, config
- `app/schemas/` — Pydantic request/response models
- `app/services/` — Orchestration services between REST API, ML Engine, and Business Engine
- `app/main.py` — FastAPI application entry point

## Commands
- `python -m uvicorn backend.app.main:app --reload` — Launch FastAPI dev server on port 8000
