// Small DOM helpers and modal dialogs (no framework).

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
        el("button", { class: "btn", onclick: () => finish(false), text: "Abbrechen" }),
        el("button", {
          class: danger ? "btn btn-danger" : "btn btn-primary",
          onclick: () => finish(true),
          text: "OK",
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
        el("button", { class: "btn", onclick: () => finish(null), text: "Abbrechen" }),
        el("button", {
          class: "btn btn-primary",
          onclick: () => finish(input.value.trim()),
          text: "OK",
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

export function importDialog(): Promise<ImportInput | null> {
  return new Promise((resolve) => {
    let dismiss = (): void => {};
    const name = el("input", { class: "input", placeholder: "Checklist-Name" });
    const text = el("textarea", { class: "textarea", placeholder: "Markdown einfügen…" });
    const finish = (value: ImportInput | null): void => {
      dismiss();
      resolve(value);
    };
    const box = el("div", { class: "modal modal-wide" }, [
      el("h3", { text: "Checklist importieren" }),
      name,
      text,
      el("div", { class: "modal-actions" }, [
        el("button", { class: "btn", onclick: () => finish(null), text: "Abbrechen" }),
        el("button", {
          class: "btn btn-primary",
          onclick: () => finish({ name: name.value.trim(), text: text.value }),
          text: "Importieren",
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
