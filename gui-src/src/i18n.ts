// Internationalization (issue #84): a tiny message catalog with **English as the default
// language** and **German as a full second locale** (matching the strings the app shipped
// before i18n). The active locale is persisted in localStorage; t(key, params) looks it up
// and interpolates {name} placeholders. Unknown keys fall back to English, then to the key.

export type Locale = "en" | "de";

export const LOCALES: Locale[] = ["en", "de"];
const STORAGE_KEY = "receiptboard.lang";

type Catalog = Record<string, string>;

const en: Catalog = {
  "common.cancel": "Cancel",
  "common.ok": "OK",
  "common.save": "Save",
  "common.add": "Add",
  "common.remove": "Remove",
  "common.close": "Close",
  "common.duplicate": "Duplicate",
  "common.edit": "Edit",
  "common.none": "(none)",

  "toolbar.new": "New",
  "toolbar.import": "Import",
  "toolbar.clone": "Clone",
  "toolbar.delete": "Delete",
  "toolbar.export": "Export",
  "toolbar.updates": "Updates",
  "toolbar.search": "Search…",
  "toolbar.checklist": "Checklist",
  "toolbar.vocab": "Vocabulary",
  "toolbar.audit": "Audit",

  "theme.system": "🌗 System",
  "theme.dark": "🌙 Dark",
  "theme.light": "☀ Light",

  "tree.empty": "No checklist. Create one or import.",
  "tree.addCategory": "Category",
  "tree.addItem": "Item",

  "vocab.title": "Vocabulary",
  "vocab.tools": "Tools",
  "vocab.resourceTypes": "Resource Types",
  "vocab.valueOptional": "Value optional",
  "vocab.regexPlaceholder": "Regex (optional)",
  "vocab.newTool": "New tool…",
  "vocab.newResourceType": "New resource type (key)…",
  "vocab.duplicatePrompt": 'Duplicate of "{name}" – new key',

  "audit.title": "Audit log",
  "audit.empty": "No audit entries.",
  "audit.colTime": "Time",
  "audit.colOrigin": "Origin",
  "audit.colAction": "Action",
  "audit.colTarget": "Target",
  "audit.colAffected": "Affected",

  "search.heading": 'Search: "{query}" ({count})',
  "search.empty": "No matches.",
  "search.topLevel": "(top level)",

  "item.editTitle": "Edit item",
  "item.addTitle": "Add item",
  "item.name": "Name",
  "item.data": "Data",
  "item.instructions": "Instructions",
  "item.resources": "Resources",
  "item.addResource": "Resource",
  "item.tools": "Tools",
  "item.valuePlaceholder": "value (optional)",

  "prompt.newChecklist": "New checklist (empty)",
  "prompt.cloneName": "Clone name",
  "prompt.categoryName": "Category name",
  "confirm.deleteChecklist": 'Permanently delete checklist "{name}"?',
  "confirm.uncheckCategory":
    'Uncheck category "{name}"? {count} completed item(s) will be reset.',
  "confirm.removeCategory": 'Remove category "{name}"?',
  "confirm.removeItem": 'Remove item "{name}"?',

  "import.title": "Import checklist",
  "import.namePlaceholder": "Checklist name",
  "import.textPlaceholder": "Paste Markdown…",
  "import.check": "Check",
  "import.run": "Import",
  "import.checking": "Checking…",
  "import.ok": "✓ Importable: {categories} categories, {items} items",
  "import.bad": "✗ {count} error(s) — not importable:",
  "import.issue": "Line {line} · {token} · {message}",
  "import.warning": "Warning line {line}: {message}",
  "import.error": "Error: {message}",

  "update.available": "New version {latest} available (installed: {current}).",
  "update.whatsNew": "What's new?",
  "update.installNow": "Install now",
  "update.later": "Later",
  "update.downloading": "Downloading…",
  "update.launching": "Launching installer – the app will close…",
  "update.upToDate": "Up to date – version {current} is the latest.",
};

const de: Catalog = {
  "common.cancel": "Abbrechen",
  "common.ok": "OK",
  "common.save": "Speichern",
  "common.add": "Hinzufügen",
  "common.remove": "Entfernen",
  "common.close": "Schließen",
  "common.duplicate": "Duplizieren",
  "common.edit": "Bearbeiten",
  "common.none": "(keine)",

  "toolbar.new": "Neu",
  "toolbar.import": "Import",
  "toolbar.clone": "Klonen",
  "toolbar.delete": "Löschen",
  "toolbar.export": "Export",
  "toolbar.updates": "Updates",
  "toolbar.search": "Suchen…",
  "toolbar.checklist": "Checklist",
  "toolbar.vocab": "Vokabular",
  "toolbar.audit": "Audit",

  "theme.system": "🌗 System",
  "theme.dark": "🌙 Dark",
  "theme.light": "☀ Light",

  "tree.empty": "Keine Checklist. Lege eine an oder importiere.",
  "tree.addCategory": "Kategorie",
  "tree.addItem": "Eintrag",

  "vocab.title": "Vokabular",
  "vocab.tools": "Tools",
  "vocab.resourceTypes": "Resource Types",
  "vocab.valueOptional": "Wert optional",
  "vocab.regexPlaceholder": "Regex (optional)",
  "vocab.newTool": "Neuer Tool…",
  "vocab.newResourceType": "Neuer Resource Type (Key)…",
  "vocab.duplicatePrompt": 'Duplikat von "{name}" – neuer Key',

  "audit.title": "Audit-Log",
  "audit.empty": "Keine Audit-Einträge.",
  "audit.colTime": "Zeit",
  "audit.colOrigin": "Herkunft",
  "audit.colAction": "Aktion",
  "audit.colTarget": "Ziel",
  "audit.colAffected": "Betroffen",

  "search.heading": 'Suche: "{query}" ({count})',
  "search.empty": "Keine Treffer.",
  "search.topLevel": "(oberste Ebene)",

  "item.editTitle": "Eintrag bearbeiten",
  "item.addTitle": "Eintrag hinzufügen",
  "item.name": "Name",
  "item.data": "Data",
  "item.instructions": "Instructions",
  "item.resources": "Resources",
  "item.addResource": "Resource",
  "item.tools": "Tools",
  "item.valuePlaceholder": "value (optional)",

  "prompt.newChecklist": "Neue Checklist (leer)",
  "prompt.cloneName": "Klon-Name",
  "prompt.categoryName": "Kategorie-Name",
  "confirm.deleteChecklist": 'Checklist "{name}" endgültig löschen?',
  "confirm.uncheckCategory":
    'Kategorie "{name}" abwählen? {count} erledigte(r) Eintrag/Einträge werden zurückgesetzt.',
  "confirm.removeCategory": 'Kategorie "{name}" entfernen?',
  "confirm.removeItem": 'Eintrag "{name}" entfernen?',

  "import.title": "Checklist importieren",
  "import.namePlaceholder": "Checklist-Name",
  "import.textPlaceholder": "Markdown einfügen…",
  "import.check": "Prüfen",
  "import.run": "Importieren",
  "import.checking": "Prüfe…",
  "import.ok": "✓ Importierbar: {categories} Kategorien, {items} Einträge",
  "import.bad": "✗ {count} Fehler — nicht importierbar:",
  "import.issue": "Zeile {line} · {token} · {message}",
  "import.warning": "Warnung Zeile {line}: {message}",
  "import.error": "Fehler: {message}",

  "update.available": "Neue Version {latest} verfügbar (installiert: {current}).",
  "update.whatsNew": "Was ist neu?",
  "update.installNow": "Jetzt installieren",
  "update.later": "Später",
  "update.downloading": "Wird geladen…",
  "update.launching": "Installer wird gestartet – die App wird geschlossen…",
  "update.upToDate": "Aktuell – Version {current} ist die neueste.",
};

const catalogs: Record<Locale, Catalog> = { en, de };

let active: Locale = loadLocale();

export function loadLocale(): Locale {
  const value = localStorage.getItem(STORAGE_KEY);
  return value === "de" || value === "en" ? value : "en";
}

export function getLocale(): Locale {
  return active;
}

export function setLocale(locale: Locale): void {
  active = locale;
  localStorage.setItem(STORAGE_KEY, locale);
  document.documentElement.lang = locale;
}

// Apply the persisted locale to <html lang> without changing it (called at startup).
export function initLocale(): void {
  document.documentElement.lang = active;
}

export function nextLocale(): Locale {
  return LOCALES[(LOCALES.indexOf(active) + 1) % LOCALES.length]!;
}

export function localeLabel(locale: Locale = active): string {
  return `🌐 ${locale.toUpperCase()}`;
}

export function t(key: string, params?: Record<string, string | number>): string {
  const template = catalogs[active][key] ?? en[key] ?? key;
  if (!params) {
    return template;
  }
  return template.replace(/\{(\w+)\}/g, (_match, name: string) =>
    name in params ? String(params[name]) : `{${name}}`,
  );
}
