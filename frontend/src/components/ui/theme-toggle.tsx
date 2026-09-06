"use client";

import * as React from "react";
import { Sun, Moon } from "lucide-react";

interface ThemeToggleProps {
  onChange?: (mode: "light" | "dark") => void;
}

export function ThemeToggle({ onChange }: ThemeToggleProps = {}) {
  // Read from localStorage on client mount for consistent hydration
  // If not set, default to "light" (matches server default)
  const [mode, setMode] = React.useState<"light" | "dark">("light");

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("theme");
      const finalMode = stored === "dark" ? "dark" : "light";
      setMode(finalMode);
      document.documentElement.classList.toggle("dark", finalMode === "dark");
      localStorage.setItem("theme", finalMode);
      onChange?.(finalMode);
    }
  }, []);

  return (
    <button
      aria-label={`Toggle ${mode === "dark" ? "dark" : "light"} mode`}
      className="p-2 rounded-lg transition-colors hover:bg-accent/30"
      onClick={() => setMode(mode === "dark" ? "light" : "dark")}
    >
      {mode === "dark" ? (
        <Sun className="w-5 h-5 text-yellow-400" />
      ) : (
        <Moon className="w-5 h-5 text-yellow-300" />
      )}
    </button>
  );
}