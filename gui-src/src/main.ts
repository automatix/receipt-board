// Receipt Board GUI bootstrap (issue #8).
//
// The page is served same-origin by the local server at /app, so requests use relative
// paths. pywebview injects the session token (ADR-0009) into window.__RECEIPT_BOARD__
// after load; privileged requests attach it as X-Session-Token. This minimal version
// proves the window -> server path by calling the public GET /checklists. The full
// feature set (tree, inline edit, drag & drop, vocabulary, search) arrives in issue #9.

interface RbConfig {
  token: string;
}

declare global {
  interface Window {
    __RECEIPT_BOARD__?: RbConfig;
  }
}

interface ChecklistSummary {
  id: number;
  name: string;
}

async function whenConfigReady(timeoutMs = 3000): Promise<RbConfig> {
  const start = Date.now();
  while (!window.__RECEIPT_BOARD__) {
    if (Date.now() - start > timeoutMs) {
      return { token: "" };
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  return window.__RECEIPT_BOARD__;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = window.__RECEIPT_BOARD__?.token;
  if (token) {
    headers.set("X-Session-Token", token);
  }
  const response = await fetch(path, { ...init, headers });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

async function main(): Promise<void> {
  await whenConfigReady();
  const status = document.getElementById("status");
  const app = document.getElementById("app");
  if (!status || !app) {
    return;
  }
  try {
    const checklists = await api<ChecklistSummary[]>("/checklists");
    status.textContent = `Verbunden — ${checklists.length} Checklist(s)`;
    app.innerHTML =
      checklists.map((c) => `<div>${c.id}: ${c.name}</div>`).join("") ||
      "<p>Keine Checklists.</p>";
  } catch (error) {
    status.textContent = `Fehler: ${(error as Error).message}`;
  }
}

void main();
