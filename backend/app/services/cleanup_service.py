import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional
from app.config import (
    CLEANUP_INTERVAL_SECONDS,
    FILE_EXPIRATION_SECONDS,
    TEMP_DIR,
)

logger = logging.getLogger("marino_editor.cleanup")


def delete_ticket_files(ticket_id: str) -> None:
    """Deletes all files associated with a given ticket_id."""
    if not ticket_id or len(ticket_id) < 10:
        return

    pattern = f"{ticket_id}*"
    deleted_count = 0
    for file_path in TEMP_DIR.glob(pattern):
        try:
            if file_path.is_file():
                file_path.unlink(missing_ok=True)
                deleted_count += 1
        except Exception as e:
            logger.warning(f"No se pudo eliminar {file_path}: {e}")

    logger.info(f"Limpieza completada para ticket {ticket_id}: {deleted_count} archivos eliminados.")


def sweep_expired_files(max_age_seconds: int = FILE_EXPIRATION_SECONDS) -> int:
    """Sweeps all files in TEMP_DIR older than max_age_seconds."""
    now = time.time()
    count = 0
    if not TEMP_DIR.exists():
        return 0

    for item in TEMP_DIR.iterdir():
        if item.is_file():
            try:
                mtime = item.stat().st_mtime
                if (now - mtime) > max_age_seconds:
                    item.unlink(missing_ok=True)
                    count += 1
            except Exception as e:
                logger.warning(f"Error borrando archivo expirado {item}: {e}")

    if count > 0:
        logger.info(f"Recolector de basura: {count} archivos expirados eliminados.")
    return count


async def start_periodic_cleanup_loop(interval: int = CLEANUP_INTERVAL_SECONDS) -> None:
    """Runs a continuous background loop to clean up abandoned temporary files."""
    logger.info(f"Iniciando servicio de autolimpieza periódica (intervalo: {interval}s)...")
    while True:
        try:
            sweep_expired_files()
        except Exception as e:
            logger.error(f"Error en bucle de autolimpieza: {e}")
        await asyncio.sleep(interval)
