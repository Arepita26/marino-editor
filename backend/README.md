---
title: Marino Editor API
emoji: 🎬
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Marino Editor API - 90 Segundos DDHH

Backend de procesamiento y ensamblaje de video con FFmpeg para **La TV Calle** y **DDHH**, uniendo clips de usuario con la intro oficial de **Marino Alvarado**.

## Características
- **Costo $0 Perpetuo**: Diseñado para el nivel gratuito de Hugging Face Spaces (CPU Basic).
- **Resolución vertical estandarizada**: Forzado a 1080x1920 a 30 fps constantes (`yuv420p` SDR).
- **Disolvencia cruzada**: 0.3s video (`xfade`) y audio (`acrossfade`).
- **Nivelación acústica**: EBU R128 `loudnorm` (`I=-16`, `TP=-1.5`, `LRA=11`).
- **Autolimpieza efímera**: Eliminación automática de videos tras la descarga y recolector de basura de archivos de más de 30 minutos.
- **Límite de archivo**: Hasta 500 MB por video.

## Endpoints
- `GET /`: Información básica de la API.
- `GET /api/health`: Estado de la API y disponibilidad de la intro oficial.
- `POST /api/procesar`: Recibe video (`multipart/form-data`) y arranca proceso asíncrono.
- `GET /api/status/{ticket_id}`: Consulta de estado y progreso.
- `GET /api/descargar/{ticket_id}`: Descarga directa del video final con autolimpieza.
