import React from "react";
import { useTheme } from "../hooks/useTheme";

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme, isDark } = useTheme();

  return (
    <button
      className="theme-toggle-btn"
      onClick={toggleTheme}
      type="button"
      aria-label={`Cambiar a modo ${isDark ? "claro" : "oscuro"}`}
      title={`Cambiar a modo ${isDark ? "claro" : "oscuro"}`}
    >
      <span>{isDark ? "☀️" : "🌙"}</span>
      <span>{isDark ? "Modo Claro" : "Modo Oscuro"}</span>
    </button>
  );
};
