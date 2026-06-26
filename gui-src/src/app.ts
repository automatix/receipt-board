// Receipt Board GUI application (TECH_SPEC §7).
//
// A framework-free SPA over the REST API: checklist tree with collapse, done checkboxes
// with cascade (category uncheck confirmed with the affected count), inline rename, an
// item editor (data/instructions/resources/tools), native HTML5 drag & drop for
// reorder/re-parent, vocabulary management, search, and checklist create/import/clone/
// delete/export. The active checklist is reloaded after every mutating action.

import { ApiError, api } from "./api";
import type {
  ChecklistSummary,
  ChecklistTree,
  ItemFields,
  NodeKind,
  ResourceRef,
  TreeNode,
  VocabEntry,
} from "./types";
import {
  type ThemeMode,
  applyTheme,
  loadTheme,
  nextTheme,
  saveTheme,
  themeLabel,
} from "./theme";
import {
  byId,
  clear,
  confirmDialog,
  el,
  importDialog,
  textPrompt,
  toast,
} from "./ui";

interface State {
  checklists: ChecklistSummary[];
  activeId: number | null;
  tree: ChecklistTree | null;
  view: "checklist" | "vocab";
  resourceTypes: VocabEntry[];
  tools: VocabEntry[];
  collapsed: Set<number>;
}

const state: State = {
  checklists: [],
  activeId: null,
  tree: null,
  view: "checklist",
  resourceTypes: [],
  tools: [],
  collapsed: new Set(),
};

let dragged: { kind: NodeKind; id: number } | null = null;
let themeMode: ThemeMode = loadTheme();
const parentOf = new Map<string, number | null>();

const key = (kind: NodeKind, id: number): string => `${kind}:${id}`;

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

async function reload(): Promise<void> {
  await loadChecklists();
  await loadActiveTree();
  render();
}

// Run a mutating action, surfacing API errors as toasts and reloading on success.
// Reloads the checklist list too so the toolbar dropdown stays current after a
// create/import/clone/delete (and reflects the active selection after any action).
async function act(action: () => Promise<unknown>): Promise<void> {
  try {
    await action();
    await loadChecklists();
    await loadActiveTree();
    render();
  } catch (error) {
    if (error instanceof ApiError) {
      toast(error.message, true);
    } else {
      toast(String(error), true);
    }
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
  renderToolbar();
  const main = byId("app");
  clear(main);
  if (state.view === "vocab") {
    main.append(renderVocab());
  } else if (!state.tree) {
    main.append(el("p", { class: "empty", text: "Keine Checklist. Lege eine an oder importiere." }));
  } else {
    indexParentMap(state.tree);
    main.append(renderTree(state.tree));
  }
}

function renderToolbar(): void {
  const bar = byId("toolbar");
  clear(bar);

  const selector = el("select", { class: "input", onchange: onSelectChecklist }) as HTMLSelectElement;
  for (const checklist of state.checklists) {
    const option = el("option", { value: String(checklist.id), text: checklist.name });
    if (checklist.id === state.activeId) {
      option.setAttribute("selected", "selected");
    }
    selector.append(option);
  }
  if (state.checklists.length === 0) {
    selector.append(el("option", { text: "(keine)" }));
  }

  const search = el("input", { class: "input search", placeholder: "Suchen…" }) as HTMLInputElement;
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      void runSearch(search.value.trim());
    }
  });

  bar.append(
    el("div", { class: "toolbar-group" }, [
      selector,
      button("Neu", () => void onCreateBlank()),
      button("Import", () => void onImport()),
      button("Klonen", () => void onClone()),
      button("Löschen", () => void onDeleteChecklist(), "btn-danger"),
      button("Export", () => void onExport()),
      button("Aktualisieren", () => void reload()),
    ]),
    el("div", { class: "toolbar-group" }, [
      search,
      button(state.view === "vocab" ? "Checklist" : "Vokabular", () => {
        state.view = state.view === "vocab" ? "checklist" : "vocab";
        render();
      }),
      button(themeLabel(themeMode), () => {
        themeMode = nextTheme(themeMode);
        applyTheme(themeMode);
        saveTheme(themeMode);
        renderToolbar();
      }),
    ]),
  );
}

function button(label: string, onClick: () => void, extra = ""): HTMLButtonElement {
  return el("button", { class: `btn ${extra}`.trim(), onclick: onClick, text: label });
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
      button("+ Kategorie", () => void onAddCategory(null)),
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
        button("+ Kategorie", () => void onAddCategory(node.id)),
        button("+ Eintrag", () => void onAddItem(node.id)),
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
  const commit = (): void => {
    const value = input.value.trim();
    if (value && value !== node.name) {
      void act(() =>
        node.kind === "category" ? api.editCategory(node.id, value) : api.editItem(node.id, { name: value }),
      );
    } else {
      render();
    }
  };
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      commit();
    } else if (event.key === "Escape") {
      render();
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
    actions.append(button("✎", () => void onEditItem(node), "btn-mini"));
  }
  actions.append(button("🗑", () => void onRemove(node), "btn-mini btn-danger"));
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
  const wrap = el("div", { class: "vocab" }, [el("h2", { text: "Vokabular" })]);
  wrap.append(renderResourceTypeSection(state.resourceTypes));
  wrap.append(renderVocabSection("Tools", "tool", state.tools));
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
        button("Entfernen", () => void onRemoveVocab(kind, entry), "btn-mini btn-danger"),
      ]),
    );
  }
  const adder = el("input", { class: "input", placeholder: `Neuer ${title}…` }) as HTMLInputElement;
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
  section.append(el("div", { class: "vocab-row" }, [adder, button("Hinzufügen", add)]));
  return section;
}

// Resource types carry a key, value-optionality and a value regex; full CRUD + duplicate.
function renderResourceTypeSection(entries: VocabEntry[]): HTMLElement {
  const kind = "resource_type" as const;
  const optionalLabel = (box: HTMLInputElement): HTMLElement =>
    el("label", { class: "tool-check" }, [box, document.createTextNode(" Wert optional")]);
  const section = el("div", { class: "vocab-section" }, [el("h3", { text: "Resource Types" })]);

  for (const entry of entries) {
    const nameInput = el("input", { class: "input inline", value: entry.name }) as HTMLInputElement;
    const optBox = el("input", { class: "checkbox", type: "checkbox" }) as HTMLInputElement;
    optBox.checked = entry.value_optional ?? false;
    const patternInput = el("input", {
      class: "input",
      placeholder: "Regex (optional)",
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
      const name = await textPrompt(`Duplikat von "${entry.name}" – neuer Key`);
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
        button("Speichern", save, "btn-mini"),
        button("Duplizieren", () => void duplicate(), "btn-mini"),
        button("Entfernen", () => void onRemoveVocab(kind, entry), "btn-mini btn-danger"),
      ]),
    );
  }

  const nameAdd = el("input", {
    class: "input",
    placeholder: "Neuer Resource Type (Key)…",
  }) as HTMLInputElement;
  const optAdd = el("input", { class: "checkbox", type: "checkbox" }) as HTMLInputElement;
  const patternAdd = el("input", {
    class: "input",
    placeholder: "Regex (optional)",
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
      button("Hinzufügen", add),
    ]),
  );
  return section;
}

// -- search -------------------------------------------------------------------

async function runSearch(query: string): Promise<void> {
  if (!query) {
    render();
    return;
  }
  try {
    const hits = await api.search(query);
    const main = byId("app");
    clear(main);
    const panel = el("div", { class: "search-results" }, [
      el("div", { class: "search-head" }, [
        el("h2", { text: `Suche: "${query}" (${hits.length})` }),
        button("Schließen", () => render()),
      ]),
    ]);
    if (hits.length === 0) {
      panel.append(el("p", { class: "empty", text: "Keine Treffer." }));
    }
    for (const hit of hits) {
      const path = hit.path.length ? hit.path.join(" / ") : "(oberste Ebene)";
      panel.append(
        el("div", { class: "hit" }, [
          el("span", { class: "hit-kind", text: hit.kind === "category" ? "📁" : "📄" }),
          el("span", { class: "hit-name", text: hit.name }),
          el("span", { class: "hit-path", text: path }),
        ]),
      );
    }
    main.append(panel);
  } catch (error) {
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}

// -- actions ------------------------------------------------------------------

function onSelectChecklist(event: Event): void {
  const value = (event.target as HTMLSelectElement).value;
  const id = Number(value);
  if (!Number.isNaN(id)) {
    state.activeId = id;
    state.collapsed.clear();
    void act(async () => {});
  }
}

async function onCreateBlank(): Promise<void> {
  const name = await textPrompt("Neue Checklist (leer)");
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
  const name = await textPrompt("Klon-Name");
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
  if (await confirmDialog(`Checklist "${state.tree.name}" endgültig löschen?`)) {
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
  const name = await textPrompt("Kategorie-Name");
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
  const fields = await itemEditDialog(template, "Eintrag hinzufügen");
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
      `Kategorie "${node.name}" abwählen? ${affected} erledigte(r) Eintrag/Einträge werden zurückgesetzt.`,
    );
    if (!ok) {
      checkbox.checked = true;
      return;
    }
  }
  await act(() => api.setCategoryDone(node.id, desired));
}

async function onRemove(node: TreeNode): Promise<void> {
  const label = node.kind === "category" ? "Kategorie" : "Eintrag";
  if (await confirmDialog(`${label} "${node.name}" entfernen?`)) {
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

function itemEditDialog(node: TreeNode, title = "Eintrag bearbeiten"): Promise<ItemFields | null> {
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
        placeholder: "value (optional)",
        value: resource?.value ?? "",
      }) as HTMLInputElement;
      const row = el("div", { class: "resource-row" }, [typeSelect, valueInput]);
      row.append(button("×", () => row.remove(), "btn-mini btn-danger"));
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
      labelled("Name", nameInput),
      labelled("Data", dataInput),
      labelled("Instructions", instrInput),
      el("div", { class: "field" }, [
        el("div", { class: "field-label" }, [
          el("span", { text: "Resources" }),
          button("+ Resource", () => addResourceRow(), "btn-mini"),
        ]),
        resourceList,
      ]),
      el("div", { class: "field" }, [el("div", { class: "field-label", text: "Tools" }), ...toolBoxes]),
      el("div", { class: "modal-actions" }, [
        el("button", { class: "btn", onclick: () => finish(null), text: "Abbrechen" }),
        el("button", { class: "btn btn-primary", onclick: () => finish(collect()), text: "Speichern" }),
      ]),
    ]);
    overlay.append(box);
    document.body.append(overlay);
  });
}

function labelled(label: string, input: HTMLElement): HTMLElement {
  return el("div", { class: "field" }, [el("div", { class: "field-label", text: label }), input]);
}

// -- entry --------------------------------------------------------------------

export async function start(): Promise<void> {
  try {
    await loadVocab();
    await reload();
  } catch (error) {
    toast(error instanceof ApiError ? error.message : String(error), true);
  }
}
