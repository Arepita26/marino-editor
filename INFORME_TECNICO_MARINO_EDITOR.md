# INFORME TÉCNICO DE PRODUCCIÓN: DESCARGA SEGURA BLOB, WEB SHARE API Y REFINAMIENTO v2.3.0

**Proyecto:** Marino Editor — Suite de Video Automatizada (90 Segundos con Marino Alvarado)  
**Fecha:** 13 de Septiembre de 2026  
**Versión Actual:** `v2.3.0`  
**Repositorio GitHub:** [https://github.com/Arepita26/marino-editor](https://github.com/Arepita26/marino-editor) (Rama `main`)  
**Frontend en Producción (Vercel):** [https://marino-editor.vercel.app](https://marino-editor.vercel.app)  
**Backend en Producción (Hugging Face Spaces):** [https://arepita26-marino-editor-api.hf.space/gradio_api/v1](https://arepita26-marino-editor-api.hf.space/gradio_api/v1)  
**Autor Git:** `Arepita26 <rosaserick26@gmail.com>`  

---

## 1. REFINAMIENTOS VISUALES SOLICITADOS POR EL USUARIO

1. **Eliminación del Badge Azul con Nombre de Archivo:**
   * Se retiró el elemento `<span id="selectedFileName" class="file-name-badge"></span>` de la interfaz.
   * Ahora, cuando el usuario selecciona un video, la tarjeta de carga se mantiene limpia y minimalista, mostrando únicamente el texto: *"¡Video cargado! Toca abajo para procesar"*, el borde activo y el botón principal *"Procesar Video"* listo.
2. **Eliminación del Botón Separado de WhatsApp:**
   * Se eliminó el botón verde individual de WhatsApp de la pantalla de resultados.
   * La acción se unificó en el botón principal **"Descargar Video"**, el cual activa la **Web Share API** nativa en dispositivos móviles. Esto permite al usuario elegir directamente entre enviar el video a WhatsApp, Telegram o guardarlo directamente en su Galería de Fotos/Videos del teléfono.

---

## 2. DIAGNÓSTICO DEL FALLO "ARCHIVO BB" / PANTALLA NEGRA EN ANDROID

En dispositivos móviles (especialmente Android 12, 13 y 14), la descarga de videos generados en segundo plano solía fallar produciendo archivos con nombres aleatorios temporales (ej. `bb78a9...bin`) o archivos de 0 bytes que la galería reproducía en negro:

1. **Revocación Prematura de ObjectURL:**
   * En navegadores de escritorio, revocar un Blob URL después de 2 segundos es seguro. Sin embargo, en teléfonos móviles Android, el gestor de descargas del sistema operativo descarga el archivo de forma asíncrona hacia el almacenamiento flash (`/storage/emulated/0/Download`).
   * Si el código ejecuta `URL.revokeObjectURL(blobUrl)` a los pocos segundos mientras Android aún está escribiendo los megabytes, el hilo de escritura se corta abruptamente. Como resultado, el teléfono almacena un archivo corrupto de 0 bytes o truncado, que la galería no puede decodificar (pantalla negra).
2. **Pérdida de Metadatos y Restricciones Cross-Origin:**
   * Si el enlace de descarga apunta a un dominio externo (`*.hf.space`), los navegadores móviles bloquean el atributo `download="nombre.mp4"` por seguridad CORS, forzando al navegador a inventar un nombre basado en el hash o UUID temporal (`bb...`).

---

## 3. SOLUCIÓN IMPLEMENTADA (ARQUITECTURA v2.3.0)

### A. Función de Descarga Segura y Web Share API (`frontend/script.js`)
```javascript
async function triggerSecureMobileDownload(videoUrl, customFileName) {
  const defaultName = getDatedFilename();
  const fileName = customFileName || defaultName;
  const originalBtnText = btnDownloadFile ? btnDownloadFile.textContent : "Descargar Video";

  if (btnDownloadFile) {
    btnDownloadFile.disabled = true;
    btnDownloadFile.textContent = "Preparando archivo para tu teléfono...";
  }

  try {
    // 1. Descargar el buffer completo como Blob para evitar bloqueos Cross-Origin
    const response = await fetch(videoUrl);
    if (!response.ok) throw new Error("No se pudo obtener el video procesado del servidor.");

    const rawBlob = await response.blob();
    // Forzar estrictamente el tipo MIME a video/mp4
    const videoBlob = new Blob([rawBlob], { type: "video/mp4" });

    // 2. Ruta A: Web Share API con archivos nativos (Compartir a WhatsApp / Guardar en Galería)
    const file = new File([videoBlob], fileName, { type: "video/mp4" });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try {
        await navigator.share({
          files: [file],
          title: "90 Segundos con Marino Alvarado",
          text: "Cápsula informativa DDHH lista para difusión."
        });
        if (btnDownloadFile) {
          btnDownloadFile.disabled = false;
          btnDownloadFile.textContent = "¡Video compartido / guardado!";
          setTimeout(() => { btnDownloadFile.textContent = originalBtnText; }, 3500);
        }
        return;
      } catch (shareErr) {
        if (shareErr.name === "AbortError") {
          if (btnDownloadFile) {
            btnDownloadFile.disabled = false;
            btnDownloadFile.textContent = originalBtnText;
          }
          return;
        }
        console.warn("Fallo Web Share, usando descarga por ancla:", shareErr);
      }
    }

    // 3. Ruta B: Fallback de descarga tradicional por ObjectURL protegido
    const blobUrl = URL.createObjectURL(videoBlob);
    const downloadAnchor = document.createElement("a");
    downloadAnchor.style.display = "none";
    downloadAnchor.href = blobUrl;
    downloadAnchor.setAttribute("download", fileName);
    downloadAnchor.setAttribute("target", "_self");

    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    document.body.removeChild(downloadAnchor);

    if (btnDownloadFile) {
      btnDownloadFile.disabled = false;
      btnDownloadFile.textContent = "¡Descarga iniciada! Revisa tus notificaciones";
      setTimeout(() => { btnDownloadFile.textContent = originalBtnText; }, 4000);
    }

    // 4. Retardo crítico: NO revocar el BlobURL antes de 60 segundos en móviles
    setTimeout(() => {
      URL.revokeObjectURL(blobUrl);
    }, 60000);

  } catch (err) {
    console.error("Error al procesar descarga móvil:", err);
    if (btnDownloadFile) {
      btnDownloadFile.disabled = false;
      btnDownloadFile.textContent = originalBtnText;
    }
    const emergencyLink = document.createElement("a");
    emergencyLink.href = videoUrl;
    emergencyLink.download = fileName;
    emergencyLink.target = "_blank";
    emergencyLink.click();
  }
}
```

### B. Cabeceras en Backend FastAPI (`backend/app/routes/video.py`):
```python
return FileResponse(
    path=str(output_path),
    media_type="video/mp4",
    filename=safe_filename,
    headers={
        "Content-Disposition": f'attachment; filename="{safe_filename}"',
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    },
)
```

---

## 4. VERIFICACIÓN Y ESTADO DE PRODUCCIÓN

| Parámetro | Estado |
| :--- | :--- |
| **Versión en Vercel** | `v2.3.0` |
| **Badge Azul** | **ELIMINADO** |
| **Botón Verde WhatsApp** | **ELIMINADO** (Sustituido por Web Share API nativo en el botón de descarga) |
| **Retención de Blob** | **60 Segundos** (Protegido contra cortes en Android) |
| **Cabeceras HTTP** | `Cache-Control: no-cache, no-store, must-revalidate, max-age=0` |
| **URL Producción** | [https://marino-editor.vercel.app](https://marino-editor.vercel.app) |
