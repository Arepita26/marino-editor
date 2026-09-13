// ==========================================================================
// MARINO EDITOR — SUITE DE VIDEO AUTOMATIZADA
// Versión: 2.1.0 (Fix Definitivo Selección Móvil & Despacho Táctil)
// ==========================================================================

// 1. AUTOLIMPIEZA DE SERVICE WORKERS ANTERIORES Y CACHÉ RESIDUAL
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(registrations => {
    for (let registration of registrations) {
      registration.unregister();
    }
  }).catch(() => {});
}

if ('caches' in window) {
  caches.keys().then(names => {
    for (let name of names) {
      caches.delete(name);
    }
  }).catch(() => {});
}

(function () {
  // 2. CONTROL DE TEMA VISUAL (MODO OSCURO / CLARO)
  const THEME_KEY = "marino_suite_theme";
  const htmlEl = document.documentElement;
  const btnTheme = document.getElementById("btn-theme-toggle");
  const themeIcon = document.getElementById("theme-icon");

  function setAppTheme(theme) {
    htmlEl.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
    const isDark = theme === "dark";
    if (themeIcon) themeIcon.textContent = isDark ? "☀️" : "🌙";
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", isDark ? "#09090B" : "#EEF2F6");
  }

  const initialTheme = localStorage.getItem(THEME_KEY) || "dark";
  setAppTheme(initialTheme);

  if (btnTheme) {
    btnTheme.addEventListener("click", () => {
      const current = htmlEl.getAttribute("data-theme") || "dark";
      setAppTheme(current === "dark" ? "light" : "dark");
    });
  }

  // 3. ELEMENTOS DE LA INTERFAZ
  const viewForm = document.getElementById("view-form");
  const viewProgress = document.getElementById("view-progress");
  const viewResult = document.getElementById("view-result");

  const videoInput = document.getElementById("videoInput") || document.getElementById("file-input-video");
  const fileNameBadge = document.getElementById("selectedFileName");
  const dropzoneContainer = document.getElementById("dropzoneContainer") || document.getElementById("dropzone-box");
  const dropzonePrimaryText = document.getElementById("dropzonePrimaryText") || document.querySelector(".primary-text");
  const processBtn = document.getElementById("btnProcesar") || document.getElementById("processButton") || document.getElementById("btn-process-action");

  const progressFillBar = document.getElementById("progress-fill-bar");
  const progressPercentLabel = document.getElementById("progress-percent-label");
  const progressBytesLabel = document.getElementById("progress-bytes-label");
  const progressLiveMessage = document.getElementById("progress-live-message");
  const btnCancelProcessing = document.getElementById("btn-cancel-processing");

  const finalVideoPlayer = document.getElementById("final-video-player");
  const btnDownloadFile = document.getElementById("btn-download-file");
  const btnShareWhatsapp = document.getElementById("btn-share-whatsapp");
  const btnProcessAnother = document.getElementById("btn-process-another");

  let currentFile = null;
  let processedDownloadUrl = "";
  let currentXhr = null;
  let currentPollTimer = null;
  let currentTicketId = null;

  // Configuración de Servidor Backend (Hugging Face ZeroGPU / Local)
  const DEFAULT_HF_BACKEND = "https://arepita26-marino-editor-api.hf.space/gradio_api/v1";
  const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  const urlBackendParam = new URLSearchParams(window.location.search).get("backend");
  if (urlBackendParam) {
    try { localStorage.setItem("marino_backend_url", urlBackendParam); } catch (e) {}
  }
  let BACKEND_URL = localStorage.getItem("marino_backend_url") || (isLocalhost ? "http://127.0.0.1:7860" : DEFAULT_HF_BACKEND);
  if (BACKEND_URL.includes("arepita26-marino-editor-api.hf.space") && !BACKEND_URL.includes("/gradio_api/v1")) {
    BACKEND_URL = DEFAULT_HF_BACKEND;
    try { localStorage.setItem("marino_backend_url", BACKEND_URL); } catch (e) {}
  }

  // 4. LÓGICA DE SELECCIÓN DE ARCHIVOS
  // ATENCIÓN: NUNCA agregar listener 'click' con videoInput.value = '' en móviles,
  // porque iOS Safari y Chrome Android despachan un 'click' sintético al volver de la galería
  // y borraban inmediatamente el archivo recién seleccionado.

  function handleFileSelected(file) {
    if (!file) return;

    // Validación tolerante: si viene de accept="video/*" o tiene extensión/mime de video, o es genérico móvil
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

    // Actualizar badge visual con el nombre y tamaño
    if (fileNameBadge) {
      const displayName = file.name || "video_seleccionado.mp4";
      fileNameBadge.textContent = `Archivo: ${displayName} (${sizeMB.toFixed(1)} MB)`;
      fileNameBadge.style.display = "inline-block";
    }

    if (dropzonePrimaryText) {
      dropzonePrimaryText.textContent = "¡Video seleccionado! Toca abajo para procesar";
    }

    if (dropzoneContainer) {
      dropzoneContainer.style.borderColor = "#0066FF";
      dropzoneContainer.style.background = "rgba(0, 102, 255, 0.1)";
    }

    // Habilitar botón de procesar con estilo activo
    if (processBtn) {
      processBtn.disabled = false;
      processBtn.style.opacity = "1";
      processBtn.style.cursor = "pointer";
    }

    // Vibración de confirmación en móviles
    if (navigator.vibrate) {
      try { navigator.vibrate([40, 30, 40]); } catch (err) {}
    }
  }

  if (videoInput) {
    videoInput.addEventListener("change", function (e) {
      const files = (e.target && e.target.files) || (videoInput && videoInput.files);
      if (files && files.length > 0) {
        handleFileSelected(files[0]);
      }
    });

    videoInput.addEventListener("input", function (e) {
      const files = (e.target && e.target.files) || (videoInput && videoInput.files);
      if (files && files.length > 0) {
        handleFileSelected(files[0]);
      }
    });
  }

  // Soporte Desktop Drag & Drop
  if (dropzoneContainer && videoInput) {
    dropzoneContainer.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzoneContainer.classList.add("drag-over");
    });
    dropzoneContainer.addEventListener("dragleave", () => {
      dropzoneContainer.classList.remove("drag-over");
    });
    dropzoneContainer.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzoneContainer.classList.remove("drag-over");
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });
  }

  // 5. ROTADOR DINÁMICO DE FRASES DE PROGRESO
  const PROGRESS_PHRASES = [
    "Iniciando procesamiento de video...",
    "El video se está procesando correctamente...",
    "Normalizando resolución a vertical 1080x1920...",
    "Nivelando y ecualizando audio con estándar EBU R128...",
    "¡Ya falta poco, ensamblando con la intro oficial!...",
    "Generando archivo final en alta resolución..."
  ];
  let phraseTimer = null;
  let phraseIdx = 0;

  function updateProgressMessage(text) {
    if (!progressLiveMessage) return;
    progressLiveMessage.style.opacity = "0";
    setTimeout(() => {
      progressLiveMessage.textContent = text;
      progressLiveMessage.style.opacity = "1";
    }, 150);
  }

  function startStatusPhraseRotation() {
    phraseIdx = 0;
    if (progressLiveMessage) {
      progressLiveMessage.style.opacity = "1";
      progressLiveMessage.textContent = PROGRESS_PHRASES[0];
    }
    if (phraseTimer) clearInterval(phraseTimer);
    phraseTimer = setInterval(() => {
      phraseIdx = (phraseIdx + 1) % PROGRESS_PHRASES.length;
      updateProgressMessage(PROGRESS_PHRASES[phraseIdx]);
    }, 2800);
  }

  function stopStatusPhraseRotation(finalMsg) {
    if (phraseTimer) {
      clearInterval(phraseTimer);
      phraseTimer = null;
    }
    if (progressLiveMessage) {
      progressLiveMessage.style.opacity = "1";
      if (finalMsg) progressLiveMessage.textContent = finalMsg;
    }
  }

  // 6. CANCELACIÓN
  if (btnCancelProcessing) {
    btnCancelProcessing.addEventListener("click", () => {
      if (currentXhr) {
        try { currentXhr.abort(); } catch (e) {}
        currentXhr = null;
      }
      if (currentPollTimer) {
        clearInterval(currentPollTimer);
        currentPollTimer = null;
      }
      if (currentTicketId) {
        fetch(`${BACKEND_URL}/api/cancelar/${currentTicketId}`, { method: "POST" }).catch(() => {});
        currentTicketId = null;
      }
      stopStatusPhraseRotation();
      if (viewProgress) viewProgress.style.display = "none";
      if (viewForm) viewForm.style.display = "block";
      if (progressFillBar) progressFillBar.style.width = "0%";
      if (progressPercentLabel) progressPercentLabel.textContent = "0%";
    });
  }

  // 7. INICIAR PROCESAMIENTO
  if (processBtn) {
    processBtn.addEventListener("click", async () => {
      if (!currentFile) return;

      if (viewForm) viewForm.style.display = "none";
      if (viewProgress) viewProgress.style.display = "block";
      if (viewResult) viewResult.style.display = "none";

      if (progressFillBar) progressFillBar.style.width = "0%";
      if (progressPercentLabel) progressPercentLabel.textContent = "0%";
      if (progressBytesLabel) {
        progressBytesLabel.textContent = `0.0 MB / ${(currentFile.size / (1024 * 1024)).toFixed(1)} MB`;
      }

      startStatusPhraseRotation();

      // Verificar conexión con el backend
      let isOnline = false;
      for (let attempt = 1; attempt <= 4; attempt++) {
        try {
          updateProgressMessage(attempt > 1 ? `Conectando con el servidor en la nube (intento ${attempt}/4)...` : "Verificando disponibilidad del servidor de renderizado...");
          const check = await fetch(BACKEND_URL + "/api/health", { cache: "no-store" });
          if (check.ok) {
            const data = await check.json();
            if (data.status === "online") {
              isOnline = true;
              break;
            }
          }
        } catch (e) {
          console.warn("Intento de conexión:", e);
        }
        if (attempt < 4) await new Promise(r => setTimeout(r, 2000));
      }

      if (isOnline) {
        processWithServer();
      } else {
        stopStatusPhraseRotation();
        alert("No se pudo conectar con el servidor de renderizado de Marino. Por favor espera unos segundos e intenta nuevamente mientras el servidor en la nube arranca.");
        if (viewProgress) viewProgress.style.display = "none";
        if (viewForm) viewForm.style.display = "block";
      }
    });
  }

  function processWithServer() {
    const xhr = new XMLHttpRequest();
    currentXhr = xhr;
    const formData = new FormData();
    formData.append("file", currentFile);

    xhr.upload.addEventListener("progress", (evt) => {
      if (evt.lengthComputable) {
        const pct = Math.round((evt.loaded / evt.total) * 100);
        const loadedMB = (evt.loaded / (1024 * 1024)).toFixed(1);
        const totalMB = (evt.total / (1024 * 1024)).toFixed(1);
        const visualPct = Math.round(pct * 0.4);
        if (progressFillBar) progressFillBar.style.width = visualPct + "%";
        if (progressPercentLabel) progressPercentLabel.textContent = visualPct + "%";
        if (progressBytesLabel) progressBytesLabel.textContent = `${loadedMB} MB / ${totalMB} MB`;
      }
    });

    xhr.addEventListener("load", () => {
      currentXhr = null;
      if (xhr.status >= 200 && xhr.status < 300) {
        const data = JSON.parse(xhr.responseText);
        currentTicketId = data.ticket_id;
        pollServerJob(data.ticket_id);
      } else {
        let errorMsg = `Error del servidor (${xhr.status}).`;
        try {
          const errData = JSON.parse(xhr.responseText);
          if (errData.detail) errorMsg = errData.detail;
        } catch (e) {}
        stopStatusPhraseRotation();
        alert(errorMsg);
        if (viewProgress) viewProgress.style.display = "none";
        if (viewForm) viewForm.style.display = "block";
      }
    });

    xhr.addEventListener("error", () => {
      currentXhr = null;
      stopStatusPhraseRotation();
      alert("Error de conexión al enviar el video al servidor. Por favor verifica tu conexión.");
      if (viewProgress) viewProgress.style.display = "none";
      if (viewForm) viewForm.style.display = "block";
    });

    xhr.open("POST", BACKEND_URL + "/api/procesar");
    xhr.send(formData);
  }

  function pollServerJob(ticketId) {
    let consecutiveErrors = 0;
    currentPollTimer = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/status/${ticketId}`);
        if (res.ok) {
          consecutiveErrors = 0;
          const data = await res.json();
          if (data.progress && progressFillBar && progressPercentLabel) {
            progressFillBar.style.width = data.progress + "%";
            progressPercentLabel.textContent = data.progress + "%";
          }

          if (data.status === "completado") {
            clearInterval(currentPollTimer);
            currentPollTimer = null;
            currentTicketId = null;
            stopStatusPhraseRotation("¡Video ensamblado con éxito con la intro de Marino!");
            processedDownloadUrl = `${BACKEND_URL}/api/descargar/${ticketId}.mp4`;
            showFinishedResult(processedDownloadUrl);
          } else if (data.status === "error") {
            clearInterval(currentPollTimer);
            currentPollTimer = null;
            currentTicketId = null;
            stopStatusPhraseRotation();
            alert("Error en el procesamiento del video: " + (data.error || "Desconocido"));
            if (viewProgress) viewProgress.style.display = "none";
            if (viewForm) viewForm.style.display = "block";
          }
        } else {
          consecutiveErrors++;
          if (consecutiveErrors > 10) {
            clearInterval(currentPollTimer);
            currentPollTimer = null;
            stopStatusPhraseRotation();
            alert("Se perdió la comunicación con el servidor durante el procesamiento.");
            if (viewProgress) viewProgress.style.display = "none";
            if (viewForm) viewForm.style.display = "block";
          }
        }
      } catch (e) {
        consecutiveErrors++;
        if (consecutiveErrors > 10) {
          clearInterval(currentPollTimer);
          currentPollTimer = null;
          stopStatusPhraseRotation();
          alert("Error de conexión mientras se procesaba el video.");
          if (viewProgress) viewProgress.style.display = "none";
          if (viewForm) viewForm.style.display = "block";
        }
      }
    }, 1500);
  }

  // 8. MOSTRAR RESULTADO (VIDEO VERTICAL 9:16)
  function showFinishedResult(videoUrl) {
    if (viewProgress) viewProgress.style.display = "none";
    if (viewResult) viewResult.style.display = "block";

    if (finalVideoPlayer) {
      finalVideoPlayer.pause();
      finalVideoPlayer.src = videoUrl;
      finalVideoPlayer.currentTime = 0;
      finalVideoPlayer.load();
    }
  }

  // 9. GENERADOR DE NOMBRE CON FECHA EXACTA
  const MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
  ];

  function getDatedFilename() {
    const now = new Date();
    const day = now.getDate();
    const month = MESES_ES[now.getMonth()];
    const year = now.getFullYear();
    return `${day}_de_${month}_de_${year}.mp4`;
  }

  // 10. DESCARGAR VIDEO
  if (btnDownloadFile) {
    btnDownloadFile.addEventListener("click", async (e) => {
      e.preventDefault();
      const filename = getDatedFilename();

      try {
        const res = await fetch(processedDownloadUrl);
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(new Blob([blob], { type: "video/mp4" }));

        const a = document.createElement("a");
        a.style.display = "none";
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(blobUrl);
        }, 2000);
      } catch (err) {
        const a = document.createElement("a");
        a.href = processedDownloadUrl;
        a.download = filename;
        a.click();
      }
    });
  }

  // 11. COMPARTIR EN WHATSAPP
  if (btnShareWhatsapp) {
    btnShareWhatsapp.addEventListener("click", async () => {
      const filename = getDatedFilename();
      const readableDate = filename.replace(".mp4", "").replace(/_/g, " ");

      if (navigator.canShare && processedDownloadUrl) {
        try {
          const res = await fetch(processedDownloadUrl);
          const blob = await res.blob();
          const file = new File([blob], filename, { type: "video/mp4" });
          if (navigator.canShare({ files: [file] })) {
            await navigator.share({
              files: [file],
              title: "90 Segundos con Marino Alvarado",
              text: `Video listo de 90 Segundos con Marino Alvarado — ${readableDate}`
            });
            return;
          }
        } catch (e) {
          console.warn("navigator.share no disponible para archivos:", e);
        }
      }
      const text = encodeURIComponent(`¡Hola! Aquí está el video listo (${readableDate}) de 90 Segundos con Marino Alvarado para La TV Calle.`);
      window.open(`https://api.whatsapp.com/send?text=${text}`, "_blank");
    });
  }

  // 12. PROCESAR OTRO VIDEO
  if (btnProcessAnother) {
    btnProcessAnother.addEventListener("click", () => {
      currentFile = null;
      processedDownloadUrl = "";
      if (videoInput) videoInput.value = "";
      if (fileNameBadge) {
        fileNameBadge.textContent = "";
        fileNameBadge.style.display = "none";
      }
      if (dropzonePrimaryText) {
        dropzonePrimaryText.textContent = "Toca aquí para seleccionar el video";
      }
      if (dropzoneContainer) {
        dropzoneContainer.style.borderColor = "";
        dropzoneContainer.style.background = "";
      }
      if (processBtn) {
        processBtn.disabled = true;
        processBtn.style.opacity = "";
      }

      if (viewForm) viewForm.style.display = "block";
      if (viewProgress) viewProgress.style.display = "none";
      if (viewResult) viewResult.style.display = "none";

      if (finalVideoPlayer) {
        finalVideoPlayer.pause();
        finalVideoPlayer.src = "";
      }
    });
  }
})();
