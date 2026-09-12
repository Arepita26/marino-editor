import React from "react";
import { ThemeToggle } from "./ThemeToggle";

export const Header: React.FC = () => {
  return (
    <header className="app-header">
      <div className="brand-badge">
        <div className="brand-icon" aria-hidden="true">
          90s
        </div>
        <div className="brand-text">
          <h1>90 Segundos DDHH</h1>
          <p className="brand-subtitle">La TV Calle • Marino Alvarado</p>
        </div>
      </div>
      <ThemeToggle />
    </header>
  );
};
