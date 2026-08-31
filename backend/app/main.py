"""FastAPI Application Entry Point (TASK 10 Production Hardened)."""

import json
import logging
import time
import uuid
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.app.api.v1 import admin, analytics, auth, customers, data_quality, export, health, models, scoring, segments
from backend.app.core.config import settings

# Configure structured logging
logger = logging.getLogger("telecom_churn_backend")
logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

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
    """Production Security Headers & Request Correlation Tracking Middleware."""
    correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
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

    # Log access securely without leaking PII or secrets
    log_entry = {
        "correlation_id": correlation_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": duration_ms,
    }
    logger.info(json.dumps(log_entry))

    return response


# Standardized Exception Handlers (no internal stack traces exposed to client)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    correlation_id = request.headers.get("X-Correlation-ID", f"err-{uuid.uuid4().hex[:8]}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail if isinstance(exc.detail, (str, dict, list)) else str(exc.detail),
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail if isinstance(exc.detail, str) else "Request error",
                "request_id": correlation_id,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = request.headers.get("X-Correlation-ID", f"val-{uuid.uuid4().hex[:8]}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
    correlation_id = request.headers.get("X-Correlation-ID", f"exc-{uuid.uuid4().hex[:8]}")
    logger.error(f"[Unhandled Exception] ID: {correlation_id} - Path: {request.url.path} - Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
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
