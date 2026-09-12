import React from "react";
import { shareVideoToWhatsApp } from "../services/api";

interface Props {
  downloadUrl: string;
  onReset: () => void;
}

export const ResultCard: React.FC<Props> = ({ downloadUrl, onReset }) => {
  const handleShare = async () => {
    try {
      // Intentar obtener el blob para compartir el archivo directamente por WhatsApp / sistema
      const res = await fetch(downloadUrl);
      if (res.ok) {
        const blob = await res.blob();
        await shareVideoToWhatsApp(blob);
      } else {
        await shareVideoToWhatsApp(downloadUrl);
      }
    } catch {
      await shareVideoToWhatsApp(downloadUrl);
    }
  };

  return (
    <section className="main-card" aria-labelledby="result-title">
      <div className="success-banner">
        <span style={{ fontSize: "28px" }}>✅</span>
        <h2 id="result-title" style={{ fontSize: "22px", fontWeight: 800 }}>
          ¡Tu video está listo!
        </h2>
      </div>

      <p className="card-desc">
        La intro de Marino Alvarado ha sido unida correctamente con tu video en formato vertical (1080x1920) y audio nivelado.
      </p>

      {/* Reproductor de previsualización */}
      <video
        src={downloadUrl}
        controls
        playsInline
        className="video-player-preview"
      />

      {/* Botón 1: Descargar Video Listo */}
      <a
        href={downloadUrl}
        download="90_segundos_marino_alvarado.mp4"
        className="btn-download-giant"
        id="btn-download-video"
      >
        <span style={{ fontSize: "24px" }}>⬇️</span>
        <span>Descargar Video Listo</span>
      </a>

      {/* Botón 2: Compartir en WhatsApp */}
      <button
        type="button"
        className="btn-whatsapp-giant"
        onClick={handleShare}
        id="btn-share-whatsapp"
      >
        <span style={{ fontSize: "24px" }}>💬</span>
        <span>Compartir directo en WhatsApp</span>
      </button>

      {/* Botón 3: Hacer otro video */}
      <button
        type="button"
        className="btn-reset-secondary"
        onClick={onReset}
        id="btn-new-video"
      >
        🔄 Hacer otro video
      </button>
    </section>
  );
};
