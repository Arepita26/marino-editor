import gradio as gr
from app.main import app as fastapi_app

# Interfaz de presentación e información del Space en Hugging Face
with gr.Blocks(title="Marino Editor API — 90 Segundos DDHH") as demo:
    gr.Markdown("# 🎬 Marino Editor API")
    gr.Markdown("**Servicio backend de renderizado de video vertical para La TV Calle y DDHH.**")
    gr.Markdown("""
    - ✅ **Intro Oficial:** Permanente e integrado en `assets/intro_marino.mp4`.
    - ⚡ **Aceleración:** Ensamblaje ultrarrápido multihilo con FFmpeg.
    - 📱 **Formato:** Vertical 1080x1920 (9:16) a 30 fps constantes.
    - 🔗 **Endpoints API Disponibles:**
      - `GET /api/health`
      - `POST /api/procesar`
      - `GET /api/status/{ticket_id}`
      - `GET /api/descargar/{ticket_id}`
      - `POST /api/cancelar/{ticket_id}`
    """)

# Monta la app Gradio junto con FastAPI en la raíz
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
