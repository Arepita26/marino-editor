---
title: Marino Editor API
emoji: 🎬
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
---

# Marino Editor API - 90 Segundos DDHH

Backend de procesamiento y ensamblaje de video con FFmpeg para **La TV Calle** y **DDHH**, uniendo clips de usuario con la intro oficial de **Marino Alvarado**.

## Características
- **Costo $0 Perpetuo**: Diseñado para el nivel gratuito de Hugging Face Spaces (CPU Basic: 2 vCPU, 16 GB RAM).
- **Intro Permanente**: Almacenado en `assets/intro_marino.mp4`, siempre disponible en el Space.
- **Resolución vertical**: Forzado a 1080x1920 a 30 fps constantes (`yuv420p` SDR).
- **Aceleración multihilo**: Concatena en 2.5 a 4 segundos aprovechando los 2 vCPU.
- **Autolimpieza efímera**: Eliminación automática de videos temporales tras la descarga.
- **Límite de archivo**: Hasta 500 MB por video.

## Endpoints
- `GET /`: Información básica de la API y panel de estado.
- `GET /api/health`: Estado de la API y disponibilidad de la intro oficial.
- `POST /api/procesar`: Recibe video (`multipart/form-data`) y arranca proceso asíncrono.
- `GET /api/status/{ticket_id}`: Consulta de estado y progreso.
- `GET /api/descargar/{ticket_id}`: Descarga directa del video final.
- `POST /api/cancelar/{ticket_id}`: Aborta el procesamiento y limpia archivos en disco.
