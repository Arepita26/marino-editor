import React from "react";

interface Props {
  isUploading: boolean;
  uploadPercent: number;
  uploadedMB: string;
  totalMB: string;
  stepMessage: string;
}

export const ProcessingState: React.FC<Props> = ({
  isUploading,
  uploadPercent,
  uploadedMB,
  totalMB,
  stepMessage,
}) => {
  return (
    <section className="main-card progress-card" aria-live="polite">
      <div style={{ fontSize: "42px", marginBottom: "16px" }}>
        <span className="spinner-icon" style={{ display: "inline-block" }}>
          ⚙️
        </span>
      </div>

      <h2 className="progress-header-title">
        {isUploading ? "Subiendo video al servidor..." : "Procesando video con Marino..."}
      </h2>

      <div className="progress-track" role="progressbar" aria-valuenow={uploadPercent} aria-valuemin={0} aria-valuemax={100}>
        <div
          className="progress-fill"
          style={{ width: `${uploadPercent}%` }}
        />
      </div>

      <div className="progress-percent-label">
        {isUploading
          ? `${uploadPercent}% (${uploadedMB} MB de ${totalMB} MB)`
          : `${uploadPercent}%`}
      </div>

      <p className="progress-step-text">
        {stepMessage || "Uniendo con la intro oficial de Marino Alvarado..."}
      </p>

      <p style={{ fontSize: "16px", color: "var(--text-muted)" }}>
        Por favor no cierres esta ventana. El proceso toma solo unos segundos.
      </p>
    </section>
  );
};
