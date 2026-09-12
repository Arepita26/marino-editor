import asyncio
from datetime import datetime
import logging
import os
from pathlib import Path
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from app.config import MAX_FILE_SIZE_MB, TEMP_DIR
from app.services.cleanup_service import delete_ticket_files
from app.services.video_processor import (
    TaskStatus,
    cancel_task,
    get_task_status,
    process_video_pipeline,
    register_ticket,
    update_task,
)
from app.utils.security import (
    generate_ticket_id,
    stream_and_save_upload,
    validate_file_metadata,
)

logger = logging.getLogger("marino_editor.routes.video")
router = APIRouter(prefix="/api", tags=["Video Processing"])


@router.post("/procesar")
async def procesar_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Receives an uploaded video clip, validates size (up to 500 MB) and format,
    assigns a unique ticket_id, streams to ephemeral disk, and initiates
    asynchronous FFmpeg assembly in the background.
    """
    # 1. Validate basic metadata (name, extension, mime)
    is_valid, err_msg = validate_file_metadata(file)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )

    # 2. Generate secure ticket
    ticket_id = generate_ticket_id()
    register_ticket(ticket_id)

    # 3. Stream upload directly to disk with byte enforcement
    try:
        saved_path = await stream_and_save_upload(file, ticket_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando subida para {ticket_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error guardando el archivo de video: {str(e)}",
        )

    # 4. Schedule background FFmpeg pipeline
    background_tasks.add_task(process_video_pipeline, ticket_id, saved_path)

    return {
        "ticket_id": ticket_id,
        "status": "procesando",
        "message": "Video recibido correctamente. Iniciando ensamblaje con intro oficial.",
        "max_size_mb": MAX_FILE_SIZE_MB,
    }


@router.get("/status/{ticket_id}")
def obtener_estado(ticket_id: str):
    """
    Poll endpoint called every 3-4 seconds by the client to query processing state.
    """
    task = get_task_status(ticket_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' no encontrado o ha expirado.",
        )

    return {
        "ticket_id": ticket_id,
        "status": task["status"],
        "progress": task["progress"],
        "step": task.get("step", ""),
        "error": task.get("error"),
    }


@router.get("/descargar/{ticket_id}")
def descargar_video(ticket_id: str, background_tasks: BackgroundTasks):
    """
    Delivers the assembled video as a downloadable MP4 stream and schedules
    immediate cleanup of ephemeral files on disk upon completion.
    """
    task = get_task_status(ticket_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' no existe o ya fue eliminado.",
        )

    if task["status"] != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El video para el ticket '{ticket_id}' aún no está listo (estado: {task['status']}).",
        )

    output_path = task.get("output_path")
    if not output_path or not Path(output_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo resultante no se encuentra en el servidor. Puede haber expirado.",
        )

    meses_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    now = datetime.now()
    safe_filename = f"{now.day}_de_{meses_es[now.month - 1]}_de_{now.year}.mp4"

    # Schedule background cleanup after delivering response
    # We give a 60 second delay before deleting so mobile browsers can retry or complete ranges
    def delayed_cleanup():
        import time
        time.sleep(30)
        delete_ticket_files(ticket_id)

    background_tasks.add_task(delayed_cleanup)

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=safe_filename,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.post("/cancelar/{ticket_id}")
def cancelar_procesamiento(ticket_id: str):
    """
    Aborts any running FFmpeg process for the ticket and frees resources immediately.
    """
    cancelled = cancel_task(ticket_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' no encontrado o no activo.",
        )
    return {"status": "cancelado", "ticket_id": ticket_id, "message": "Procesamiento cancelado exitosamente."}

