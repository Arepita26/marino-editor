# Guía de Despliegue: Frontend en Vercel ($0 Perpetuo)

Esta guía explica paso a paso cómo desplegar la aplicación web móvil en **Vercel** utilizando el plan Hobby gratuito (**$0/mes para siempre**).

---

## Requisitos Previos
1. Una cuenta en [Vercel](https://vercel.com/signup).
2. Repositorio en GitHub con el proyecto (o la herramienta CLI de Vercel).

---

## Paso 1: Conectar con GitHub
1. Sube tu proyecto a GitHub (o un repositorio privado o público).
2. Entra a tu panel de control en [Vercel](https://vercel.com/dashboard).
3. Haz clic en **Add New...** -> **Project**.
4. Importa el repositorio de GitHub donde se encuentra el proyecto.

---

## Paso 2: Configuración del Proyecto en Vercel
En la pantalla de configuración antes de desplegar:
1. **Framework Preset**: Selecciona **Vite** (o déjalo en detección automática).
2. **Root Directory**: Haz clic en **Edit** y selecciona la carpeta:
   - `frontend`
   - *(Muy importante: selecciona la carpeta frontend para que Vercel compile únicamente la web).*
3. **Build & Output Settings**: Déjalas por defecto:
   - Build Command: `npm run build` o `vite build`
   - Output Directory: `dist`
4. **Environment Variables**:
   - Agrega la siguiente variable con la URL de tu backend en Hugging Face Spaces:
     * **Name**: `VITE_API_URL`
     * **Value**: `https://TU_USUARIO-marino-editor-api.hf.space`
5. Haz clic en **Deploy**.

---

## Paso 3: Verificación y Certificado HTTPS Automático
1. Vercel compilará la aplicación en aproximadamente 45 segundos.
2. Te asignará automáticamente un dominio gratuito con **HTTPS y certificado SSL TLS 1.3**:
   - Ejemplo: `https://marino-editor.vercel.app`
3. Gracias al archivo [vercel.json](file:///c:/Users/erick/Desktop/Proyectos%20Antigravity/Marino%20Editor/frontend/vercel.json), la web ya incluye:
   - Encabezados de seguridad de grado militar (`HSTS`, `X-Content-Type-Options`, `X-Frame-Options`, `CSP`).
   - Control de caché anti-obsolescencia (`Cache-Control: no-cache, no-store` para HTML y `version.json`), obligando a los teléfonos a refrescarse de inmediato cuando hagamos cambios.

---

## Paso 4: Instalar en Teléfono Móvil (PWA)
1. Abre la URL en Safari (iPhone) o Chrome (Android).
2. **En iPhone (iOS)**: Toca el botón de compartir (el cuadrado con la flecha hacia arriba) y selecciona **"Agregar a pantalla de inicio"**.
3. **En Android**: Toca los 3 puntos del menú de Chrome y selecciona **"Instalar aplicación"** o **"Agregar a pantalla principal"**.
4. La aplicación se abrirá como una aplicación nativa, a pantalla completa y con iconos oficiales.
