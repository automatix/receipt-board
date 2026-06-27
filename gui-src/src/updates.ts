// In-app updater UI (issue #83): a manual "check for updates" action plus a silent check
// on startup that shows a non-blocking banner when a newer public release exists. Installing
// is always explicit — never automatic.

import { ApiError, api } from "./api";
import type { UpdateInfo } from "./types";
import { byId, el, toast } from "./ui";

const BANNER_ID = "update-banner";

function bannerHost(): HTMLElement {
  return byId(BANNER_ID);
}

export function dismissBanner(): void {
  bannerHost().replaceChildren();
}

function showBanner(info: UpdateInfo): void {
  const text = el("span", {
    class: "update-banner-text",
    text: `Neue Version ${info.latest} verfügbar (installiert: ${info.current}).`,
  });

  const actions = el("div", { class: "update-banner-actions" });
  if (info.notes_url) {
    actions.append(
      el("a", {
        class: "update-banner-link",
        href: info.notes_url,
        target: "_blank",
        rel: "noopener noreferrer",
        text: "Was ist neu?",
      }),
    );
  }
  const install = el("button", {
    class: "btn btn-primary",
    text: "Jetzt installieren",
  }) as HTMLButtonElement;
  install.addEventListener("click", () => void startInstall(install));
  const dismiss = el("button", { class: "btn", text: "Später" });
  dismiss.addEventListener("click", () => dismissBanner());
  actions.append(install, dismiss);

  bannerHost().replaceChildren(el("div", { class: "update-banner" }, [text, actions]));
}

async function startInstall(button: HTMLButtonElement): Promise<void> {
  button.setAttribute("disabled", "disabled");
  button.textContent = "Wird geladen…";
  try {
    await api.installUpdate();
    // The backend launches the (UAC-gated) installer and then closes this window.
    bannerHost().replaceChildren(
      el("div", { class: "update-banner" }, [
        el("span", {
          class: "update-banner-text",
          text: "Installer wird gestartet – die App wird geschlossen…",
        }),
      ]),
    );
  } catch (error) {
    button.removeAttribute("disabled");
    button.textContent = "Jetzt installieren";
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}

// Manual check (toolbar): always gives feedback, success or failure.
export async function checkForUpdatesManually(): Promise<void> {
  try {
    const info = await api.checkUpdate();
    if (info.update_available) {
      showBanner(info);
    } else {
      toast(`Aktuell – Version ${info.current} ist die neueste.`);
    }
  } catch (error) {
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}

// Silent check on startup: only surfaces a banner if a newer version exists.
export async function checkForUpdatesOnStartup(): Promise<void> {
  try {
    const info = await api.checkUpdate();
    if (info.update_available) {
      showBanner(info);
    }
  } catch {
    // Stay quiet on startup failures (offline, rate-limited, etc.).
  }
}
