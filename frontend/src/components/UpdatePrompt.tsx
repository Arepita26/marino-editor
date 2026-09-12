import React from "react";
import { useForceUpdate } from "../hooks/useForceUpdate";

export const UpdatePrompt: React.FC = () => {
  const { hasUpdate, remoteVersion, forceAppReload } = useForceUpdate();

  if (!hasUpdate) return null;

  return (
    <div className="update-banner" role="alert">
      <div className="update-banner-text">
        <strong>⚡ Nueva versión disponible ({remoteVersion?.version || "Reciente"})</strong>
        <div>Actualiza para aplicar las últimas mejoras.</div>
      </div>
      <button
        className="update-reload-btn"
        onClick={forceAppReload}
        type="button"
      >
        Actualizar ahora
      </button>
    </div>
  );
};
