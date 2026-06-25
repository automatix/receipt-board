// Domain types mirroring the REST contract (TECH_SPEC §9).

export type NodeKind = "category" | "expense_item";
export type VocabKind = "resource_type" | "tool";

export interface RbConfig {
  token: string;
}

export interface ResourceRef {
  type: string;
  value: string | null;
}

export interface TreeNode {
  kind: NodeKind;
  id: number;
  name: string;
  position: number;
  done: boolean;
  children?: TreeNode[];
  data?: string | null;
  instructions?: string | null;
  resources?: ResourceRef[];
  tools?: string[];
}

export interface ChecklistTree {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  children: TreeNode[];
}

export interface ChecklistSummary {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface SearchHit {
  id: number;
  name: string;
  kind: NodeKind;
  checklist_id: number;
  path: string[];
}

export interface VocabEntry {
  id: number;
  name: string;
}

export interface ItemFields {
  name?: string;
  data?: string | null;
  instructions?: string | null;
  resources?: ResourceRef[];
  tools?: string[];
}

declare global {
  interface Window {
    __RECEIPT_BOARD__?: RbConfig;
  }
}
