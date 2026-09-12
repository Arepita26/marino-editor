import React, { useState } from "react";
import { Header } from "./components/Header";
import { UpdatePrompt } from "./components/UpdatePrompt";
import { VideoPicker } from "./components/VideoPicker";
import { ProcessingState } from "./components/ProcessingState";
import { ResultCard } from "./components/ResultCard";
import { SecurityNotice } from "./components/SecurityNotice";
import { VideoMetadata, ProcessState } from "./types";
import { uploadVideoWithProgress, pollTicketStatus, getApiBaseUrl, setApiBaseUrl } from "./services/api";

export const App: React.FC = () => {
  const [state, setState] = useState<ProcessState>("IDLE");
  const [selectedVideo, setSelectedVideo] = useState<VideoMetadata | null>(null);
  
  // Progress states
  const [isUploading, setIsUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [uploadedMB, setUploadedMB] = useState("0");
  const [totalMB, setTotalMB] = useState("0");
  const [stepMessage, setStepMessage] = useState("");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  
  // Backend config modal / input
  const [showConfig, setShowConfig] = useState(false);
  const [backendUrl, setBackendInput] = useState(getApiBaseUrl());

  const handleVideoSelected = (meta: VideoMetadata) => {
    setSelectedVideo(meta);
    setState("SELECTED");
    setErrorMessage("");
  };

  const handleStartProcessing = async () => {
    if (!selectedVideo) return;

    setState("UPLOADING");
    setIsUploading(true);
    setUploadPercent(0);
    setErrorMessage("");
    setStepMessage("Iniciando subida segura...");

    try {
      // 1. Subida del archivo por XHR con progreso real
      const { ticketId } = await uploadVideoWithProgress(
        selectedVideo.file,
        (percent, loaded, total) => {
          setUploadPercent(percent);
          setUploadedMB(loaded);
          setTotalMB(total);
          if (percent >= 100) {
            setStepMessage("Video subido. Iniciando ensamblaje con la intro de Marino Alvarado...");
          }
        }
      );

      // 2. Polling asíncrono
      setIsUploading(false);
      setState("PROCESSING");
      setStepMessage("Uniendo con la intro de Marino Alvarado (1080x1920) y ecualizando audio...");

      const finalTicket = await pollTicketStatus(ticketId, (update) => {
        if (update.progress) {
          setUploadPercent(update.progress);
        }
        if (update.step) {
          setStepMessage(update.step);
        }
      });

      // 3. Completado
      setDownloadUrl(finalTicket.downloadUrl || `${getApiBaseUrl()}/api/descargar/${ticketId}`);
      setState("COMPLETED");

      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate([100, 50, 100]);
      }
    } catch (err: any) {
      console.error("Error en procesamiento:", err);
      // Simulación en caso de entorno local sin backend encendido aún
      const isNetworkError = err.message?.includes("conexión") || err.message?.includes("Network");
      if (isNetworkError && window.confirm("¿El backend en Hugging Face aún no está corriendo? ¿Deseas probar la simulación completa de la interfaz?")) {
        simulateProcessingFlow();
        return;
      }

      setErrorMessage(err.message || "Ocurrió un error al procesar el video.");
      setState("ERROR");
    }
  };

  // Modo de simulación para pruebas directas en navegadores
  const simulateProcessingFlow = () => {
    setIsUploading(true);
    setState("UPLOADING");
    let p = 0;
    const interval = setInterval(() => {
      p += 15;
      if (p <= 100) {
        setUploadPercent(p);
        setUploadedMB((p * 0.25).toFixed(1));
        setTotalMB("25.0");
      } else {
        clearInterval(interval);
        setIsUploading(false);
        setState("PROCESSING");
        setStepMessage("Ensamblando con la intro de Marino Alvarado (Simulación activa)...");
        setTimeout(() => {
          setDownloadUrl(selectedVideo?.previewUrl || "");
          setState("COMPLETED");
        }, 2500);
      }
    }, 400);
  };

  const handleReset = () => {
    setState("IDLE");
    setSelectedVideo(null);
    setUploadPercent(0);
    setDownloadUrl("");
    setErrorMessage("");
  };

  const saveBackendUrl = () => {
    setApiBaseUrl(backendUrl);
    setShowConfig(false);
    alert("URL del backend actualizada.");
  };

  return (
    <div className="app-container">
      <Header />
      <UpdatePrompt />

      <main>
        {/* Error banner si algo falla */}
        {state === "ERROR" && (
          <div
            style={{
              backgroundColor: "rgba(220, 38, 38, 0.1)",
              border: "2px solid var(--color-error)",
              borderRadius: "var(--radius-md)",
              padding: "16px",
              marginBottom: "20px",
              color: "var(--color-error)",
              fontWeight: 700,
            }}
          >
            <p>⚠️ {errorMessage}</p>
            <button
              onClick={handleReset}
              className="btn-reset-secondary"
              style={{ marginTop: "12px" }}
            >
              Intentar de nuevo
            </button>
          </div>
        )}

        {/* ESTADO 1: SELECCIÓN */}
        {(state === "IDLE" || state === "SELECTED") && (
          <VideoPicker
            selectedVideo={selectedVideo}
            onVideoSelected={handleVideoSelected}
            onStartProcessing={handleStartProcessing}
            isProcessing={false}
          />
        )}

        {/* ESTADO 2: CARGA Y PROCESAMIENTO */}
        {(state === "UPLOADING" || state === "PROCESSING") && (
          <ProcessingState
            isUploading={isUploading}
            uploadPercent={uploadPercent}
            uploadedMB={uploadedMB}
            totalMB={totalMB}
            stepMessage={stepMessage}
          />
        )}

        {/* ESTADO 3: RESULTADO LISTO */}
        {state === "COMPLETED" && (
          <ResultCard downloadUrl={downloadUrl} onReset={handleReset} />
        )}

        {/* Acceso a configuración del backend */}
        <div style={{ textAlign: "center", margin: "16px 0" }}>
          <button
            type="button"
            onClick={() => setShowConfig(!showConfig)}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              fontSize: "14px",
              textDecoration: "underline",
              cursor: "pointer",
            }}
          >
            ⚙️ Configurar servidor de procesamiento
          </button>
          {showConfig && (
            <div
              style={{
                marginTop: "12px",
                padding: "14px",
                background: "var(--bg-card)",
                border: "1px solid var(--border-color)",
                borderRadius: "var(--radius-md)",
              }}
            >
              <label style={{ display: "block", fontSize: "14px", fontWeight: 700, marginBottom: "6px" }}>
                URL del Backend (Hugging Face Spaces):
              </label>
              <input
                type="text"
                value={backendUrl}
                onChange={(e) => setBackendInput(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px",
                  borderRadius: "8px",
                  border: "1px solid var(--border-color)",
                  marginBottom: "8px",
                  background: "var(--bg-card-secondary)",
                  color: "var(--text-primary)",
                  fontSize: "14px",
                }}
              />
              <button
                type="button"
                onClick={saveBackendUrl}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "var(--color-primary)",
                  color: "#fff",
                  border: "none",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Guardar URL
              </button>
            </div>
          )}
        </div>
      </main>

      <SecurityNotice />
    </div>
  );
};
export default App;
