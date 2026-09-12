# Guía de Despliegue: Backend en Hugging Face Spaces ($0 Perpetuo)

Esta guía explica paso a paso cómo desplegar el backend de procesamiento de video con **FastAPI + FFmpeg** en **Hugging Face Spaces** utilizando el nivel gratuito con Docker (**Free CPU Basic: 2 vCPU, 16 GB de RAM, $0/mes para siempre**).

---

## Requisitos Previos
1. Una cuenta gratuita en [Hugging Face](https://huggingface.co/join).
2. Git instalado en tu computadora (o puedes subir los archivos directamente desde el navegador web).

---

## Paso 1: Crear el Space en Hugging Face
1. Inicia sesión en [Hugging Face](https://huggingface.co/).
2. Haz clic en tu avatar arriba a la derecha y selecciona **New Space** (o ve a `https://huggingface.co/new-space`).
3. Completa los campos:
   - **Space name**: `marino-editor-api` (o el nombre que elijas).
   - **License**: `mit` o `apache-2.0`.
   - **Select the Space SDK**: Selecciona **Docker** (muy importante: NO Gradio, NO Streamlit; selecciona **Docker**).
   - **Choose a Docker template**: Selecciona **Blank**.
   - **Space Hardware**: Selecciona **CPU Basic (Free - 2 vCPU, 16 GB RAM)**.
   - **Visibility**: **Public** (para que el frontend web pueda conectarse sin tokens).
4. Haz clic en **Create Space**.

---

## Paso 2: Subir los Archivos del Backend
Puedes subir los archivos clonando el repositorio de Git que te da Hugging Face o usando la interfaz web:

### Opción A: Vía Git (Recomendada)
En tu terminal:
```bash
# 1. Clona el Space vacío creado en tu máquina
git clone https://huggingface.co/spaces/TU_USUARIO/marino-editor-api

# 2. Copia todo el contenido de la carpeta 'backend/' dentro del repositorio clonado:
# - app/
# - assets/ (incluyendo intro_marino.mp4 o intro_marino.mov)
# - Dockerfile
# - requirements.txt
# - README.md

# 3. Haz commit y push
cd marino-editor-api
git add .
git commit -m "Despliegue inicial backend Marino Editor con FFmpeg"
git push
```

### Opción B: Vía Navegador Web (Directo en Hugging Face)
1. En la página de tu Space, ve a la pestaña **Files**.
2. Haz clic en **Add file** -> **Upload files**.
3. Arrastra los archivos de la carpeta `backend/` asegurándote de mantener la estructura de subcarpetas (`app/` y `assets/`).
4. Haz clic en **Commit changes to main**.

---

## Paso 3: Esperar la Compilación Automática
1. Hugging Face detectará el archivo `Dockerfile` y comenzará a construir la imagen de Debian con FFmpeg y Python 3.10.
2. Esto toma aproximadamente 2 a 3 minutos la primera vez.
3. Cuando termine, el estado cambiará a **Running** (color verde).

---

## Paso 4: Obtener la URL Pública de la API
1. En la esquina superior derecha del Space (junto al botón "Embed this Space" o en los 3 puntos `...`), haz clic en **Direct URL** o copia la URL de tu Space:
   - Ejemplo: `https://TU_USUARIO-marino-editor-api.hf.space`
2. Prueba que esté funcionando abriendo en tu navegador:
   - `https://TU_USUARIO-marino-editor-api.hf.space/api/health`
3. Debe responder un JSON indicando:
   ```json
   {
     "status": "online",
     "service": "90 Segundos DDHH Video Assembler",
     "intro_available": true,
     "max_upload_mb": 500
   }
   ```

---

## Paso 5: Conectar con el Frontend
Copia esa URL y pégala en el frontend:
- En la interfaz web tocando **"⚙️ Configurar servidor de procesamiento"**, o
- Como variable de entorno en Vercel: `VITE_API_URL=https://TU_USUARIO-marino-editor-api.hf.space`.
