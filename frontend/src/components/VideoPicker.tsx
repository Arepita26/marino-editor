import React, { useRef } from "react";
import { VideoMetadata } from "../types";

interface Props {
  selectedVideo: VideoMetadata | null;
  onVideoSelected: (meta: VideoMetadata) => void;
  onStartProcessing: () => void;
  isProcessing: boolean;
}

const MAX_MB_CLIENT = 500;

export const VideoPicker: React.FC<Props> = ({
  selectedVideo,
  onVideoSelected,
  onStartProcessing,
  isProcessing,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check size limit: 500 MB
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > MAX_MB_CLIENT) {
      alert(`El video pesa ${sizeMB.toFixed(1)} MB. El límite máximo permitido es de ${MAX_MB_CLIENT} MB.`);
      return;
    }

    const previewUrl = URL.createObjectURL(file);
    const meta: VideoMetadata = {
      file,
      name: file.name,
      sizeBytes: file.size,
      sizeFormatted: `${sizeMB.toFixed(1)} MB`,
      previewUrl,
    };

    onVideoSelected(meta);

    // Subtle haptic feedback on mobile devices if available
    if (typeof navigator !== "undefined" && navigator.vibrate) {
      navigator.vibrate(40);
    }
  };

  const triggerSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <section className="main-card" aria-labelledby="picker-title">
      <span className="step-label">Paso 1 de 2</span>
      <h2 id="picker-title" className="card-title">
        Elige o graba tu video
      </h2>
      <p className="card-desc">
        Toca el botón azul para elegir tu video grabado desde la galería o la cámara de tu teléfono.
      </p>

      {/* Input nativo oculto compatible con cámara y galería */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/*"
        onChange={handleFileChange}
        style={{ display: "none" }}
        id="video-file-input"
      />

      {/* Botón 1 Gigante: Elegir Video */}
      <button
        type="button"
        className="btn-upload-giant"
        onClick={triggerSelect}
        id="btn-select-video"
      >
        <span style={{ fontSize: "26px" }}>📁</span>
        <span>1. Elegir Video</span>
      </button>

      {/* Caja de información del clip seleccionado */}
      {selectedVideo && (
        <div className="clip-preview-box">
          <div className="clip-info-row">
            <span className="clip-name">📹 {selectedVideo.name}</span>
            <span className="clip-badge">{selectedVideo.sizeFormatted}</span>
          </div>
        </div>
      )}

      {/* Botón 2: Pegar Intro y Procesar */}
      <button
        type="button"
        className="btn-process-giant"
        disabled={!selectedVideo || isProcessing}
        onClick={onStartProcessing}
        id="btn-start-process"
      >
        <span>🎬</span>
        <span>2. Pegar Intro y Procesar</span>
      </button>
    </section>
  );
};
