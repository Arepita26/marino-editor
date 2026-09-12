import React from "react";

export const SecurityNotice: React.FC = () => {
  return (
    <footer className="security-notice">
      <div className="security-badge">
        <span>🔒</span>
        <span>Conexión Segura HTTPS • Privacidad Total</span>
      </div>
      <p>
        Tus videos son procesados de forma temporal y se eliminan automáticamente del servidor una vez descargados. Cero almacenamiento permanente.
      </p>
    </footer>
  );
};
