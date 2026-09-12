import asyncio
import json
import logging
import os
import subprocess
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import (
    CROSSFADE_DURATION_SECONDS,
    CROSSFADE_OFFSET_SECONDS,
    INTRO_VIDEO_PATH,
    TEMP_DIR,
)

logger = logging.getLogger("marino_editor.video_processor")


class TaskStatus(str, Enum):
    PENDING = "pendiente"
    PROCESSING = "procesando"
    COMPLETED = "completado"
    CANCELLED = "cancelado"
    ERROR = "error"


# In-memory ticket registry for asynchronous state tracking
# {ticket_id: {"status": TaskStatus, "progress": int, "output_path": Path, "error": str, "created_at": float, "proc": Process}}
TASKS: Dict[str, Dict[str, Any]] = {}


def register_ticket(ticket_id: str) -> None:
    """Registers a new processing task."""
    TASKS[ticket_id] = {
        "status": TaskStatus.PROCESSING,
        "progress": 5,
        "step": "Iniciando procesamiento de video...",
        "output_path": None,
        "error": None,
        "created_at": time.time(),
        "proc": None,
    }


def get_task_status(ticket_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves status for a given ticket."""
    return TASKS.get(ticket_id)


def update_task(ticket_id: str, **kwargs) -> None:
    """Updates fields in task registry."""
    if ticket_id in TASKS:
        TASKS[ticket_id].update(kwargs)


def cancel_task(ticket_id: str) -> bool:
    """Terminates any running FFmpeg process and cleans up files for the given ticket."""
    task = TASKS.get(ticket_id)
    if not task:
        return False

    proc = task.get("proc")
    if proc:
        try:
            proc.terminate()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    task["status"] = TaskStatus.CANCELLED
    task["step"] = "Procesamiento cancelado por el usuario."

    input_file = TEMP_DIR / f"{ticket_id}_input.mp4"
    output_file = TEMP_DIR / f"{ticket_id}_output.mp4"
    for f in [input_file, output_file]:
        try:
            if f.exists():
                f.unlink()
        except Exception:
            pass

    return True


def probe_input_video(file_path: Path) -> dict:
    """Proactively inspects video streams and audio presence with ffprobe."""
    result = {"has_video": True, "has_audio": True, "duration": 60.0}
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "stream=codec_type,duration:format=duration",
            "-of", "json",
            str(file_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            streams = data.get("streams", [])
            result["has_video"] = any(s.get("codec_type") == "video" for s in streams)
            result["has_audio"] = any(s.get("codec_type") == "audio" for s in streams)
            dur = data.get("format", {}).get("duration")
            if dur:
                result["duration"] = float(dur)
    except Exception as e:
        logger.warning(f"Advertencia en ffprobe: {e}. Asumiendo valores estándar.")
    return result


async def process_video_pipeline(ticket_id: str, input_path: Path) -> None:
    """
    Ultra-fast video assembly pipeline: joins the fixed official Marino Alvarado intro
    with the user's vertical mobile clip using direct concatenation and libx264 ultrafast preset.
    """
    output_path = TEMP_DIR / f"{ticket_id}_output.mp4"
    log_path = TEMP_DIR / f"{ticket_id}_ffmpeg.log"

    if not INTRO_VIDEO_PATH.exists():
        msg = f"No se encontró el video de intro oficial en {INTRO_VIDEO_PATH}."
        logger.error(msg)
        update_task(ticket_id, status=TaskStatus.ERROR, error=msg, progress=0)
        return

    update_task(
        ticket_id,
        status=TaskStatus.PROCESSING,
        progress=25,
        step="Analizando video e integrando resolución vertical 1080x1920...",
    )

    probe = probe_input_video(input_path)

    if probe["has_audio"]:
        filter_complex = (
            "[0:v]setsar=1,format=yuv420p[v0]; "
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v1]; "
            "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0]; "
            "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a1]; "
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
        )
    else:
        silence_dur = max(float(probe.get("duration", 60.0)), 1.0)
        filter_complex = (
            "[0:v]setsar=1,format=yuv420p[v0]; "
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v1]; "
            "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0]; "
            f"aevalsrc=0:d={silence_dur}:s=48000:c=stereo[a1]; "
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
        )

    map_args = ["-map", "[v]", "-map", "[a]"]

    cmd = [
        "ffmpeg",
        "-y",
        "-analyzeduration", "10M",
        "-probesize", "10M",
        "-fflags", "+genpts+discardcorrupt",
        "-err_detect", "ignore_err",
        "-autorotate",
        "-i", str(INTRO_VIDEO_PATH),
        "-i", str(input_path),
        "-filter_complex_threads", "0",
        "-filter_complex", filter_complex,
        *map_args,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "fastdecode",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-max_muxing_queue_size", "1024",
        "-threads", "0",
        "-movflags", "+faststart",
        str(output_path),
    ]

    logger.info(f"Iniciando FFmpeg ultra-rápido para ticket {ticket_id}: {' '.join(cmd)}")
    update_task(
        ticket_id,
        progress=60,
        step="Ensamblando intro oficial con el video...",
    )

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if ticket_id in TASKS:
            TASKS[ticket_id]["proc"] = process

        stdout, stderr = await process.communicate()

        if ticket_id in TASKS and TASKS[ticket_id].get("status") == TaskStatus.CANCELLED:
            return

        with open(log_path, "wb") as f:
            f.write(b"--- STDOUT ---\n" + stdout + b"\n--- STDERR ---\n" + stderr)

        if process.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="ignore")[-800:]
            logger.error(f"FFmpeg falló (código {process.returncode}): {err_msg}")
            update_task(
                ticket_id,
                status=TaskStatus.ERROR,
                error=f"Error en procesamiento de video: {err_msg}",
                progress=0,
            )
            return

        if not output_path.exists() or output_path.stat().st_size == 0:
            logger.error("El archivo de salida FFmpeg no fue generado o está vacío.")
            update_task(
                ticket_id,
                status=TaskStatus.ERROR,
                error="El video final no pudo generarse correctamente.",
                progress=0,
            )
            return

        logger.info(f"Video procesado exitosamente para ticket {ticket_id}: {output_path}")
        update_task(
            ticket_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            step="¡Video listo para descargar y compartir!",
            output_path=output_path,
        )

    except Exception as e:
        if ticket_id in TASKS and TASKS[ticket_id].get("status") != TaskStatus.CANCELLED:
            logger.exception(f"Excepción inesperada en video pipeline para {ticket_id}: {e}")
            update_task(
                ticket_id,
                status=TaskStatus.ERROR,
                error=f"Fallo del sistema de video: {str(e)}",
                progress=0,
            )
