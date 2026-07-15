// In-page text search (issue #127): the GUI runs in a pywebview (WebView2) window that
// ships no browser find bar, so Ctrl+F / F3 would otherwise do nothing. This module
// provides the usual find-on-page over the currently displayed content (#app): Ctrl+F
// opens the bar, typing highlights all matches (case-insensitive), Enter/F3 cycle
// forward, Shift+Enter/Shift+F3 backward, Esc closes. Matches are painted via the CSS
// Custom Highlight API — no DOM rewriting, so live SSE re-renders stay safe; app.ts
// calls refreshFind() after each render() to re-apply the highlights.

import { t } from "./i18n";
import { el } from "./ui";

const HIGHLIGHT_ALL = "find";
const HIGHLIGHT_CURRENT = "find-current";

let bar: HTMLElement | null = null;
let input: HTMLInputElement | null = null;
let counter: HTMLElement | null = null;
let ranges: Range[] = [];
let current = -1;

// Text nodes inside hidden subtrees (e.g. the hidden file <input> label) are not
// "displayed content"; offsetParent is null for display:none elements.
function isDisplayed(element: Element | null): boolean {
  return element instanceof HTMLElement && element.offsetParent !== null;
}

function collectMatches(query: string): Range[] {
  const root = document.getElementById("app");
  const needle = query.toLowerCase();
  if (!root || !needle) {
    return [];
  }
  const out: Range[] = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) =>
      node.nodeValue && isDisplayed(node.parentElement)
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT,
  });
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const text = node.nodeValue!.toLowerCase();
    for (
      let index = text.indexOf(needle);
      index !== -1;
      index = text.indexOf(needle, index + needle.length)
    ) {
      const range = new Range();
      range.setStart(node, index);
      range.setEnd(node, index + needle.length);
      out.push(range);
    }
  }
  return out;
}

function paint(): void {
  CSS.highlights.delete(HIGHLIGHT_ALL);
  CSS.highlights.delete(HIGHLIGHT_CURRENT);
  if (ranges.length > 0) {
    CSS.highlights.set(HIGHLIGHT_ALL, new Highlight(...ranges));
    if (current >= 0) {
      CSS.highlights.set(HIGHLIGHT_CURRENT, new Highlight(ranges[current]!));
    }
  }
  if (counter) {
    counter.textContent = `${ranges.length ? current + 1 : 0}/${ranges.length}`;
    counter.classList.toggle("find-none", input !== null && input.value !== "" && ranges.length === 0);
  }
}

function scrollToCurrent(): void {
  const range = ranges[current];
  if (!range) {
    return;
  }
  const target = range.startContainer.parentElement;
  target?.scrollIntoView({ block: "center", behavior: "instant" as ScrollBehavior });
}

function search(): void {
  ranges = collectMatches(input?.value ?? "");
  current = ranges.length > 0 ? 0 : -1;
  paint();
  scrollToCurrent();
}

function step(delta: number): void {
  if (ranges.length === 0) {
    return;
  }
  current = (current + delta + ranges.length) % ranges.length;
  paint();
  scrollToCurrent();
}

function closeBar(): void {
  if (!bar) {
    return;
  }
  bar.remove();
  bar = null;
  input = null;
  counter = null;
  ranges = [];
  current = -1;
  CSS.highlights.delete(HIGHLIGHT_ALL);
  CSS.highlights.delete(HIGHLIGHT_CURRENT);
}

function openBar(): void {
  if (bar) {
    input?.focus();
    input?.select();
    return;
  }
  input = el("input", { class: "input find-input", placeholder: t("find.placeholder") }) as HTMLInputElement;
  input.addEventListener("input", search);
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      step(event.shiftKey ? -1 : 1);
    } else if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation(); // an open dialog's Esc handler must not also fire
      closeBar();
    }
  });
  counter = el("span", { class: "find-counter", text: "0/0" });
  const prev = el("button", { class: "btn btn-mini", onclick: () => step(-1), text: "▲" });
  const next = el("button", { class: "btn btn-mini", onclick: () => step(1), text: "▼" });
  const close = el("button", { class: "btn btn-mini", onclick: closeBar, text: "✕" });
  prev.setAttribute("aria-label", t("find.prev"));
  prev.setAttribute("title", t("find.prev"));
  next.setAttribute("aria-label", t("find.next"));
  next.setAttribute("title", t("find.next"));
  close.setAttribute("aria-label", t("find.close"));
  close.setAttribute("title", t("find.close"));
  bar = el("div", { class: "find-bar" }, [input, counter, prev, next, close]);
  document.body.append(bar);
  input.focus();
}

// Re-apply the highlights after a re-render (render() replaces #app's children, which
// detaches every highlighted range). Keeps the current position when possible.
export function refreshFind(): void {
  if (!bar || !input) {
    return;
  }
  const keep = current;
  ranges = collectMatches(input.value);
  current = ranges.length > 0 ? Math.min(Math.max(keep, 0), ranges.length - 1) : -1;
  paint();
}

// Global keyboard wiring; call once at startup.
export function setupFind(): void {
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === "f") {
      event.preventDefault();
      openBar();
    } else if (event.key === "F3") {
      event.preventDefault();
      if (bar) {
        step(event.shiftKey ? -1 : 1);
      } else {
        openBar();
      }
    } else if (event.key === "Escape" && bar && !document.querySelector(".overlay")) {
      // Browser-like: Esc closes the find bar from anywhere — but never while a dialog
      // is open (its own Esc handling wins).
      closeBar();
    }
  });
}
