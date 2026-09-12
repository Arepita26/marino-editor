import { useEffect, useState } from "react";
import { AppVersionInfo } from "../types";

export const CURRENT_APP_VERSION = "1.0.0";
const CHECK_INTERVAL_MS = 45 * 1000; // 45 seconds

export function useForceUpdate() {
  const [hasUpdate, setHasUpdate] = useState(false);
  const [remoteVersion, setRemoteVersion] = useState<AppVersionInfo | null>(null);

  const checkForUpdate = async () => {
    try {
      // Cache-busting query parameter
      const res = await fetch(`/version.json?t=${Date.now()}`, {
        cache: "no-store",
        headers: { "Cache-Control": "no-cache" },
      });
      if (res.ok) {
        const data: AppVersionInfo = await res.json();
        if (data.version && data.version !== CURRENT_APP_VERSION) {
          setHasUpdate(true);
          setRemoteVersion(data);
          if (data.forceReload) {
            console.log("[ForceUpdate] Nueva versión obligatoria detectada:", data.version);
          }
        }
      }
    } catch (e) {
      // Silent error in offline or development mode
    }
  };

  useEffect(() => {
    checkForUpdate();
    const interval = setInterval(checkForUpdate, CHECK_INTERVAL_MS);

    // Also check immediately when user switches back to the app on mobile
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        checkForUpdate();
      }
    };

    window.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("focus", checkForUpdate);

    return () => {
      clearInterval(interval);
      window.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("focus", checkForUpdate);
    };
  }, []);

  const forceAppReload = async () => {
    try {
      // Unregister service workers and clear cache storage
      if ("serviceWorker" in navigator) {
        const registrations = await navigator.serviceWorker.getRegistrations();
        for (const reg of registrations) {
          await reg.update();
        }
      }
      if ("caches" in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map((name) => caches.delete(name)));
      }
    } catch (err) {
      console.warn("Error limpiando caché:", err);
    }
    // Hard reload
    window.location.reload();
  };

  return { hasUpdate, remoteVersion, forceAppReload };
}
