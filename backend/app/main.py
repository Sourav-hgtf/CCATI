import json
import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1 import admin, analytics, auth, customers, export, health, models, scoring, segments
from backend.app.core.config import settings

logger = logging.getLogger("telecom_churn_backend")
logger.setLevel(logging.INFO)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_logging_middleware(request: Request, call_next):
    """TICKET-904: Observability middleware adding X-Correlation-ID header & duration tracking."""
    correlation_id = request.headers.get("X-Correlation-ID", f"corr-{uuid.uuid4().hex[:10]}")
    start_time = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time-MS"] = str(duration_ms)

    log_entry = {
        "correlation_id": correlation_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }
    logger.info(json.dumps(log_entry))

    return response

# Include Routers
app.include_router(health.router, tags=["Health"])
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Auth"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])
app.include_router(customers.router, prefix=settings.API_V1_STR, tags=["Customers"])
app.include_router(segments.router, prefix=settings.API_V1_STR, tags=["Segments"])
app.include_router(models.router, prefix=settings.API_V1_STR, tags=["Model Monitoring"])
app.include_router(scoring.router, prefix=settings.API_V1_STR, tags=["Scoring Jobs"])
app.include_router(export.router, prefix=settings.API_V1_STR, tags=["Data Export"])
app.include_router(admin.router, prefix=settings.API_V1_STR, tags=["Admin"])


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
