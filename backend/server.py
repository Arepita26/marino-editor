import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
from app.routes.health import router as health_router
from app.routes.video import router as video_router

with gr.Blocks(title="Marino Editor API — 90 Segundos DDHH") as demo:
    gr.Markdown("# 🎬 Marino Editor API")
    gr.Markdown("**Servicio backend de renderizado de video vertical para La TV Calle y DDHH.**")
    gr.Markdown("""
    - ✅ **Intro Oficial:** Permanente e integrado en `assets/intro_marino.mp4`.
    - ⚡ **Aceleración:** Ensamblaje ultrarrápido multihilo con FFmpeg.
    - 📱 **Formato:** Vertical 1080x1920 (9:16) a 30 fps constantes.
    - 🔗 **Endpoints API Activos:**
      - `GET /api/health`
      - `POST /api/procesar`
      - `GET /api/status/{ticket_id}`
      - `GET /api/descargar/{ticket_id}`
      - `POST /api/cancelar/{ticket_id}`
    """)

# Registrar middleware de CORS y los routers de procesamiento de video
demo.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)
demo.app.include_router(health_router)
demo.app.include_router(video_router)

if __name__ == "__main__":
    demo.launch()
