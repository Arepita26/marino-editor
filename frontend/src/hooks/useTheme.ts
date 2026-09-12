import { useEffect, useState } from "react";
import { AppTheme } from "../types";

const THEME_STORAGE_KEY = "marino_editor_theme";

export function useTheme() {
  const [theme, setTheme] = useState<AppTheme>(() => {
    // 1. Check local storage
    const saved = localStorage.getItem(THEME_STORAGE_KEY) as AppTheme | null;
    if (saved === "light" || saved === "dark") {
      return saved;
    }
    // 2. Check system preference
    if (typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "dark"; // Default to dark OLED for high contrast
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return { theme, toggleTheme, isDark: theme === "dark" };
}
