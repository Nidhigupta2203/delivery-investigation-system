from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import get_db

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API for managing robotics dataset orders, deliveries, and recording investigations.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Enable CORS for frontend and development tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount business API v1 routers
app.include_router(api_router)


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint welcoming clients and confirming the service is online."""
    return {
        "message": "Welcome to Delivery Investigation System API",
        "version": "0.1.0",
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Healthcheck endpoint verifying the API server and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": f"disconnected: {str(exc)}",
                "environment": settings.APP_ENV,
            },
        )

    return {
        "status": "healthy",
        "database": db_status,
        "environment": settings.APP_ENV,
    }
