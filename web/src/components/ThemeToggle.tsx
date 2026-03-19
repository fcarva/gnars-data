import { useEffect, useState } from "react";

type ThemeMode = "light" | "dark";

function preferredTheme(): ThemeMode {
  if (typeof window === "undefined") {
    return "dark";
  }
  const stored = window.localStorage.getItem("gnars-theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>("dark");

  useEffect(() => {
    const next = preferredTheme();
    setTheme(next);
    document.documentElement.dataset.theme = next;
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("gnars-theme", theme);
  }, [theme]);

  return (
    <button
      className="theme-toggle"
      type="button"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
      aria-label="Toggle color theme"
    >
      {theme === "light" ? "dark" : "light"}
    </button>
  );
}
