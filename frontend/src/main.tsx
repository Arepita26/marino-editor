import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

// Registro de Service Worker para actualizaciones forzadas inmediatas
if ("serviceWorker" in navigator && (import.meta as any).env?.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => {
        console.log("[SW] Service Worker registrado exitosamente:", reg.scope);
      })
      .catch((err) => {
        console.warn("[SW] Error al registrar Service Worker:", err);
      });
  });
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
