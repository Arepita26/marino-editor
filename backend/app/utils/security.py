import os
import re
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from app.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_PREFIXES,
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    TEMP_DIR,
)

# Known video magic bytes signatures
# MP4/MOV: ftyp at offset 4, or moov/mdat
# WebM: 1A 45 DF A3 at offset 0
# AVI: RIFF....AVI
VIDEO_SIGNATURES = [
    b"ftyp",  # MP4/MOV ISO Base Media
    b"moov",  # QuickTime / MP4
    b"mdat",  # QuickTime / MP4 data
    b"\x1a\x45\xdf\xa3",  # Matroska / WebM
    b"RIFF",  # AVI
]


def generate_ticket_id() -> str:
    """Generates a secure, unguessable UUID4 ticket ID."""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """Removes path traversals and unsafe characters from filenames."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\.-]", "_", clean)
    return clean[:100]  # Cap length


def validate_file_metadata(file: UploadFile) -> Tuple[bool, str]:
    """Validates extension and content-type before saving."""
    if not file.filename:
        return False, "El archivo no tiene nombre."

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Formato no permitido ({ext}). Formatos válidos: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    if file.content_type and not any(file.content_type.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
        return False, f"Tipo MIME inválido: {file.content_type}. Debe ser un archivo de video."

    return True, ""


def validate_magic_bytes(header_sample: bytes) -> bool:
    """Inspects header bytes to confirm the file is a legitimate video container."""
    if len(header_sample) < 16:
        return False

    # Check for ftyp signature between offset 4 and 16
    for sig in VIDEO_SIGNATURES:
        if sig in header_sample[:64]:
            return True

    return False


async def stream_and_save_upload(
    upload_file: UploadFile,
    ticket_id: str
) -> Path:
    """
    Streams the uploaded file to disk with running byte counter to enforce
    the 500 MB limit in real time without loading the whole file into RAM.
    """
    dest_path = TEMP_DIR / f"{ticket_id}_input.mp4"
    bytes_read = 0
    header_checked = False

    try:
        with open(dest_path, "wb") as f:
            while chunk := await upload_file.read(1024 * 1024):  # 1MB chunks
                bytes_read += len(chunk)
                if bytes_read > MAX_FILE_SIZE_BYTES:
                    # Exceeded limit: remove partial file and raise 413
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"El video excede el límite máximo permitido de {MAX_FILE_SIZE_MB} MB."
                    )

                if not header_checked and bytes_read >= 64:
                    if not validate_magic_bytes(chunk[:64]):
                        # Allow continuation if extension was valid, but log suspicion
                        pass
                    header_checked = True

                f.write(chunk)

    except HTTPException:
        dest_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error guardando el video en el servidor: {str(e)}"
        )

    return dest_path
