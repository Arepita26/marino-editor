# INFORME TÉCNICO DE PRODUCCIÓN: RESTAURACIÓN DEL SELECTOR DEL SISTEMA (SAF) Y FORZADO DE CACHÉ v2.2.0

**Proyecto:** Marino Editor — Suite de Video Automatizada (90 Segundos con Marino Alvarado)  
**Fecha:** 13 de Septiembre de 2026  
**Versión Actual:** `v2.2.0`  
**Repositorio GitHub:** [https://github.com/Arepita26/marino-editor](https://github.com/Arepita26/marino-editor) (Rama `main`)  
**Frontend en Producción (Vercel):** [https://marino-editor.vercel.app](https://marino-editor.vercel.app)  
**Backend en Producción (Hugging Face Spaces):** [https://arepita26-marino-editor-api.hf.space/gradio_api/v1](https://arepita26-marino-editor-api.hf.space/gradio_api/v1)  
**Autor Git:** `Arepita26 <rosaserick26@gmail.com>`  

---

## 1. DIAGNÓSTICO Y CAUSA RAÍZ (PHOTO PICKER VS. SAF EN ANDROID 13/14)

### El Síntoma
Al tocar la zona de carga en teléfonos con Android 13 o 14, se abría una galería modal en fondo oscuro ("Photo Picker" con pestañas *Videos / Colecciones*). Al seleccionar un video, la ventana se cerraba pero el archivo se descartaba silenciosamente y nunca llegaba a la aplicación web.

### La Causa Técnica
1. **Comportamiento del comodín `accept="video/*"`:**
   En Android 13+ y en versiones recientes de Chromium/Brave/Samsung Internet, la presencia de `accept="video/*"` invoca el componente de sistema **Android Photo Picker**.
2. **Fallo de IPC / Permisos en el Photo Picker:**
   El Photo Picker opera bajo un proveedor de contenido desacoplado (`MediaStore.ACTION_PICK_IMAGES`). En múltiples implementaciones de navegadores móviles, la transferencia del descriptor de archivo (`Content URI` a `File blob`) falla o se interrumpe al destruirse la actividad modal, entregando una lista vacía de archivos al evento `change`.
3. **La Solución Comprobada (Arquitectura TV Calle Generator):**
   Al declarar extensiones de archivo explícitas:
   `accept=".mp4,.mov,.m4v,.webm,video/mp4,video/quicktime,application/octet-stream"`
   Android no puede asociar la solicitud únicamente al Photo Picker de medios. En su lugar, el sistema operativo invoca el **Selector de Intención del Sistema (Storage Access Framework - SAF)**, desplegando el menú con:
   * **Cámara**
   * **Cámara de video**
   * **Grabadora de audio**
   * **Archivos / Fotos y videos (Gestor de Recientes)**
   Al tocar "Archivos", el usuario ingresa a la lista de **Recientes**, donde los archivos de WhatsApp, descargas y cámara devuelven siempre descriptores válidos con lectura directa.

---

## 2. MODIFICACIONES IMPLEMENTADAS EN EL FRONTEND

### A. Estructura HTML (`frontend/index.html`)
Se configuró el atributo `accept` explícito y se actualizaron las referencias de recursos a `v2.2.0`:

```html
<!-- Zona de Selección Adaptada a Táctil Directo SAF -->
<div class="dropzone-label" id="dropzoneContainer">
  <div class="dropzone-content">
    <div class="upload-icon">📹</div>
    <p class="primary-text" id="dropzonePrimaryText">Toca aquí para seleccionar el video</p>
    <p class="sub-text">MP4 o MOV (Hasta 500 MB)</p>
    <span id="selectedFileName" class="file-name-badge"></span>
  </div>
  <input 
    type="file" 
    id="videoInput" 
    name="video" 
    accept=".mp4,.mov,.m4v,.webm,video/mp4,video/quicktime,application/octet-stream" 
    class="native-touch-input"
  />
</div>
```

**Busting de Caché en Recursos:**
```html
<link rel="stylesheet" href="styles.css?v=2.2.0" />
<link rel="stylesheet" href="src/styles/index.css?v=2.2.0" />
<script src="script.js?v=2.2.0" defer></script>
```

**Pie de Página:**
```html
<p>Marino Editor — Suite de Video Automatizada v2.2.0</p>
```

---

### B. Lógica JavaScript (`frontend/script.js`)

1. **Mecanismo de Rescate `window.onfocus`:**
   Garantiza que si el sistema operativo omite o retarda el evento `change` al cerrar la app de Recientes, el archivo se capture de inmediato al recuperar el foco de la ventana:
   ```javascript
   // Rescate cuando el usuario vuelve de la app de Archivos / Recientes (Arquitectura TV Calle)
   window.addEventListener("focus", () => {
     setTimeout(() => {
       const vInput = document.getElementById("videoInput") || videoInput;
       if (vInput && vInput.files && vInput.files.length > 0) {
         handleFileSelected(vInput.files[0]);
       }
     }, 300);
   });
   ```

2. **Validación Tolerante de Formatos:**
   Acepta tipos MIME de video, extensiones válidas y archivos genéricos (`application/octet-stream` o sin MIME) típicos de teléfonos móviles:
   ```javascript
   function handleFileSelected(file) {
     if (!file) return;

     const isVideoMime = file.type && file.type.startsWith("video/");
     const isVideoExt = /\.(mp4|mov|m4v|webm|mkv|3gp|avi|flv|wmv)$/i.test(file.name || "");
     const isMobileGeneric = !file.type || file.type === "application/octet-stream" || file.type === "";

     if (file.type && !isVideoMime && !isMobileGeneric && !isVideoExt) {
       alert("Por favor selecciona un archivo de video válido (.mp4 o .mov).");
       if (videoInput) videoInput.value = "";
       return;
     }

     const sizeMB = file.size / (1024 * 1024);
     if (sizeMB > 500) {
       alert(`El video pesa ${sizeMB.toFixed(1)} MB. El límite máximo es de 500 MB.`);
       if (videoInput) videoInput.value = "";
       return;
     }

     currentFile = file;

     if (fileNameBadge) {
       const displayName = file.name || "video_noticia.mp4";
       fileNameBadge.textContent = `Archivo: ${displayName} (${sizeMB.toFixed(1)} MB)`;
       fileNameBadge.style.display = "inline-block";
     }

     if (dropzonePrimaryText) {
       dropzonePrimaryText.textContent = "¡Video cargado! Toca abajo para procesar";
     }

     if (dropzoneContainer) {
       dropzoneContainer.style.borderColor = "#0066FF";
       dropzoneContainer.style.background = "rgba(0, 102, 255, 0.1)";
     }

     if (processBtn) {
       processBtn.disabled = false;
       processBtn.style.opacity = "1";
       processBtn.style.cursor = "pointer";
     }

     if (navigator.vibrate) {
       try { navigator.vibrate([40, 30, 40]); } catch (err) {}
     }
   }
   ```

3. **Purgado de Service Workers:**
   Desmantela de forma proactiva cualquier caché residual previa en navegadores móviles:
   ```javascript
   if ('serviceWorker' in navigator) {
     navigator.serviceWorker.getRegistrations().then(registrations => {
       for (let registration of registrations) {
         registration.unregister();
       }
     });
   }
   if ('caches' in window) {
     caches.keys().then(names => {
       for (let name of names) {
         caches.delete(name);
       }
     });
   }
   ```

---

## 3. CONFIGURACIÓN ANTI-CACHÉ VERCEL (`vercel.json`)
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "no-cache, no-store, must-revalidate, max-age=0" },
        { "key": "Pragma", "value": "no-cache" },
        { "key": "Expires", "value": "0" }
      ]
    }
  ]
}
```

---

## 4. ESTADO DE LOS SERVICIOS

| Componente | Plataforma | Estado | Versión |
| :--- | :--- | :--- | :--- |
| **Frontend Web** | Vercel Edge | **ONLINE** | `v2.2.0` |
| **Backend API** | Hugging Face (ZeroGPU) | **ONLINE** (`/gradio_api/v1`) | Operativo |
| **Repositorio Git** | GitHub | **SINCRONIZADO (`main`)** | `Arepita26/marino-editor` |
| **Selector Android** | Storage Access Framework | **RESTAURADO** | Clásico / Recientes |
