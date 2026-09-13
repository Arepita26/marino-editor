import { ProcessingTicket } from "../types";

// Permite cambiar la URL del backend de Hugging Face desde localStorage o variable de entorno
const DEFAULT_API_URL = (import.meta as any).env?.VITE_API_URL || "https://arepita26-marino-editor-api.hf.space";

export function getApiBaseUrl(): string {
  if (typeof window !== "undefined") {
    const custom = localStorage.getItem("marino_backend_url");
    if (custom) return custom;
  }
  return DEFAULT_API_URL;
}

export function setApiBaseUrl(url: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("marino_backend_url", url);
  }
}

/**
 * Realiza la subida directa del archivo de video mediante XMLHttpRequest
 * para obtener el progreso de carga byte a byte en tiempo real.
 */
export function uploadVideoWithProgress(
  file: File,
  onProgress: (percent: number, loadedMB: string, totalMB: string) => void
): Promise<{ ticketId: string }> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);

    const baseUrl = getApiBaseUrl();
    const endpoint = `${baseUrl}/api/procesar`;

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        const loadedMB = (event.loaded / (1024 * 1024)).toFixed(1);
        const totalMB = (event.total / (1024 * 1024)).toFixed(1);
        onProgress(percent, loadedMB, totalMB);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve({ ticketId: response.ticket_id });
        } catch (err) {
          reject(new Error("Respuesta inválida del servidor."));
        }
      } else {
        try {
          const errRes = JSON.parse(xhr.responseText);
          reject(new Error(errRes.detail || `Error del servidor (${xhr.status})`));
        } catch {
          reject(new Error(`Fallo de conexión con el servidor (${xhr.status})`));
        }
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Error de conexión al subir el video. Comprueba tu red o la URL del backend."));
    });

    xhr.addEventListener("abort", () => {
      reject(new Error("Subida cancelada por el usuario."));
    });

    xhr.open("POST", endpoint);
    xhr.send(formData);
  });
}

/**
 * Consulta el estado del procesamiento cada 3.5 segundos.
 */
export async function pollTicketStatus(
  ticketId: string,
  onUpdate: (ticket: ProcessingTicket) => void,
  intervalMs = 3500
): Promise<ProcessingTicket> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/status/${ticketId}`;

  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const res = await fetch(endpoint, { cache: "no-store" });
        if (!res.ok) {
          throw new Error(`Error consultando estado (${res.status})`);
        }
        const data = await res.json();
        const ticket: ProcessingTicket = {
          ticketId: data.ticket_id,
          status: data.status,
          progress: data.progress || 50,
          step: data.step,
          error: data.error,
          downloadUrl: `${baseUrl}/api/descargar/${ticketId}`,
        };

        onUpdate(ticket);

        if (ticket.status === "completado") {
          clearInterval(timer);
          resolve(ticket);
        } else if (ticket.status === "error") {
          clearInterval(timer);
          reject(new Error(ticket.error || "Error durante el procesamiento del video."));
        }
      } catch (err) {
        clearInterval(timer);
        reject(err);
      }
    }, intervalMs);
  });
}

/**
 * Comparte el video procesado en WhatsApp o en la hoja nativa del teléfono.
 */
export async function shareVideoToWhatsApp(
  videoBlobOrUrl: Blob | string,
  title = "90 Segundos con Marino Alvarado"
): Promise<boolean> {
  // 1. Probar Web Share API nivel 2 (archivos directos en iOS y Android)
  if (navigator.canShare && videoBlobOrUrl instanceof Blob) {
    const file = new File([videoBlobOrUrl], "90_segundos_marino_alvarado.mp4", {
      type: "video/mp4",
    });
    if (navigator.canShare({ files: [file] })) {
      try {
        await navigator.share({
          files: [file],
          title: title,
          text: "¡Aquí está el video editado de 90 Segundos con Marino Alvarado para La TV Calle!",
        });
        return true;
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.warn("Fallo al compartir archivo directamente:", err);
        }
      }
    }
  }

  // 2. Fallback: Enlace directo de WhatsApp con mensaje
  const text = encodeURIComponent(
    `¡Hola! Aquí está el video listo de *90 Segundos con Marino Alvarado* para La TV Calle.`
  );
  window.open(`https://api.whatsapp.com/send?text=${text}`, "_blank");
  return true;
}
