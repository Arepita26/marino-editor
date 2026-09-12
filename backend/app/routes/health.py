import os
import shutil
from pathlib import Path
from fastapi import APIRouter
from app.config import (
    INTRO_VIDEO_PATH,
    MAX_FILE_SIZE_MB,
    TEMP_DIR,
)

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health_check():
    """Health check endpoint confirming API status and asset readiness."""
    intro_ready = INTRO_VIDEO_PATH.exists()
    intro_size_mb = (
        round(INTRO_VIDEO_PATH.stat().st_size / (1024 * 1024), 2)
        if intro_ready
        else 0
    )

    # Check disk space in temp directory
    try:
        total, used, free = shutil.disk_usage(TEMP_DIR)
        disk_free_gb = round(free / (1024 * 1024 * 1024), 2)
    except Exception:
        disk_free_gb = "unknown"

    return {
        "status": "online",
        "service": "90 Segundos DDHH Video Assembler",
        "intro_available": intro_ready,
        "intro_size_mb": intro_size_mb,
        "intro_path": str(INTRO_VIDEO_PATH.name),
        "max_upload_mb": MAX_FILE_SIZE_MB,
        "disk_free_gb": disk_free_gb,
    }
