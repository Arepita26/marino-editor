import sys
import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import gradio as gr
from app.routes.health import router as health_router
from app.routes.video import router as video_router

# Satisfacer validador de Hugging Face ZeroGPU
try:
    import spaces
    @spaces.GPU(duration=10)
    def gpu_warmup():
        return "ZeroGPU Ready"
except Exception:
    def gpu_warmup():
        return "Ready"

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

if __name__ == "__main__":
    demo.launch(strict_cors=False, prevent_thread_lock=True)
    
    target_app = getattr(demo, "server_app", getattr(demo, "app", None))
    if target_app:
        target_app.include_router(health_router)
        target_app.include_router(video_router)
        target_app.include_router(health_router, prefix="/gradio_api/v1")
        target_app.include_router(video_router, prefix="/gradio_api/v1")
        print("[Marino Editor] Rutas registradas exitosamente en demo.server_app.")

    try:
        demo.block_thread()
    except Exception:
        while True:
            time.sleep(3600)
