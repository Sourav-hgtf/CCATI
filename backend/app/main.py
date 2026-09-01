"""FastAPI Application Entry Point (TASK 10 Production Hardened, TASK 12 Observability)."""

import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.app.api.v1 import (
    admin, analytics, auth, customers, data_quality,
    export, health, models, observability, scoring, segments,
)
from backend.app.core.config import settings
from backend.app.core.logger import get_logger
from backend.app.core.metrics import metrics_collector

# Structured logger for the application entry point
logger = get_logger("telecom_churn.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/openapi.json" if settings.APP_ENV != "production" or settings.DEBUG else None,
    docs_url="/docs" if settings.APP_ENV != "production" or settings.DEBUG else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" or settings.DEBUG else None,
)

# Configure CORS with environment-driven origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "X-Request-ID", "X-Process-Time-MS"],
)


@app.middleware("http")
async def security_and_observability_middleware(request: Request, call_next):
    """Production Security Headers, Request Correlation & Metrics Tracking Middleware (TASK 10/12)."""
    correlation_id = (
        request.headers.get(settings.REQUEST_ID_HEADER)
        or request.headers.get("X-Correlation-ID")
        or f"req-{uuid.uuid4().hex[:12]}"
    )
    start_time = time.time()

    # Payload size protection
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.MAX_REQUEST_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": f"Request payload exceeds maximum allowed limit of {settings.MAX_REQUEST_SIZE_BYTES // (1024 * 1024)}MB.",
                    "request_id": correlation_id,
                }
            },
        )

    response = await call_next(request)

    duration_ms = round((time.time() - start_time) * 1000, 2)
    is_error = response.status_code >= 400

    # ── Operational Metrics (TASK 12) ────────────────────────────────────────
    if settings.ENABLE_METRICS:
        metrics_collector.inc("api_requests_total")
        metrics_collector.observe("api_latency_ms", duration_ms)
        metrics_collector.inc_endpoint(request.url.path, is_error=is_error)
        if is_error:
            metrics_collector.inc("api_errors_total")

    # Correlation and Timing Headers
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Request-ID"] = correlation_id
    response.headers["X-Process-Time-MS"] = str(duration_ms)

    # Security Headers (OWASP Recommended)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

    # HSTS for production or when enabled
    if settings.ENABLE_HSTS or settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Cache-Control on API responses containing potentially sensitive subscriber data
    if request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"

    # Structured access log — no PII, no secrets
    logger.info(
        "request_handled",
        extra={
            "request_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


# Standardized Exception Handlers (no internal stack traces exposed to client)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    correlation_id = request.headers.get(settings.REQUEST_ID_HEADER, f"err-{uuid.uuid4().hex[:8]}")
    error_code = f"HTTP_{exc.status_code}"
    if exc.status_code == 429:
        error_code = "RATE_LIMIT_EXCEEDED"
    elif exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
    elif exc.status_code == 404:
        error_code = "HTTP_404"

    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = correlation_id
    headers["X-Correlation-ID"] = correlation_id

    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "detail": exc.detail if isinstance(exc.detail, (str, dict, list)) else str(exc.detail),
            "error": {
                "code": error_code,
                "message": exc.detail if isinstance(exc.detail, str) else "Request error",
                "request_id": correlation_id,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = request.headers.get(settings.REQUEST_ID_HEADER, f"val-{uuid.uuid4().hex[:8]}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        headers={"X-Request-ID": correlation_id, "X-Correlation-ID": correlation_id},
        content={
            "detail": exc.errors(),
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters or payload structure.",
                "request_id": correlation_id,
            },
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    correlation_id = request.headers.get(settings.REQUEST_ID_HEADER, f"exc-{uuid.uuid4().hex[:8]}")
    logger.error(
        "unhandled_exception",
        extra={
            "request_id": correlation_id,
            "path": request.url.path,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers={"X-Request-ID": correlation_id, "X-Correlation-ID": correlation_id},
        content={
            "detail": "An internal server error occurred.",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please reference the request ID when reporting this issue.",
                "request_id": correlation_id,
            },
        },
    )



# Include Routers
app.include_router(health.router, tags=["Health"])
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Auth"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])
app.include_router(customers.router, prefix=settings.API_V1_STR, tags=["Customers"])
app.include_router(segments.router, prefix=settings.API_V1_STR, tags=["Segments"])
app.include_router(models.router, prefix=settings.API_V1_STR, tags=["Model Monitoring"])
app.include_router(data_quality.router, prefix=settings.API_V1_STR, tags=["Data Quality"])
app.include_router(scoring.router, prefix=settings.API_V1_STR, tags=["Scoring Jobs"])
app.include_router(export.router, prefix=settings.API_V1_STR, tags=["Data Export"])
app.include_router(admin.router, prefix=settings.API_V1_STR, tags=["Admin"])
app.include_router(observability.router, prefix=settings.API_V1_STR, tags=["Observability"])


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "docs_url": "/docs" if settings.APP_ENV != "production" or settings.DEBUG else None,
        "api_v1": settings.API_V1_STR,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
