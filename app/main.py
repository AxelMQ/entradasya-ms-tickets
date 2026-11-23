import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.batch import router as batch_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.validation import router as validation_router
from app.core.config import settings
from app.core.database import check_db_ready


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage directory exists at startup
    settings.get_resolved_storage_path()
    yield


app = FastAPI(
    title="ms-tickets API",
    description="Microservicio de Emisión de Entradas, Generación de PDF y Código QR - EntradasYa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Checks
@app.get("/health/live", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_live():
    """Liveness probe: returns 200 if process is running."""
    return {
        "status": "UP",
        "service": "ms-tickets",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready", tags=["Health"])
async def health_ready():
    """Readiness probe: checks active database connection."""
    is_ready = await check_db_ready()
    if is_ready:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "UP",
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "DOWN",
            "database": "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_legacy():
    """Legacy health check endpoint."""
    return {
        "status": "UP",
        "service": "ms-tickets",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include Routers
app.include_router(batch_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")
app.include_router(validation_router, prefix="/api/v1")

# Also include under /api for backwards compatibility
app.include_router(batch_router, prefix="/api")
app.include_router(tickets_router, prefix="/api")
app.include_router(validation_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
