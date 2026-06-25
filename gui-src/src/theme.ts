// Theme handling: System (follow the OS) / Dark / Light, persisted in localStorage.

export type ThemeMode = "system" | "dark" | "light";

const KEY = "receiptboard.theme";
const ORDER: ThemeMode[] = ["system", "dark", "light"];

export function loadTheme(): ThemeMode {
  const value = localStorage.getItem(KEY);
  return value === "dark" || value === "light" || value === "system" ? value : "system";
}

export function saveTheme(mode: ThemeMode): void {
  localStorage.setItem(KEY, mode);
}

export function applyTheme(mode: ThemeMode): void {
  const root = document.documentElement;
  if (mode === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", mode);
  }
}

export function nextTheme(mode: ThemeMode): ThemeMode {
  return ORDER[(ORDER.indexOf(mode) + 1) % ORDER.length]!;
}

export function themeLabel(mode: ThemeMode): string {
  if (mode === "dark") {
    return "🌙 Dark";
  }
  if (mode === "light") {
    return "☀ Light";
  }
  return "🌗 System";
}
