// Entry point: wait for the injected session token, then start the app (issue #9).

import { start } from "./app";
import { initLocale } from "./i18n";
import { applyTheme, loadTheme } from "./theme";

async function whenConfigReady(timeoutMs = 3000): Promise<void> {
  const begin = Date.now();
  while (!window.__RECEIPT_BOARD__) {
    if (Date.now() - begin > timeoutMs) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
}

// Ignore files dropped anywhere on the window (issue #105): WebView2 would otherwise navigate
// to / preview the dropped file. Scoped to file drags ("Files"), so the internal tree
// drag-and-drop (which carries "text/plain") is untouched. The import dialog attaches its own
// handler on its element — that runs first and reads the file before this no-op fires.
function ignoreWindowFileDrops(): void {
  for (const type of ["dragover", "drop"] as const) {
    window.addEventListener(type, (event: DragEvent) => {
      if (event.dataTransfer && Array.from(event.dataTransfer.types).includes("Files")) {
        event.preventDefault();
      }
    });
  }
}

async function main(): Promise<void> {
  ignoreWindowFileDrops();
  initLocale();
  applyTheme(loadTheme());
  await whenConfigReady();
  await start();
}

void main();
