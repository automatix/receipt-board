// Typed REST client. Same-origin (served at /app); privileged calls attach the
// session token injected by pywebview (ADR-0009).

import type {
  ChecklistSummary,
  ChecklistTree,
  ImportReport,
  ItemFields,
  NodeKind,
  SearchHit,
  VocabEntry,
  VocabKind,
} from "./types";

export class ApiError extends Error {
  readonly code: string;
  readonly details: unknown;

  constructor(message: string, code: string, details: unknown) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

function headers(): Headers {
  const h = new Headers({ "Content-Type": "application/json" });
  const token = window.__RECEIPT_BOARD__?.token;
  if (token) {
    h.set("X-Session-Token", token);
  }
  return h;
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method, headers: headers() };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }
  const response = await fetch(path, init);
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const error = (data && data.error) || {};
    throw new ApiError(error.message || `HTTP ${response.status}`, error.code || "error", error.details);
  }
  return data as T;
}

export const api = {
  listChecklists: () => request<ChecklistSummary[]>("GET", "/checklists"),
  exportChecklist: (id: number) => request<ChecklistTree>("GET", `/checklists/${id}`),
  search: (q: string) => request<SearchHit[]>("GET", `/search?q=${encodeURIComponent(q)}`),

  createBlank: (name: string) =>
    request<{ id: number }>("POST", "/checklists", { mode: "blank", name }),
  createImport: (name: string, text: string) =>
    request<{ id: number }>("POST", "/checklists", { mode: "import", name, text }),
  validateImport: (text: string) =>
    request<ImportReport>("POST", "/import/validate", { text }),
  createClone: (sourceId: number, name: string) =>
    request<{ id: number }>("POST", "/checklists", { mode: "clone", name, source_id: sourceId }),
  deleteChecklist: (id: number) => request<void>("DELETE", `/checklists/${id}`),

  addCategory: (checklistId: number, name: string, parentId: number | null) =>
    request<{ id: number }>("POST", `/checklists/${checklistId}/categories`, {
      name,
      parent_id: parentId,
    }),
  addItem: (checklistId: number, categoryId: number, fields: ItemFields & { name: string }) =>
    request<{ id: number }>("POST", `/checklists/${checklistId}/items`, {
      category_id: categoryId,
      ...fields,
    }),

  editCategory: (id: number, name: string) =>
    request<void>("PATCH", `/categories/${id}`, { name }),
  editItem: (id: number, fields: ItemFields) => request<void>("PATCH", `/items/${id}`, fields),
  removeNode: (kind: NodeKind, id: number) =>
    request<void>("DELETE", kind === "category" ? `/categories/${id}` : `/items/${id}`),
  move: (kind: NodeKind, id: number, newParentId: number | null, position: number | null) =>
    request<{ affected_ids: unknown[] }>("POST", `/nodes/${kind}/${id}/move`, {
      new_parent_id: newParentId,
      position,
    }),

  setItemDone: (id: number, done: boolean) =>
    request<{ affected_ids: unknown[] }>("POST", `/items/${id}/done`, { done }),
  setCategoryDone: (id: number, done: boolean) =>
    request<{ affected_ids: unknown[] }>("POST", `/categories/${id}/done`, { done }),

  listVocab: (kind: VocabKind) => request<VocabEntry[]>("GET", `/vocab/${kind}`),
  addVocab: (kind: VocabKind, entry: Partial<VocabEntry> & { name: string }) =>
    request<VocabEntry>("POST", `/vocab/${kind}`, entry),
  updateVocab: (kind: VocabKind, id: number, patch: Partial<VocabEntry>) =>
    request<VocabEntry>("PATCH", `/vocab/${kind}/${id}`, patch),
  duplicateVocab: (kind: VocabKind, id: number, name: string) =>
    request<VocabEntry>("POST", `/vocab/${kind}/${id}/duplicate`, { name }),
  removeVocab: (kind: VocabKind, id: number) => request<void>("DELETE", `/vocab/${kind}/${id}`),
};
