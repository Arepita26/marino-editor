// Service Worker: Marino Editor 90 Segundos DDHH
// Estrategia de actualización forzada inmediata (Zero Stale Cache)
const CACHE_NAME = "marino-editor-v1.0.0";

self.addEventListener("install", (event) => {
  // Fuerza al Service Worker a activarse de inmediato sin esperar a que el usuario cierre pestañas
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log("[SW] Eliminando caché antigua:", key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // version.json y llamadas a la API NUNCA deben pasar por caché del SW
  if (url.pathname.includes("version.json") || url.pathname.startsWith("/api")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Network-first con fallback a caché para garantizar frescura en teléfonos
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});
