// Entry point: wait for the injected session token, then start the app (issue #9).

import { start } from "./app";
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

async function main(): Promise<void> {
  applyTheme(loadTheme());
  await whenConfigReady();
  await start();
}

void main();
