// Small DOM helpers and modal dialogs (no framework).

import { t } from "./i18n";
import type { ImportReport } from "./types";

type ElAttrs = Record<string, string | number | EventListener>;

export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: ElAttrs = {},
  children: Array<Node | string> = [],
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") {
      node.className = String(value);
    } else if (key === "text") {
      node.textContent = String(value);
    } else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value as EventListener);
    } else {
      node.setAttribute(key, String(value));
    }
  }
  for (const child of children) {
    node.append(child);
  }
  return node;
}

export function byId(id: string): HTMLElement {
  const node = document.getElementById(id);
  if (!node) {
    throw new Error(`Missing element #${id}`);
  }
  return node;
}

export function clear(node: HTMLElement): void {
  node.replaceChildren();
}

function mountModal(box: HTMLElement, onCancel: () => void): () => void {
  const overlay = el("div", { class: "overlay" });
  overlay.append(box);
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
      onCancel();
    }
  });
  const onKey = (event: KeyboardEvent): void => {
    if (event.key === "Escape") {
      onCancel();
    }
  };
  document.addEventListener("keydown", onKey);
  document.body.append(overlay);
  return () => {
    document.removeEventListener("keydown", onKey);
    overlay.remove();
  };
}

export function confirmDialog(message: string, danger = true): Promise<boolean> {
  return new Promise((resolve) => {
    let dismiss = (): void => {};
    const finish = (value: boolean): void => {
      dismiss();
      resolve(value);
    };
    const box = el("div", { class: "modal" }, [
      el("p", { class: "modal-message", text: message }),
      el("div", { class: "modal-actions" }, [
        el("button", { class: "btn", onclick: () => finish(false), text: t("common.cancel") }),
        el("button", {
          class: danger ? "btn btn-danger" : "btn btn-primary",
          onclick: () => finish(true),
          text: t("common.ok"),
        }),
      ]),
    ]);
    dismiss = mountModal(box, () => finish(false));
  });
}

export function textPrompt(title: string, initial = ""): Promise<string | null> {
  return new Promise((resolve) => {
    let dismiss = (): void => {};
    const input = el("input", { class: "input", value: initial });
    const finish = (value: string | null): void => {
      dismiss();
      resolve(value);
    };
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        finish(input.value.trim());
      }
    });
    const box = el("div", { class: "modal" }, [
      el("h3", { text: title }),
      input,
      el("div", { class: "modal-actions" }, [
        el("button", { class: "btn", onclick: () => finish(null), text: t("common.cancel") }),
        el("button", {
          class: "btn btn-primary",
          onclick: () => finish(input.value.trim()),
          text: t("common.ok"),
        }),
      ]),
    ]);
    dismiss = mountModal(box, () => finish(null));
    setTimeout(() => input.focus(), 0);
  });
}

export interface ImportInput {
  name: string;
  text: string;
}

function renderReport(container: HTMLElement, report: ImportReport): void {
  const children: HTMLElement[] = [];
  if (report.valid) {
    children.push(
      el("p", {
        class: "import-ok",
        text: t("import.ok", {
          categories: report.summary.categories,
          items: report.summary.items,
        }),
      }),
    );
  } else {
    children.push(
      el("p", { class: "import-bad", text: t("import.bad", { count: report.errors.length }) }),
    );
    for (const issue of report.errors) {
      children.push(
        el("div", {
          class: "import-issue",
          text: t("import.issue", {
            line: issue.line,
            token: issue.token,
            message: issue.message,
          }),
        }),
      );
    }
  }
  for (const warning of report.warnings) {
    children.push(
      el("div", {
        class: "import-issue warn",
        text: t("import.warning", { line: warning.line, message: warning.message }),
      }),
    );
  }
  container.replaceChildren(...children);
}

export function importDialog(
  validate: (text: string) => Promise<ImportReport>,
): Promise<ImportInput | null> {
  return new Promise((resolve) => {
    let dismiss = (): void => {};
    const name = el("input", { class: "input", placeholder: t("import.namePlaceholder") });
    const text = el("textarea", { class: "textarea", placeholder: t("import.textPlaceholder") });
    const report = el("div", { class: "import-report" });
    const finish = (value: ImportInput | null): void => {
      dismiss();
      resolve(value);
    };
    const onCheck = async (): Promise<void> => {
      report.replaceChildren(el("p", { class: "empty", text: t("import.checking") }));
      try {
        renderReport(report, await validate(text.value));
      } catch (error) {
        report.replaceChildren(
          el("p", {
            class: "import-bad",
            text: t("import.error", { message: (error as Error).message }),
          }),
        );
      }
    };
    const box = el("div", { class: "modal modal-wide" }, [
      el("h3", { text: t("import.title") }),
      name,
      text,
      report,
      el("div", { class: "modal-actions" }, [
        el("button", { class: "btn", onclick: () => finish(null), text: t("common.cancel") }),
        el("button", { class: "btn", onclick: () => void onCheck(), text: t("import.check") }),
        el("button", {
          class: "btn btn-primary",
          onclick: () => finish({ name: name.value.trim(), text: text.value }),
          text: t("import.run"),
        }),
      ]),
    ]);
    dismiss = mountModal(box, () => finish(null));
  });
}

export function toast(message: string, isError = false): void {
  const node = el("div", { class: isError ? "toast toast-error" : "toast", text: message });
  document.body.append(node);
  setTimeout(() => node.remove(), 4000);
}
