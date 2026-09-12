import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import CORS_ORIGINS
from app.routes.health import router as health_router
from app.routes.video import router as video_router
from app.services.cleanup_service import (
    start_periodic_cleanup_loop,
    sweep_expired_files,
)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("marino_editor.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown routines."""
    logger.info("Iniciando Backend Marino Editor (90 Segundos DDHH)...")
    # Clean any stale files from previous run
    sweep_expired_files(max_age_seconds=0)
    # Start background cleanup task
    cleanup_task = asyncio.create_task(start_periodic_cleanup_loop())
    yield
    logger.info("Deteniendo Backend Marino Editor...")
    cleanup_task.cancel()


app = FastAPI(
    title="Marino Editor API - 90 Segundos DDHH",
    description="Plataforma de ensamblaje automatizado de video para La TV Calle y Marino Alvarado (Provea / DDHH)",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for Hugging Face Spaces public API access
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)

# Include Routers
app.include_router(health_router)
app.include_router(video_router)


@app.get("/")
def root():
    return {
        "app": "Marino Editor API",
        "version": "1.0.0",
        "description": "Backend de procesamiento FFmpeg 1080x1920 para '90 Segundos con Marino Alvarado'",
        "docs": "/docs",
        "health": "/api/health",
    }


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Error no controlado en {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Error interno del servidor",
            "detail": str(exc),
        },
    )
