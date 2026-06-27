// Receipt Board GUI application (TECH_SPEC §7).
//
// A framework-free SPA over the REST API: checklist tree with collapse, done checkboxes
// with cascade (category uncheck confirmed with the affected count), inline rename, an
// item editor (data/instructions/resources/tools), native HTML5 drag & drop for
// reorder/re-parent, vocabulary management, search, and checklist create/import/clone/
// delete/export. All views refresh live via Server-Sent Events (issue #73), so external
// changes (CLI/REST/automation) appear with no manual refresh.

import { ApiError, api } from "./api";
import type {
  AuditEntry,
  ChecklistSummary,
  ChecklistTree,
  ItemFields,
  NodeKind,
  ResourceRef,
  TreeNode,
  VocabEntry,
} from "./types";
import { type ThemeMode, applyTheme, loadTheme, nextTheme, saveTheme } from "./theme";
import { type IconName, icon } from "./icons";
import { localeLabel, nextLocale, setLocale, t } from "./i18n";
import {
  byId,
  clear,
  confirmDialog,
  el,
  importDialog,
  textPrompt,
  toast,
} from "./ui";
import { checkForUpdatesManually, checkForUpdatesOnStartup } from "./updates";

interface State {
  checklists: ChecklistSummary[];
  activeId: number | null;
  tree: ChecklistTree | null;
  view: "checklist" | "vocab" | "audit";
  resourceTypes: VocabEntry[];
  tools: VocabEntry[];
  audit: AuditEntry[];
  collapsed: Set<number>;
}

const state: State = {
  checklists: [],
  activeId: null,
  tree: null,
  view: "checklist",
  resourceTypes: [],
  tools: [],
  audit: [],
  collapsed: new Set(),
};

let dragged: { kind: NodeKind; id: number } | null = null;
let themeMode: ThemeMode = loadTheme();
const parentOf = new Map<string, number | null>();

const key = (kind: NodeKind, id: number): string => `${kind}:${id}`;

const LIVE_DEBOUNCE_MS = 80;

// Live-update controller (issue #73): SSE connection state, the last seen server revision,
// and guards that keep a background refresh from clobbering an inline edit or search results.
const live = {
  source: null as EventSource | null,
  connected: false,
  revision: null as number | null,
  editing: false,
  searching: false,
  pending: false,
  timer: null as number | null,
};

// -- navigation history (issue #107) ------------------------------------------
// Browser-like back/forward over meaningful navigations: the active view, the active
// checklist and an open search. Driven by toolbar buttons, Alt+Left/Right and the mouse
// side buttons. An in-app stack (not the History API) so it can never navigate the webview
// away from the app page.
type View = State["view"];
interface NavEntry {
  view: View;
  activeId: number | null;
  search: string | null;
}
const navStack: NavEntry[] = [];
let navIndex = -1;
let navigating = false; // suppress pushes while applying a history entry
let currentSearch: string | null = null; // the query when the search overlay is open, else null
let navInputsBound = false;

function canBack(): boolean {
  return navIndex > 0;
}

function canForward(): boolean {
  return navIndex < navStack.length - 1;
}

function pushHistory(): void {
  if (navigating) {
    return;
  }
  const entry: NavEntry = { view: state.view, activeId: state.activeId, search: currentSearch };
  const top = navStack[navIndex];
  if (top && top.view === entry.view && top.activeId === entry.activeId && top.search === entry.search) {
    return; // collapse no-op navigations
  }
  navStack.splice(navIndex + 1); // drop the forward branch
  navStack.push(entry);
  navIndex = navStack.length - 1;
}

async function applyNav(entry: NavEntry): Promise<void> {
  state.view = entry.view;
  state.activeId = entry.activeId;
  await loadForView();
  if (entry.search) {
    await runSearch(entry.search, false);
  } else {
    currentSearch = null;
    render();
  }
}

async function navGo(delta: number): Promise<void> {
  const target = navIndex + delta;
  if (target < 0 || target >= navStack.length) {
    return;
  }
  navIndex = target;
  navigating = true;
  try {
    await applyNav(navStack[navIndex]!);
  } finally {
    navigating = false;
  }
}

// Switch the top-level view (checklist/vocab/audit) and record it in history.
function switchView(view: View): void {
  state.view = view;
  pushHistory();
  if (view === "audit") {
    void loadAudit().then(render);
  } else {
    render();
  }
}

// Refresh just the Back/Forward enabled state in place (the search overlay doesn't re-render
// the toolbar, so it can't clobber the user's search box).
function updateNavButtons(): void {
  const back = document.getElementById("nav-back") as HTMLButtonElement | null;
  const forward = document.getElementById("nav-forward") as HTMLButtonElement | null;
  if (back) {
    back.disabled = !canBack();
  }
  if (forward) {
    forward.disabled = !canForward();
  }
}

function setupNavInputs(): void {
  if (navInputsBound) {
    return;
  }
  navInputsBound = true;
  document.addEventListener("keydown", (event) => {
    if (!event.altKey) {
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      void navGo(-1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      void navGo(1);
    }
  });
  // Mouse side buttons: X1 (button 3) = back, X2 (button 4) = forward. Navigate on mouseup;
  // also swallow auxclick so the webview never tries its own (page) back/forward.
  window.addEventListener("mouseup", (event) => {
    if (event.button === 3) {
      event.preventDefault();
      void navGo(-1);
    } else if (event.button === 4) {
      event.preventDefault();
      void navGo(1);
    }
  });
  window.addEventListener("auxclick", (event) => {
    if (event.button === 3 || event.button === 4) {
      event.preventDefault();
    }
  });
}

// -- data loading -------------------------------------------------------------

async function loadVocab(): Promise<void> {
  state.resourceTypes = await api.listVocab("resource_type");
  state.tools = await api.listVocab("tool");
}

async function loadChecklists(): Promise<void> {
  state.checklists = await api.listChecklists();
  if (state.activeId === null && state.checklists.length > 0) {
    state.activeId = state.checklists[0]!.id;
  }
  if (state.activeId !== null && !state.checklists.some((c) => c.id === state.activeId)) {
    state.activeId = state.checklists[0]?.id ?? null;
  }
}

async function loadActiveTree(): Promise<void> {
  state.tree = state.activeId === null ? null : await api.exportChecklist(state.activeId);
}

async function loadAudit(): Promise<void> {
  state.audit = await api.listAudit(state.activeId ?? undefined, 100);
}

// Load exactly the data the current view needs (no render).
async function loadForView(): Promise<void> {
  await loadChecklists();
  await loadActiveTree();
  if (state.view === "vocab") {
    await loadVocab();
  }
  if (state.view === "audit") {
    await loadAudit();
  }
}

// Initial load + any explicit (re)load: fetch the current view's data and render.
async function reload(): Promise<void> {
  await loadForView();
  render();
}

// Run a mutating action and surface API errors as toasts. The reload is driven by the
// live SSE change event (single reload path, no double render); only when the live
// connection is down do we reload directly as a fallback.
async function act(action: () => Promise<unknown>): Promise<void> {
  try {
    await action();
    if (!live.connected) {
      await reload();
    }
  } catch (error) {
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}

// -- live updates (SSE) -------------------------------------------------------

// Coalesce a burst of change events into a single refresh.
function scheduleLiveRefresh(): void {
  if (live.timer !== null) {
    return;
  }
  live.timer = window.setTimeout(() => {
    live.timer = null;
    void liveRefresh();
  }, LIVE_DEBOUNCE_MS);
}

// Refresh from a live change event. Defer while an inline edit is in progress, and keep
// search results in place (load fresh data but do not re-render over them).
async function liveRefresh(): Promise<void> {
  if (live.editing) {
    live.pending = true;
    return;
  }
  live.pending = false;
  try {
    await loadForView();
  } catch {
    return; // transient; the next change event will retry
  }
  if (!live.searching) {
    render();
  }
}

// Called when an inline edit ends; runs a deferred refresh if one arrived meanwhile.
function endEditing(): void {
  if (!live.editing) {
    return;
  }
  live.editing = false;
  if (live.pending) {
    scheduleLiveRefresh();
  }
}

// Subscribe to server-sent change markers so the GUI reflects every change (including
// external CLI/REST/automation edits) with no manual refresh. EventSource reconnects on
// its own; on (re)connect we catch up when the revision advanced during a gap.
function connectEvents(): void {
  let source: EventSource;
  try {
    source = new EventSource("/events");
  } catch {
    return; // no EventSource in this runtime: stay on the per-action fallback reload
  }
  live.source = source;
  source.addEventListener("ready", (event) => {
    live.connected = true;
    const revision = parseRevision((event as MessageEvent).data);
    if (live.revision !== null && revision !== live.revision) {
      scheduleLiveRefresh();
    }
    live.revision = revision;
  });
  source.addEventListener("change", (event) => {
    live.connected = true;
    live.revision = parseRevision((event as MessageEvent).data);
    scheduleLiveRefresh();
  });
  source.onopen = (): void => {
    live.connected = true;
  };
  source.onerror = (): void => {
    live.connected = false;
  };
}

function parseRevision(data: string): number | null {
  try {
    const value = JSON.parse(data) as { revision?: number };
    return typeof value.revision === "number" ? value.revision : null;
  } catch {
    return null;
  }
}

// -- helpers ------------------------------------------------------------------

function countDoneItems(node: TreeNode): number {
  let total = 0;
  for (const child of node.children ?? []) {
    if (child.kind === "expense_item") {
      total += child.done ? 1 : 0;
    } else {
      total += countDoneItems(child);
    }
  }
  return total;
}

function indexParentMap(tree: ChecklistTree): void {
  parentOf.clear();
  const walk = (node: TreeNode, parentId: number | null): void => {
    parentOf.set(key(node.kind, node.id), parentId);
    for (const child of node.children ?? []) {
      walk(child, node.id);
    }
  };
  for (const top of tree.children) {
    walk(top, null);
  }
}

// -- rendering ----------------------------------------------------------------

function render(): void {
  live.searching = false; // rendering a normal view leaves any search-results state
  currentSearch = null; // a normal view is not the search overlay
  renderToolbar();
  const main = byId("app");
  clear(main);
  if (state.view === "audit") {
    main.append(renderAudit());
  } else if (state.view === "vocab") {
    main.append(renderVocab());
  } else if (!state.tree) {
    main.append(el("p", { class: "empty", text: t("tree.empty") }));
  } else {
    indexParentMap(state.tree);
    main.append(renderTree(state.tree));
  }
}

function renderToolbar(): void {
  const bar = byId("toolbar");
  clear(bar);

  const back = iconButton("back", t("nav.back"), () => void navGo(-1), "btn-nav");
  const forward = iconButton("forward", t("nav.forward"), () => void navGo(1), "btn-nav");
  back.id = "nav-back";
  forward.id = "nav-forward";
  back.disabled = !canBack();
  forward.disabled = !canForward();

  const selector = el("select", { class: "input", onchange: onSelectChecklist }) as HTMLSelectElement;
  for (const checklist of state.checklists) {
    const option = el("option", { value: String(checklist.id), text: checklist.name });
    if (checklist.id === state.activeId) {
      option.setAttribute("selected", "selected");
    }
    selector.append(option);
  }
  if (state.checklists.length === 0) {
    selector.append(el("option", { text: t("common.none") }));
  }

  const search = el("input", {
    class: "input search",
    placeholder: t("toolbar.search"),
  }) as HTMLInputElement;
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      void runSearch(search.value.trim());
    }
  });

  bar.append(
    el("div", { class: "toolbar-group" }, [back, forward]),
    el("div", { class: "toolbar-group" }, [
      selector,
      button(t("toolbar.new"), () => void onCreateBlank(), "", "new"),
      button(t("toolbar.import"), () => void onImport(), "", "import"),
      button(t("toolbar.clone"), () => void onClone(), "", "clone"),
      button(t("toolbar.delete"), () => void onDeleteChecklist(), "btn-danger", "delete"),
      button(t("toolbar.export"), () => void onExport(), "", "export"),
    ]),
    el("div", { class: "toolbar-group" }, [
      search,
      button(
        t(state.view === "vocab" ? "toolbar.checklist" : "toolbar.vocab"),
        () => switchView(state.view === "vocab" ? "checklist" : "vocab"),
        "",
        state.view === "vocab" ? "checklist" : "vocab",
      ),
      button(
        t(state.view === "audit" ? "toolbar.checklist" : "toolbar.audit"),
        () => switchView(state.view === "audit" ? "checklist" : "audit"),
        "",
        state.view === "audit" ? "checklist" : "audit",
      ),
      button(t("toolbar.updates"), () => void checkForUpdatesManually(), "", "updates"),
      button(localeLabel(), () => {
        setLocale(nextLocale());
        render();
      }),
      button(t(`theme.${themeMode}`), () => {
        themeMode = nextTheme(themeMode);
        applyTheme(themeMode);
        saveTheme(themeMode);
        renderToolbar();
      }),
    ]),
  );
}

function button(
  label: string,
  onClick: () => void,
  extra = "",
  iconName?: IconName,
): HTMLButtonElement {
  const classes = `btn ${iconName ? "btn-icon" : ""} ${extra}`.replace(/\s+/g, " ").trim();
  const btn = el("button", { class: classes, onclick: onClick }) as HTMLButtonElement;
  if (iconName) {
    btn.append(icon(iconName));
  }
  if (label) {
    btn.append(document.createTextNode(label));
  }
  return btn;
}

// Icon-only button: no visible text, so an aria-label/title carries the meaning (a11y).
function iconButton(
  iconName: IconName,
  ariaLabel: string,
  onClick: () => void,
  extra = "",
): HTMLButtonElement {
  const btn = button("", onClick, extra, iconName);
  btn.setAttribute("aria-label", ariaLabel);
  btn.setAttribute("title", ariaLabel);
  return btn;
}

function renderTree(tree: ChecklistTree): HTMLElement {
  const root = el("div", { class: "tree" }, [el("h2", { text: tree.name })]);
  const list = el("div", { class: "node-list" });
  list.append(dropZone(null, 0)); // insert at top level, position 0
  for (const node of tree.children) {
    list.append(renderNode(node));
    list.append(dropZone(null, node.position + 1));
  }
  root.append(list);
  root.append(
    el("div", { class: "node-add" }, [
      button(t("tree.addCategory"), () => void onAddCategory(null), "", "add"),
    ]),
  );
  return root;
}

function renderNode(node: TreeNode): HTMLElement {
  const container = el("div", { class: "node" });
  const row = el("div", { class: `row row-${node.kind}` });
  row.setAttribute("draggable", "true");
  row.addEventListener("dragstart", (event) => {
    dragged = { kind: node.kind, id: node.id };
    event.dataTransfer?.setData("text/plain", key(node.kind, node.id));
  });

  const isCategory = node.kind === "category";
  const hasChildren = (node.children?.length ?? 0) > 0;

  if (isCategory) {
    const collapsed = state.collapsed.has(node.id);
    row.append(
      el("span", {
        class: "toggle",
        text: hasChildren ? (collapsed ? "▸" : "▾") : "·",
        onclick: () => {
          if (collapsed) {
            state.collapsed.delete(node.id);
          } else {
            state.collapsed.add(node.id);
          }
          render();
        },
      }),
    );
  } else {
    row.append(el("span", { class: "toggle", text: "·" }));
  }

  const checkbox = el("input", { class: "checkbox", type: "checkbox" }) as HTMLInputElement;
  checkbox.checked = node.done;
  checkbox.addEventListener("change", () => void onToggleDone(node, checkbox));
  row.append(checkbox);

  row.append(nameElement(node));

  if (node.kind === "expense_item") {
    row.append(itemSummary(node));
  }

  row.append(rowActions(node));

  // Drop INTO a category (append) lands on the row itself.
  if (isCategory) {
    row.addEventListener("dragover", (event) => {
      event.preventDefault();
      row.classList.add("drop-into");
    });
    row.addEventListener("dragleave", () => row.classList.remove("drop-into"));
    row.addEventListener("drop", (event) => {
      event.preventDefault();
      row.classList.remove("drop-into");
      void onDrop(node.id, null);
    });
  }

  container.append(row);

  if (isCategory && hasChildren && !state.collapsed.has(node.id)) {
    const childList = el("div", { class: "node-list" });
    childList.append(dropZone(node.id, 0));
    for (const child of node.children ?? []) {
      childList.append(renderNode(child));
      childList.append(dropZone(node.id, child.position + 1));
    }
    container.append(childList);
  }

  if (isCategory) {
    container.append(
      el("div", { class: "node-add" }, [
        button(t("tree.addCategory"), () => void onAddCategory(node.id), "", "add"),
        button(t("tree.addItem"), () => void onAddItem(node.id), "", "add"),
      ]),
    );
  }

  return container;
}

function nameElement(node: TreeNode): HTMLElement {
  const span = el("span", { class: "name", text: node.name });
  span.addEventListener("dblclick", () => startInlineRename(node, span));
  return span;
}

function startInlineRename(node: TreeNode, span: HTMLElement): void {
  const input = el("input", { class: "input inline", value: node.name }) as HTMLInputElement;
  live.editing = true; // pause live refresh so an incoming change can't drop this input
  let done = false;
  const commit = (): void => {
    if (done) {
      return; // guard against Enter + the blur it triggers running twice
    }
    done = true;
    endEditing();
    const value = input.value.trim();
    if (value && value !== node.name) {
      void act(() =>
        node.kind === "category"
          ? api.editCategory(node.id, value)
          : api.editItem(node.id, { name: value }),
      );
    } else {
      render();
    }
  };
  const cancel = (): void => {
    if (done) {
      return;
    }
    done = true;
    endEditing();
    render();
  };
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      commit();
    } else if (event.key === "Escape") {
      cancel();
    }
  });
  input.addEventListener("blur", commit);
  span.replaceWith(input);
  input.focus();
  input.select();
}

function itemSummary(node: TreeNode): HTMLElement {
  const parts: string[] = [];
  if (node.resources?.length) {
    parts.push(node.resources.map((r) => (r.value ? `${r.type}:${r.value}` : r.type)).join(", "));
  }
  if (node.tools?.length) {
    parts.push(`{${node.tools.join(", ")}}`);
  }
  if (node.data) {
    parts.push(`[${node.data}]`);
  }
  return el("span", { class: "summary", text: parts.join("  ") });
}

function rowActions(node: TreeNode): HTMLElement {
  const actions = el("div", { class: "actions" });
  if (node.kind === "expense_item") {
    actions.append(iconButton("edit", t("common.edit"), () => void onEditItem(node), "btn-mini"));
  }
  actions.append(
    iconButton("trash", t("common.remove"), () => void onRemove(node), "btn-mini btn-danger"),
  );
  return actions;
}

function dropZone(parentId: number | null, position: number): HTMLElement {
  const zone = el("div", { class: "drop-zone" });
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("active");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("active"));
  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("active");
    void onDrop(parentId, position);
  });
  return zone;
}

// -- vocabulary view ----------------------------------------------------------

function renderVocab(): HTMLElement {
  const wrap = el("div", { class: "vocab" }, [el("h2", { text: t("vocab.title") })]);
  wrap.append(renderResourceTypeSection(state.resourceTypes));
  wrap.append(renderVocabSection(t("vocab.tools"), "tool", state.tools));
  return wrap;
}

// Tools (and any name-only vocabulary): rename on Enter, remove, add.
function renderVocabSection(title: string, kind: "tool", entries: VocabEntry[]): HTMLElement {
  const section = el("div", { class: "vocab-section" }, [el("h3", { text: title })]);
  for (const entry of entries) {
    const nameInput = el("input", { class: "input inline", value: entry.name }) as HTMLInputElement;
    const renameCommit = (): void => {
      const value = nameInput.value.trim();
      if (value && value !== entry.name) {
        void act(async () => {
          await api.updateVocab(kind, entry.id, { name: value });
          await loadVocab();
        });
      }
    };
    nameInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        renameCommit();
      }
    });
    section.append(
      el("div", { class: "vocab-row" }, [
        nameInput,
        button(t("common.remove"), () => void onRemoveVocab(kind, entry), "btn-mini btn-danger"),
      ]),
    );
  }
  const adder = el("input", {
    class: "input",
    placeholder: t("vocab.newTool"),
  }) as HTMLInputElement;
  const add = (): void => {
    const value = adder.value.trim();
    if (value) {
      void act(async () => {
        await api.addVocab(kind, { name: value });
        await loadVocab();
      });
    }
  };
  adder.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      add();
    }
  });
  section.append(el("div", { class: "vocab-row" }, [adder, button(t("common.add"), add)]));
  return section;
}

// Resource types carry a key, value-optionality and a value regex; full CRUD + duplicate.
function renderResourceTypeSection(entries: VocabEntry[]): HTMLElement {
  const kind = "resource_type" as const;
  const optionalLabel = (box: HTMLInputElement): HTMLElement =>
    el("label", { class: "tool-check" }, [box, document.createTextNode(` ${t("vocab.valueOptional")}`)]);
  const section = el("div", { class: "vocab-section" }, [
    el("h3", { text: t("vocab.resourceTypes") }),
  ]);

  for (const entry of entries) {
    const nameInput = el("input", { class: "input inline", value: entry.name }) as HTMLInputElement;
    const optBox = el("input", { class: "checkbox", type: "checkbox" }) as HTMLInputElement;
    optBox.checked = entry.value_optional ?? false;
    const patternInput = el("input", {
      class: "input",
      placeholder: t("vocab.regexPlaceholder"),
      value: entry.value_pattern ?? "",
    }) as HTMLInputElement;
    const save = (): void => {
      void act(async () => {
        await api.updateVocab(kind, entry.id, {
          name: nameInput.value.trim() || entry.name,
          value_optional: optBox.checked,
          value_pattern: patternInput.value.trim() || null,
        });
        await loadVocab();
      });
    };
    const duplicate = async (): Promise<void> => {
      const name = await textPrompt(t("vocab.duplicatePrompt", { name: entry.name }));
      if (name) {
        await act(async () => {
          await api.duplicateVocab(kind, entry.id, name);
          await loadVocab();
        });
      }
    };
    section.append(
      el("div", { class: "vocab-row" }, [
        nameInput,
        optionalLabel(optBox),
        patternInput,
        button(t("common.save"), save, "btn-mini"),
        button(t("common.duplicate"), () => void duplicate(), "btn-mini"),
        button(t("common.remove"), () => void onRemoveVocab(kind, entry), "btn-mini btn-danger"),
      ]),
    );
  }

  const nameAdd = el("input", {
    class: "input",
    placeholder: t("vocab.newResourceType"),
  }) as HTMLInputElement;
  const optAdd = el("input", { class: "checkbox", type: "checkbox" }) as HTMLInputElement;
  const patternAdd = el("input", {
    class: "input",
    placeholder: t("vocab.regexPlaceholder"),
  }) as HTMLInputElement;
  const add = (): void => {
    const value = nameAdd.value.trim();
    if (value) {
      void act(async () => {
        await api.addVocab(kind, {
          name: value,
          value_optional: optAdd.checked,
          value_pattern: patternAdd.value.trim() || null,
        });
        await loadVocab();
      });
    }
  };
  nameAdd.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      add();
    }
  });
  section.append(
    el("div", { class: "vocab-row" }, [
      nameAdd,
      optionalLabel(optAdd),
      patternAdd,
      button(t("common.add"), add),
    ]),
  );
  return section;
}

// -- audit view ---------------------------------------------------------------

function renderAudit(): HTMLElement {
  const wrap = el("div", { class: "audit" }, [
    el("div", { class: "audit-head" }, [el("h2", { text: t("audit.title") })]),
  ]);
  if (state.audit.length === 0) {
    wrap.append(el("p", { class: "empty", text: t("audit.empty") }));
    return wrap;
  }
  const table = el("table", { class: "audit-table" });
  table.append(
    el("tr", {}, [
      el("th", { text: t("audit.colTime") }),
      el("th", { text: t("audit.colOrigin") }),
      el("th", { text: t("audit.colAction") }),
      el("th", { text: t("audit.colTarget") }),
      el("th", { text: t("audit.colAffected") }),
    ]),
  );
  for (const entry of state.audit) {
    const target =
      entry.target_id != null ? `${entry.target_kind} ${entry.target_id}` : entry.target_kind;
    const affected = Array.isArray(entry.affected_ids) ? String(entry.affected_ids.length) : "";
    table.append(
      el("tr", {}, [
        el("td", { text: entry.ts }),
        el("td", { text: entry.origin }),
        el("td", { text: entry.action_type }),
        el("td", { text: target }),
        el("td", { text: affected }),
      ]),
    );
  }
  wrap.append(table);
  return wrap;
}

// -- search -------------------------------------------------------------------

async function runSearch(query: string, push = true): Promise<void> {
  if (!query) {
    closeSearch();
    return;
  }
  try {
    const hits = await api.search(query);
    const main = byId("app");
    clear(main);
    const panel = el("div", { class: "search-results" }, [
      el("div", { class: "search-head" }, [
        el("h2", { text: t("search.heading", { query, count: hits.length }) }),
        button(t("common.close"), () => closeSearch()),
      ]),
    ]);
    if (hits.length === 0) {
      panel.append(el("p", { class: "empty", text: t("search.empty") }));
    }
    for (const hit of hits) {
      const path = hit.path.length ? hit.path.join(" / ") : t("search.topLevel");
      panel.append(
        el("div", { class: "hit" }, [
          el("span", { class: "hit-kind", text: hit.kind === "category" ? "📁" : "📄" }),
          el("span", { class: "hit-name", text: hit.name }),
          el("span", { class: "hit-path", text: path }),
        ]),
      );
    }
    main.append(panel);
    live.searching = true; // keep results visible across background live refreshes
    currentSearch = query;
    if (push) {
      pushHistory();
    }
    updateNavButtons(); // the overlay didn't go through render(), so refresh nav state
  } catch (error) {
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}

// Leave the search overlay back to the normal view (a navigation in its own right).
function closeSearch(): void {
  currentSearch = null;
  pushHistory();
  render();
}

// -- actions ------------------------------------------------------------------

function onSelectChecklist(event: Event): void {
  const value = (event.target as HTMLSelectElement).value;
  const id = Number(value);
  if (!Number.isNaN(id)) {
    state.activeId = id;
    state.collapsed.clear();
    currentSearch = null;
    pushHistory();
    void selectChecklist();
  }
}

// Selecting a checklist is a local view change (not a server mutation → no SSE event),
// so it loads the chosen tree and renders directly.
async function selectChecklist(): Promise<void> {
  await loadActiveTree();
  if (state.view === "audit") {
    await loadAudit();
  }
  render();
}

async function onCreateBlank(): Promise<void> {
  const name = await textPrompt(t("prompt.newChecklist"));
  if (name) {
    await act(async () => {
      const created = await api.createBlank(name);
      state.activeId = created.id;
    });
  }
}

async function onImport(): Promise<void> {
  const input = await importDialog((text) => api.validateImport(text));
  if (input && input.name) {
    await act(async () => {
      const created = await api.createImport(input.name, input.text);
      state.activeId = created.id;
    });
  }
}

async function onClone(): Promise<void> {
  if (state.activeId === null) {
    return;
  }
  const name = await textPrompt(t("prompt.cloneName"));
  if (name) {
    const source = state.activeId;
    await act(async () => {
      const created = await api.createClone(source, name);
      state.activeId = created.id;
    });
  }
}

async function onDeleteChecklist(): Promise<void> {
  if (state.activeId === null || !state.tree) {
    return;
  }
  if (await confirmDialog(t("confirm.deleteChecklist", { name: state.tree.name }))) {
    const id = state.activeId;
    await act(async () => {
      await api.deleteChecklist(id);
      state.activeId = null;
    });
  }
}

async function onExport(): Promise<void> {
  if (state.activeId === null) {
    return;
  }
  const tree = await api.exportChecklist(state.activeId);
  const blob = new Blob([JSON.stringify(tree, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = el("a", { href: url, download: `${tree.name || "checklist"}.json` });
  anchor.click();
  URL.revokeObjectURL(url);
}

async function onAddCategory(parentId: number | null): Promise<void> {
  if (state.activeId === null) {
    return;
  }
  const name = await textPrompt(t("prompt.categoryName"));
  if (name) {
    const cid = state.activeId;
    await act(() => api.addCategory(cid, name, parentId));
  }
}

async function onAddItem(categoryId: number): Promise<void> {
  if (state.activeId === null) {
    return;
  }
  const template: TreeNode = {
    kind: "expense_item",
    id: 0,
    name: "",
    position: 0,
    done: false,
    data: null,
    instructions: null,
    resources: [],
    tools: [],
  };
  const fields = await itemEditDialog(template, t("item.addTitle"));
  if (fields && fields.name) {
    const cid = state.activeId;
    await act(() => api.addItem(cid, categoryId, { ...fields, name: fields.name! }));
  }
}

async function onToggleDone(node: TreeNode, checkbox: HTMLInputElement): Promise<void> {
  const desired = checkbox.checked;
  if (node.kind === "expense_item") {
    await act(() => api.setItemDone(node.id, desired));
    return;
  }
  if (!desired) {
    const affected = countDoneItems(node);
    const ok = await confirmDialog(
      t("confirm.uncheckCategory", { name: node.name, count: affected }),
    );
    if (!ok) {
      checkbox.checked = true;
      return;
    }
  }
  await act(() => api.setCategoryDone(node.id, desired));
}

async function onRemove(node: TreeNode): Promise<void> {
  const confirmKey = node.kind === "category" ? "confirm.removeCategory" : "confirm.removeItem";
  if (await confirmDialog(t(confirmKey, { name: node.name }))) {
    await act(() => api.removeNode(node.kind, node.id));
  }
}

async function onDrop(targetParentId: number | null, position: number | null): Promise<void> {
  const moving = dragged;
  dragged = null;
  if (!moving) {
    return;
  }
  await act(() => api.move(moving.kind, moving.id, targetParentId, position));
}

async function onEditItem(node: TreeNode): Promise<void> {
  const fields = await itemEditDialog(node);
  if (fields) {
    await act(() => api.editItem(node.id, fields));
  }
}

async function onRemoveVocab(kind: "resource_type" | "tool", entry: VocabEntry): Promise<void> {
  await act(async () => {
    await api.removeVocab(kind, entry.id);
    await loadVocab();
  });
}

// -- item editor dialog -------------------------------------------------------

function itemEditDialog(node: TreeNode, title = t("item.editTitle")): Promise<ItemFields | null> {
  return new Promise((resolve) => {
    const overlay = el("div", { class: "overlay" });
    const finish = (value: ItemFields | null): void => {
      overlay.remove();
      resolve(value);
    };

    const nameInput = el("input", { class: "input", value: node.name }) as HTMLInputElement;
    const dataInput = el("input", { class: "input", value: node.data ?? "" }) as HTMLInputElement;
    const instrInput = el("input", {
      class: "input",
      value: node.instructions ?? "",
    }) as HTMLInputElement;

    const resourceList = el("div", { class: "resource-list" });
    const addResourceRow = (resource?: ResourceRef): void => {
      const typeSelect = el("select", { class: "input" }) as HTMLSelectElement;
      for (const rt of state.resourceTypes) {
        const option = el("option", { value: rt.name, text: rt.name });
        if (resource && resource.type === rt.name) {
          option.setAttribute("selected", "selected");
        }
        typeSelect.append(option);
      }
      const valueInput = el("input", {
        class: "input",
        placeholder: t("item.valuePlaceholder"),
        value: resource?.value ?? "",
      }) as HTMLInputElement;
      const row = el("div", { class: "resource-row" }, [typeSelect, valueInput]);
      row.append(iconButton("trash", t("common.remove"), () => row.remove(), "btn-mini btn-danger"));
      resourceList.append(row);
    };
    for (const resource of node.resources ?? []) {
      addResourceRow(resource);
    }

    const toolBoxes = state.tools.map((tool) => {
      const box = el("input", { class: "checkbox", type: "checkbox", value: tool.name }) as HTMLInputElement;
      box.checked = (node.tools ?? []).includes(tool.name);
      return el("label", { class: "tool-check" }, [box, document.createTextNode(` ${tool.name}`)]);
    });

    const collect = (): ItemFields => {
      const resources: ResourceRef[] = [];
      for (const row of Array.from(resourceList.querySelectorAll(".resource-row"))) {
        const select = row.querySelector("select") as HTMLSelectElement;
        const value = (row.querySelector("input") as HTMLInputElement).value.trim();
        resources.push({ type: select.value, value: value || null });
      }
      const tools: string[] = [];
      for (const label of toolBoxes) {
        const box = label.querySelector("input") as HTMLInputElement;
        if (box.checked) {
          tools.push(box.value);
        }
      }
      return {
        name: nameInput.value.trim() || node.name,
        data: dataInput.value.trim() || null,
        instructions: instrInput.value.trim() || null,
        resources,
        tools,
      };
    };

    const box = el("div", { class: "modal modal-wide" }, [
      el("h3", { text: title }),
      labelled(t("item.name"), nameInput),
      labelled(t("item.data"), dataInput),
      labelled(t("item.instructions"), instrInput),
      el("div", { class: "field" }, [
        el("div", { class: "field-label" }, [
          el("span", { text: t("item.resources") }),
          button(t("item.addResource"), () => addResourceRow(), "btn-mini", "add"),
        ]),
        resourceList,
      ]),
      el("div", { class: "field" }, [
        el("div", { class: "field-label", text: t("item.tools") }),
        ...toolBoxes,
      ]),
      el("div", { class: "modal-actions" }, [
        el("button", { class: "btn", onclick: () => finish(null), text: t("common.cancel") }),
        el("button", {
          class: "btn btn-primary",
          onclick: () => finish(collect()),
          text: t("common.save"),
        }),
      ]),
    ]);
    overlay.append(box);
    document.body.append(overlay);
  });
}

function labelled(label: string, input: HTMLElement): HTMLElement {
  return el("div", { class: "field" }, [el("div", { class: "field-label", text: label }), input]);
}

// -- status bar ---------------------------------------------------------------

// Slim gray bar with the app version, right-aligned. The running app injects the real
// version via window.__RECEIPT_BOARD__; __APP_VERSION__ (baked from package.json) is the
// fallback when served without pywebview. Rendered once — it lives outside #app, so view
// re-renders never clear it.
function renderStatusbar(): void {
  const version = window.__RECEIPT_BOARD__?.version ?? __APP_VERSION__;
  const bar = byId("statusbar");
  clear(bar);
  bar.append(
    el("span", { class: "version", text: `v${version}`, title: t("status.version", { version }) }),
  );
}

// -- entry --------------------------------------------------------------------

export async function start(): Promise<void> {
  renderStatusbar();
  setupNavInputs();
  try {
    await loadVocab();
    await reload();
    pushHistory(); // seed the history with the initial view
    updateNavButtons();
    connectEvents();
    void checkForUpdatesOnStartup();
  } catch (error) {
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}
