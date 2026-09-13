import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import threading
import time
import urllib.parse
import uuid
from datetime import datetime
from pathlib import Path

PORT = 7860
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMP_DIR = Path(os.getenv("TEMP_DIR", str(BACKEND_DIR / "temp_processing")))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Find FFmpeg executable
FFMPEG_PATHS = [
    r"C:\Users\erick\AppData\Local\Microsoft\WinGet\Packages\yt-dlp.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-N-124279-g0f6ba39122-win64-gpl\bin\ffmpeg.exe",
    shutil.which("ffmpeg"),
    "ffmpeg",
]
FFMPEG_BIN = None
for p in FFMPEG_PATHS:
    if p and (Path(p).exists() if os.path.isabs(str(p)) else shutil.which(str(p))):
        FFMPEG_BIN = str(p)
        break

if not FFMPEG_BIN:
    FFMPEG_BIN = "ffmpeg"

# Find intro video
INTRO_PATHS = [
    FRONTEND_DIR / "public" / "intro_marino.mp4",
    BACKEND_DIR / "assets" / "intro_marino.mp4",
    BACKEND_DIR / "assets" / "intro_marino.mov",
    BASE_DIR / "Intro" / "90 segundos con Marino Alvarado.mov",
]
INTRO_VIDEO = None
for p in INTRO_PATHS:
    if p.exists():
        INTRO_VIDEO = p
        break

FFPROBE_BIN = FFMPEG_BIN.replace("ffmpeg.exe", "ffprobe.exe")

print(f"[LocalServer] FFmpeg: {FFMPEG_BIN}")
print(f"[LocalServer] FFprobe: {FFPROBE_BIN}")
print(f"[LocalServer] Intro: {INTRO_VIDEO}")
print(f"[LocalServer] Frontend: {FRONTEND_DIR}")

# Tasks registry
TASKS = {}


def cleanup_old_temp_files(max_age_seconds: int = 3600):
    """Limpia automáticamente archivos temporales con más de 1 hora para evitar saturar el disco."""
    try:
        now = time.time()
        for item in TEMP_DIR.iterdir():
            if item.is_file() and (now - item.stat().st_mtime > max_age_seconds):
                try:
                    item.unlink()
                except Exception:
                    pass
    except Exception:
        pass


def probe_input_video(input_path: Path) -> dict:
    """Inspección proactiva ultrarrápida (<80ms) con ffprobe para prevenir errores."""
    result = {
        "valid": True,
        "has_video": False,
        "has_audio": False,
        "duration": 0.0,
    }
    try:
        cmd = [
            FFPROBE_BIN,
            "-v", "error",
            "-show_entries", "stream=codec_type,duration:format=duration",
            "-of", "json",
            str(input_path),
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
        else:
            result["has_video"] = True
            result["has_audio"] = True
    except Exception as e:
        print(f"[LocalServer] Advertencia en ffprobe: {e}. Continuando con valores por defecto.")
        result["has_video"] = True
        result["has_audio"] = True
    return result


def process_video_job(ticket_id: str, input_path: Path):
    output_path = TEMP_DIR / f"{ticket_id}_output.mp4"
    log_path = TEMP_DIR / f"{ticket_id}_ffmpeg.log"

    # Mantenimiento preventivo de disco
    cleanup_old_temp_files()

    TASKS[ticket_id]["progress"] = 15
    TASKS[ticket_id]["step"] = "Iniciando análisis preventivo del video..."

    if not INTRO_VIDEO or not INTRO_VIDEO.exists():
        TASKS[ticket_id]["status"] = "error"
        TASKS[ticket_id]["error"] = "No se encontró el video de intro oficial."
        return

    # 1. Validación proactiva de entrada para evitar fallas a mitad de render
    probe = probe_input_video(input_path)
    if not probe["has_video"]:
        TASKS[ticket_id]["status"] = "error"
        TASKS[ticket_id]["error"] = "El archivo seleccionado no contiene una pista de video válida."
        return

    if probe["duration"] > 0 and probe["duration"] < 0.5:
        TASKS[ticket_id]["status"] = "error"
        TASKS[ticket_id]["error"] = "El video es demasiado corto (duración mínima: 1 segundo)."
        return

    TASKS[ticket_id]["progress"] = 35
    TASKS[ticket_id]["step"] = "Pegando intro oficial y normalizando resolución a 1080x1920..."

    # 2. Unión directa y ultrarrápida del intro oficial con el clip del teléfono
    if probe["has_audio"]:
        filter_complex = (
            "[0:v]setsar=1,format=yuv420p[v0]; "
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v1]; "
            "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0]; "
            "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a1]; "
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
        )
    else:
        # Si el clip no tiene audio, genera pista estéreo silenciosa para mantener sincronía
        silence_dur = max(float(probe.get("duration", 60.0)), 1.0)
        filter_complex = (
            "[0:v]setsar=1,format=yuv420p[v0]; "
            "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v1]; "
            "[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0]; "
            f"aevalsrc=0:d={silence_dur}:s=48000:c=stereo[a1]; "
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]"
        )
    map_args = ["-map", "[v]", "-map", "[a]"]

    # 3. Comando FFmpeg ultra-optimizado (máxima aceleración multicore)
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-analyzeduration", "10M",
        "-probesize", "10M",
        "-fflags", "+genpts+discardcorrupt",
        "-err_detect", "ignore_err",
        "-autorotate",
        "-i", str(INTRO_VIDEO),
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

    print(f"[LocalServer] Ensamblaje ultrarrápido FFmpeg: {' '.join(cmd)}")
    TASKS[ticket_id]["progress"] = 65
    TASKS[ticket_id]["step"] = "El video se está procesando correctamente..."

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        TASKS[ticket_id]["proc"] = proc
        stdout, stderr = proc.communicate()
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(stdout + "\n" + stderr)

        # Si el usuario canceló la tarea mientras se ejecutaba
        if TASKS[ticket_id].get("status") == "cancelado":
            return

        if proc.returncode != 0:
            TASKS[ticket_id]["status"] = "error"
            TASKS[ticket_id]["error"] = f"FFmpeg error: {stderr[-300:]}"
            return

        if output_path.exists() and output_path.stat().st_size > 1000:
            TASKS[ticket_id]["status"] = "completado"
            TASKS[ticket_id]["progress"] = 100
            TASKS[ticket_id]["step"] = "¡Video vertical 1080x1920 listo!"
            TASKS[ticket_id]["output_path"] = str(output_path)
            print(f"[LocalServer] ¡Video completado con éxito! {output_path} ({output_path.stat().st_size} bytes)")
        else:
            TASKS[ticket_id]["status"] = "error"
            TASKS[ticket_id]["error"] = "El video procesado no se generó correctamente."
    except Exception as e:
        if TASKS[ticket_id].get("status") != "cancelado":
            TASKS[ticket_id]["status"] = "error"
            TASKS[ticket_id]["error"] = str(e)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Expose-Headers", "Content-Disposition, Content-Length")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/gradio_api/v1"):
            path = path[len("/gradio_api/v1"):]

        # API Endpoints
        if path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "status": "online",
                "service": "90 Segundos DDHH Video Assembler",
                "ffmpeg_available": bool(FFMPEG_BIN),
                "intro_available": bool(INTRO_VIDEO and INTRO_VIDEO.exists()),
                "max_upload_mb": 500,
            }
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return

        if path.startswith("/api/status/"):
            ticket_id = path.replace("/api/status/", "").replace(".mp4", "").strip()
            task = TASKS.get(ticket_id)
            if not task:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Ticket no encontrado"}).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ticket_id": ticket_id,
                "status": task["status"],
                "progress": task["progress"],
                "step": task.get("step", ""),
                "error": task.get("error"),
            }).encode("utf-8"))
            return

        if path.startswith("/api/descargar/"):
            ticket_id = path.replace("/api/descargar/", "").replace(".mp4", "").strip()
            task = TASKS.get(ticket_id)
            if not task or task["status"] != "completado" or not task.get("output_path"):
                self.send_response(404)
                self.end_headers()
                return

            output_file = Path(task["output_path"])
            if not output_file.exists():
                self.send_response(404)
                self.end_headers()
                return

            meses_es = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]
            now = datetime.now()
            filename = f"{now.day}_de_{meses_es[now.month - 1]}_de_{now.year}.mp4"
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(output_file.stat().st_size))
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()

            try:
                with open(output_file, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass
            return

        # Serve static frontend files
        rel_path = path.lstrip("/")
        if not rel_path or rel_path == "index.html":
            file_to_serve = FRONTEND_DIR / "index.html"
        else:
            file_to_serve = FRONTEND_DIR / rel_path
            if not file_to_serve.exists():
                file_to_serve = FRONTEND_DIR / "public" / rel_path
            if not file_to_serve.exists():
                file_to_serve = FRONTEND_DIR / "index.html"

        if file_to_serve.exists() and file_to_serve.is_file():
            ext = file_to_serve.suffix.lower()
            mime_map = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
                ".mp4": "video/mp4",
                ".mov": "video/quicktime",
            }
            content_type = mime_map.get(ext, "application/octet-stream")
            size = file_to_serve.stat().st_size

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()

            with open(file_to_serve, "rb") as f:
                shutil.copyfileobj(f, self.wfile)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/gradio_api/v1"):
            path = path[len("/gradio_api/v1"):]

        if path == "/api/procesar":
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))

            if "multipart/form-data" not in content_type:
                self.send_response(400)
                self.end_headers()
                return

            boundary_match = re.search(r"boundary=([^\s;]+)", content_type)
            if not boundary_match:
                self.send_response(400)
                self.end_headers()
                return

            boundary = boundary_match.group(1).encode("utf-8")
            raw_body = self.rfile.read(content_length)

            parts = raw_body.split(b"--" + boundary)
            file_data = None
            for p in parts:
                if b'filename="' in p:
                    header_and_body = p.split(b"\r\n\r\n", 1)
                    if len(header_and_body) == 2:
                        file_data = header_and_body[1].rstrip(b"\r\n")
                        break

            if not file_data:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"detail": "No se recibió archivo de video."}).encode("utf-8"))
                return

            ticket_id = str(uuid.uuid4())
            input_path = TEMP_DIR / f"{ticket_id}_input.mp4"
            with open(input_path, "wb") as f:
                f.write(file_data)

            TASKS[ticket_id] = {
                "status": "procesando",
                "progress": 10,
                "step": "Iniciando ensamblaje vertical con FFmpeg...",
                "output_path": None,
                "error": None,
                "created_at": time.time(),
            }

            t = threading.Thread(target=process_video_job, args=(ticket_id, input_path))
            t.daemon = True
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ticket_id": ticket_id,
                "status": "procesando",
                "message": "Iniciando FFmpeg en el servidor...",
                "max_size_mb": 500,
            }).encode("utf-8"))
            return

        if path.startswith("/api/cancelar/"):
            ticket_id = path.replace("/api/cancelar/", "").strip()
            task = TASKS.get(ticket_id)
            if task:
                proc = task.get("proc")
                if proc and proc.poll() is None:
                    try:
                        proc.terminate()
                        proc.wait(timeout=1.0)
                    except Exception:
                        try:
                            proc.kill()
                        except Exception:
                            pass
                task["status"] = "cancelado"
                task["step"] = "Cancelado por el usuario."
                input_file = TEMP_DIR / f"{ticket_id}_input.mp4"
                output_file = TEMP_DIR / f"{ticket_id}_output.mp4"
                for f in [input_file, output_file]:
                    try:
                        if f.exists():
                            f.unlink()
                    except Exception:
                        pass
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "cancelado", "ticket_id": ticket_id}).encode("utf-8"))
                return
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()


def run_server():
    server_address = ("0.0.0.0", PORT)
    with socketserver.ThreadingTCPServer(server_address, RequestHandler) as httpd:
        print(f"[LocalServer] Servidor unificado activo en http://localhost:{PORT}/")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
