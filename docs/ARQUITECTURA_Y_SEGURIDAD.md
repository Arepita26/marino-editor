# Manual Técnico: Arquitectura, Seguridad, Anti-Caché y Video Pipeline

Este documento describe las especificaciones técnicas y decisiones de diseño implementadas en la suite **Marino Editor - 90 Segundos DDHH**.

---

## 1. Estrategia Anti-Caché: Forzado de Actualizaciones en Teléfonos Móviles

Uno de los problemas más comunes en aplicaciones web móviles (Safari en iOS y Chrome en Android) es la retención agresiva de archivos en caché, lo que causa que los cambios desplegados no se reflejen en los teléfonos de los usuarios.

Para resolver esto de raíz, implementamos una **arquitectura anti-caché de 4 capas**:

1. **Hashes Criptográficos en Compilaciones (Vite Build Hashes)**:
   - Todo archivo JavaScript o CSS generado recibe un nombre único basado en su contenido: `assets/index.[hash].js` y `assets/index.[hash].css`.
   - Cuando el código cambia, el nombre del archivo cambia por completo, haciendo imposible que el navegador reutilice un script viejo.

2. **Encabezados HTTP `Cache-Control` Estrictos (`vercel.json`)**:
   - `index.html`, `version.json` y `sw.js` se sirven con:
     ```http
     Cache-Control: no-cache, no-store, must-revalidate
     Pragma: no-cache
     Expires: 0
     ```
   - Esto obliga al navegador del teléfono a consultar siempre al servidor antes de renderizar la página.

3. **Monitor de Versión en Tiempo Real (`useForceUpdate` / `version.json`)**:
   - El cliente consulta periódicamente (`/version.json?t=TIMESTAMP`) cada 45 segundos y cada vez que el usuario vuelve a abrir la app (`visibilitychange` / `window.onfocus`).
   - Si la versión en el servidor difiere de la instalada en el teléfono, se despliega un banner de máxima prioridad con el botón **"Actualizar ahora"**, el cual purga el almacenamiento de `caches` y fuerza una recarga total (`window.location.reload(true)`).

4. **Service Worker Inmediato (`skipWaiting` & `clients.claim`)**:
   - En el archivo `sw.js`, el evento `install` invoca `self.skipWaiting()` y `activate` invoca `self.clients.claim()`, desactivando cualquier caché vieja sin requerir que el usuario cierre el navegador.

---

## 2. Experiencia de Usuario: Modo Ultra-Sencillo (Apple Design para Adultos Mayores)

Siguiendo las pautas de accesibilidad para personas mayores:
- **Tipografía**: Base mínima de 18px, encabezados de 24px a 32px, con pesos tipográficos marcados (700 y 800) para máxima legibilidad.
- **Botones Táctiles Gigantes**: Áreas de toque de 64px a 72px de altura, superando con creces la recomendación de Apple (44px) y Google (48px).
- **Flujo Secuencial de 3 Estados**:
  - **Estado 1**: Selección directa con un solo botón central (*"1. Elegir Video"*). Se desbloquea el botón 2 (*"2. Pegar Intro y Procesar"*).
  - **Estado 2**: Barra de progreso con porcentaje visible y texto descriptivo paso a paso.
  - **Estado 3**: Botones gigantes de descarga y compartir directo en WhatsApp.
- **Retroalimentación Táctil (Haptics)**: Vibración sutil (`navigator.vibrate`) al seleccionar el video y al finalizar el procesamiento.

---

## 3. Modo Oscuro y Modo Claro de Alto Contraste

- Se implementó un interruptor de tema persistente en `localStorage`.
- **Modo Oscuro (OLED)**: Fondo `#090D16`, tarjetas `#131B2E`, texto blanco puro `#F8FAFC` y acentos celestes `#38BDF8`.
- **Modo Claro**: Fondo `#F8FAFC`, tarjetas blancas `#FFFFFF`, texto negro pizarra `#0F172A` y acentos azul zafiro `#0284C7`.
- Ratios de contraste superiores a 7:1 (cumplimiento WCAG AAA).

---

## 4. Pipeline de Video FFmpeg Vertical (1080x1920)

El comando núcleo ejecutado en el backend:
```bash
ffmpeg -y -autorotate \
  -i assets/intro_marino.mp4 -i input_usuario.mp4 \
  -filter_complex "\
    [0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v0]; \
    [1:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p[v1]; \
    [v0][v1]xfade=transition=fade:duration=0.3:offset=3.83[v]; \
    [0:a]aformat=sample_rates=48000:channel_layouts=stereo[a0]; \
    [1:a]aformat=sample_rates=48000:channel_layouts=stereo,loudnorm=I=-16:TP=-1.5:LRA=11[a1]; \
    [a0][a1]acrossfade=d=0.3[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset ultrafast -crf 24 \
  -c:a aac -b:a 192k -threads 0 -movflags +faststart output.mp4
```

### Funciones Críticas de este Pipeline:
1. `-autorotate`: Corrige automáticamente videos grabados en vertical con metadatos EXIF de iPhone y Android.
2. `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920`: Centra y recorta el video al formato vertical estándar de Reels/TikTok/WhatsApp sin deformar la imagen.
3. `format=yuv420p`: Neutraliza grabaciones en HDR de 10 bits (Dolby Vision / HLG de iPhone 12 en adelante) para que no se vean lavadas ni negras en reproductores estándar.
4. `loudnorm=I=-16:TP=-1.5:LRA=11`: Ecualización de volumen EBU R128, nivelando el micrófono del teléfono con la locución profesional de la intro.
5. `xfade` y `acrossfade` de 0.3 segundos: Suaviza la transición visual y auditiva entre la intro de Marino y la noticia del reportero.
6. `-movflags +faststart`: Coloca el átomo `moov` al inicio del archivo MP4, permitiendo reproducción en streaming instantáneo sin esperar a descargar el video completo.

---

## 5. Mecanismos de Seguridad y Privacidad

1. **Cifrado en Tránsito (HTTPS / TLS 1.3)** forzado en Vercel y Hugging Face.
2. **Encabezados de Seguridad Web**:
   - `Content-Security-Policy (CSP)`
   - `Strict-Transport-Security (HSTS)`
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
3. **Validación de Archivos en Backend**:
   - Límite estricto de **500 MB** con contador de bytes en tiempo real (evita saturación de memoria RAM).
   - Verificación de cabeceras binarias (*magic bytes*) para contenedores MP4/QuickTime.
   - Nombres de archivo sanitizados con identificadores UUID (inmune a *path traversal*).
4. **Almacenamiento Efímero y Cero Retención**:
   - Los archivos se eliminan automáticamente del disco en segundo plano (`BackgroundTasks`) tras ser descargados.
   - Recolector de basura periódico que borra cualquier archivo con más de 30 minutos de antigüedad.
