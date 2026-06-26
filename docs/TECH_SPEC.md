# Receipt Board — Technische Spezifikation (`v1`)

> Detail-Spezifikation auf Basis von [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md),
> [`GLOSSARY.md`](./GLOSSARY.md), den [ADRs](./adr/README.md) und den Antworten aus
> [`TECH_SESSION_AGENDA.md`](./TECH_SESSION_AGENDA.md). Bei Konflikt gewinnen Glossar + ADRs.
> Deferred-Themen stehen in [`BACKLOG.md`](./BACKLOG.md).

---

## 1. Tech-Stack & Tooling

| Bereich | Wahl | Ref |
| ------- | ---- | --- |
| Sprache Backend | `Python` `3.12+` | A4 |
| Dependency-Mgmt | `uv` (Lockfile) | A1 |
| Lint/Format | `ruff` (Lint + Format) | A2 |
| Typecheck Python | **keiner** (`mypy` bewusst weggelassen) | A2 |
| Web-Framework | `FastAPI` (lokal, Loopback) | E |
| DB | `SQLite` (WAL) | B |
| Migrations | `Alembic` | B5 |
| GUI | `TypeScript` + `HTML`/`CSS`, **kein** Framework, Build via `esbuild` | G1 |
| GUI-Host | `pywebview` | Brief |
| CLI | HTTP-Client gegen lokalen Server | F2, ADR-0011 |
| Packaging | `PyInstaller` (`onedir`, `--windowed`) | I1 |
| Tests | `pytest` + `pytest-cov`, Gate ≥ `90 %` in GitHub Actions | I3 |

**Build-Voraussetzungen (Dev):** `Python` + `uv`; **`Node.js`** für den GUI-`esbuild`-Build
(Konsequenz aus „TypeScript"). Der gebündelte JS-Output wird in das Package aufgenommen.

## 2. Repo-Layout (A3)

```
receipt-board/
├─ src/receipt_board/
│  ├─ core/          # Domäne + Services (ChecklistService, VocabularyService,
│  │                 #   ImportService, AuditService), Cascade, Fehler-Typen
│  ├─ persistence/   # SQLAlchemy-Modelle, Repository, Alembic-Migrations
│  ├─ api/           # FastAPI-App, Router (public/privileged), Pydantic-Schemas
│  ├─ cli/           # CLI (HTTP-Client)
│  ├─ importer/      # Markdown-Parser + Validierung
│  └─ gui/           # statische Assets (gebündeltes JS/CSS/HTML)
├─ gui-src/          # TypeScript-Quellen (esbuild → src/receipt_board/gui/)
├─ tests/
├─ pyproject.toml    # uv, ruff, pytest, coverage
└─ alembic.ini
```

---

## 3. Datenmodell & Schema (B)

Aggregat = `Checklist` (ADR-0007). Persistenz = flache Adjazenzliste, zwei Node-Tabellen.
PKs = **Integer**, pro Tabelle (ADR-0010). `done` als `INTEGER` (0/1).

### Tabellen

- **`checklists`**: `id` PK, `name` NOT NULL, `created_at`, `updated_at`.
- **`categories`**: `id` PK, `checklist_id` → `checklists` `ON DELETE CASCADE`,
  `parent_id` → `categories` NULL `ON DELETE CASCADE`, `name` NOT NULL, `position` NOT NULL,
  `done` NOT NULL DEFAULT 0, `created_at`, `updated_at`.
- **`expense_items`**: `id` PK, `checklist_id` → `checklists` `ON DELETE CASCADE`,
  `category_id` → `categories` **NOT NULL** `ON DELETE CASCADE`, `name` NOT NULL,
  `position` NOT NULL, `done` NOT NULL DEFAULT 0, `data` TEXT NULL, `instructions` TEXT NULL,
  `created_at`, `updated_at`.
- **`resource_types`**: `id` PK, `name` NOT NULL `UNIQUE` (the type key), `value_optional`
  NOT NULL DEFAULT 0, `value_pattern` TEXT NULL (regex a value must match / used to type a
  bare token). (Vocab; Seed: `URL` `^https?://`, `Email` optional `^[^@\s]+@[^@\s]+\.[^@\s]+$`.)
- **`tools`**: `id` PK, `name` NOT NULL `UNIQUE`. (Vocab; Seed: `Browser`, `Thunderbird`.)
- **`item_resources`**: `id` PK, `item_id` → `expense_items` `ON DELETE CASCADE`,
  `resource_type_id` → `resource_types` `ON DELETE RESTRICT`, `value` TEXT **NULL**,
  `position` NOT NULL.
- **`item_tools`**: `id` PK, `item_id` → `expense_items` `ON DELETE CASCADE`,
  `tool_id` → `tools` `ON DELETE RESTRICT`, `position` NOT NULL, `UNIQUE(item_id, tool_id)`.
- **`audit_log`**: siehe §8.
- **`alembic_version`**: von `Alembic` verwaltet.

### Regeln & Invarianten

- **`position`** (B2): ein gemeinsamer Integer je Elternknoten über **beide** Node-Tabellen;
  Kinder werden nach `position` gemischt dargestellt. Umsortieren schreibt die betroffenen
  Geschwister contiguous neu. Top-Level = nur Kategorien (Items brauchen `category_id`).
- **Cascade-Invariante** (ADR-0002): `category.done ⇔ alle Kinder done` (Kinder =
  Unterkategorien + Items), vom Service gewahrt.
- **FK-Pragmas** (B4): `foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000`.
- **Indizes (B4):** `v1` minimal — nur PKs + `UNIQUE`(Vokabular-Namen). FK-/`name`-Indizes
  und `FTS5` → [`BACKLOG.md`](./BACKLOG.md).

---

## 4. Domänen-/Service-Layer (C)

- **`ChecklistService`**: `create_blank(name)`, `import_markdown(name, text)` (→ ImportService),
  `clone(checklist_id, new_name)`, `delete(checklist_id)`, `add_category(parent, name, pos?)`,
  `add_item(category_id, name, fields, pos?)`, `edit_node(kind, id, fields)`,
  `remove_node(kind, id)`, `move_node(kind, id, new_parent, pos)`,
  `set_item_done(item_id, done: bool)`.
- **`VocabularyService`**: `add(kind, name)`, `rename(kind, id, name)`,
  `remove(kind, id)` (blockt bei Nutzung → `VocabularyInUseError`).
- **`ImportService`**: Parse + Validierung (§6), atomar.
- **`AuditService`**: schreibt je Aktion **einen** Eintrag (§8).

**Cascade-Umsetzung (C2):** app-seitige Traversierung im Service; gebündelte `UPDATE`s in
**einer** Transaktion. Roll-up-/Lese-Abfragen dürfen rekursive SQL-CTEs nutzen.
Jede schreibende Operation: eine Transaktion → Mutation + Cascade + **ein** Audit-Eintrag.

**Fehler-Typen (C3):** `NotFoundError`, `ValidationError`, `VocabularyInUseError`,
`InvalidImportError` — zentral auf REST-/CLI-Fehler gemappt.

---

## 5. Cascade & `done` (ADR-0002)

- `set_node(kind, id, value)` → alle Nachkommen auf `value`; danach Vorfahren aufrollen
  (`ancestor.done = AND(direkte Kinder)`).
- **Leere Kategorie (Edge-Case):** der Roll-up lässt eine Kategorie **ohne Kinder**
  unverändert (kein vakuumes `done=true`); ein direktes Toggle setzt sie weiterhin. So
  führt z. B. das Entfernen des letzten Kindes nicht zum stillen „Erledigt".
- Extern (HTTP/CLI) ist **nur** `set_item_done` erlaubt (ADR-0003); Kategorie-`done` ändert
  sich extern nur via Roll-up (intern/GUI über `POST /categories/{id}/done`).
- Tool führt Cascade stur aus; destruktiver Schutz = GUI (Bestätigung, §7).

---

## 6. Import (D, ADR-0005)

**Quelle:** verschachtelte `- [ ]`/`- [x]`-Markdown-Checkliste.

1. **Parse (D1):** Einrückung bestimmt Hierarchie (Tabs/Spaces normalisiert, Einheit
   auto-erkannt); jede Zeile = Node; Typ strukturell (Blätter → `Expense Item`, Vorfahren →
   `Category`, ADR-0006); `name` = Text vor erster Klammergruppe (getrimmt);
   `done` aus `[x]`/`[ ]`.
2. **Felder (strikt nach Klammer-Typ):** `(...)`→`resources`, `{...}`→`tools`,
   `[...]`→`data`, `<...>`→`instructions`; Mehrfachwerte per `|`.
3. **Typisierung (D2) — datengetrieben, case-insensitive (kein if-else):** ein
   resource-Token wird generisch gegen die `resource_types` aufgelöst: `Key: value`
   (Key = Typname, `value` muss `value_pattern` erfüllen), ein bloßer `Key` (wenn
   `value_optional`, z. B. `Email`), oder ein bloßer Wert (typisiert durch den ersten Typ,
   dessen `value_pattern` matcht — z. B. `https://…`→`URL`, `a@b.de`→`Email`). tool-Token
   case-insensitive gegen `tools`-Vokabular.
4. **Validierung & Atomarität (D3, ADR-0005):** zwei-Phasen — erst komplett parsen +
   validieren, **alle** Fehler sammeln (Zeilennr. + Token + betroffenes Vokabular); bei
   Fehlern Abbruch **ohne** Schreiben + Report (empfiehlt Vokabular-Erweiterung via GUI);
   sonst Insert in **einer** Transaktion. Import ist GUI-privilegiert.

**Reservierte Kontrollzeichen (strikt):** Die acht Zeichen `(` `)` `[` `]` `{` `}` `<` `>`
sind **reserviert** (Feld-Delimiter) und im **Freitext** (Namen und Feldwerte) **nicht
zulässig**. Ein reserviertes Zeichen im Wert (z. B. ein `<…>` innerhalb eines `[...]`) ist
ein `syntax`-Fehler und bricht den atomaren Import ab. **Felder werden nur für `Expense
Item`s** geparst; auf einem Knoten, der strukturell zur `Category` wird, werden
Klammer-Inhalte ignoriert (Warnung). **Konsequenz:** Die reale Referenzdatei
`Expenses Checklist 2024_v02.md` importiert **nicht** unverändert — sie nutzt Klammern als
Namens-Zusatz (`Taxi (klassisch)`) bzw. `<…>` im Freitext (`…/<DOMAN>/…`) — und wird mit
präzisem, zeilenbezogenem Report abgelehnt. Der Erfolgsfall wird gegen eine
notations-konforme Fixture getestet.

---

## 7. GUI (G)

- **Tech (G1):** `TypeScript`, **kein** Framework, `esbuild`-Bundle (aus `gui-src/`) →
  `src/receipt_board/gui/static/`. Der lokale Server liefert die GUI **same-origin** unter
  `/app` aus (vermeidet `file://`→Loopback-CORS); das `pywebview`-Fenster lädt
  `http://127.0.0.1:{port}/app/`.
- **Baum (G2):** verschachtelte Listen; Inline-Edit der Felder; **natives HTML5-Drag&Drop**
  für Umsortieren/Re-Parenting (`position`-Update + Cascade-Roll-up).
- **Bestätigungen (G3):** Dialoge für Kategorie-Abwählen (mit Anzahl betroffener Items),
  Remove, Checklist-Löschen. **Undo** → Backlog.
- **Vokabular-Screen (G4):** hinzufügen/umbenennen; entfernen nur ungenutzt.
- **Suche:** Box → flache Trefferliste (`id`, `name`, `kind`, `checklist_id`, Pfad).
- **Token (ADR-0009):** nach dem Laden via `pywebview.evaluate_js` als
  `window.__RECEIPT_BOARD__.token` injiziert; an privilegierte Endpunkte als
  `X-Session-Token` gesendet.
- **Refresh (G4/H3):** aktive `Checklist` nach jeder mutierenden Aktion neu laden +
  manueller Refresh-Button. Live-Polling → Backlog.

---

## 8. Audit & Concurrency (H)

### `audit_log`-Schema (H1, erweitert)

`id` PK, `ts` (ISO-8601), `origin` (`GUI`/`CLI`/`REST`), `action_type`, `target_kind`
(`checklist`/`category`/`expense_item`/`vocabulary`), `target_id`, `checklist_id`,
`payload` (`JSON`: `old`/`new`), `affected_ids` (`JSON`-Liste), `app_version`, `session_id`.

- **`affected_ids` (H2):** die Cascade-Routine liefert die geänderten IDs zurück; **ein**
  Audit-Eintrag in derselben Transaktion. Bei strukturellen Ops (Anlegen/Verschieben)
  enthält `affected_ids` die per Roll-up geänderten Knoten; bei Lösch-Ops ist es leer.
- **`origin`-Erkennung:** gültiges `X-Session-Token` → `GUI`; Header
  `X-Receipt-Board-Client: cli` → `CLI`; sonst → `REST`.
- **Concurrency (ADR-0008):** eine `SQLite`-Transaktion pro Aktion (WAL), last-write-wins,
  kein App-Lock.
- **GUI-Refresh (H3):** manuell/aktionsbezogen (siehe §7).

---

## 9. REST-Vertrag (E)

- **Bind:** `127.0.0.1`, **ephemerer** Port; `runtime.json` (nur Port) im App-Daten-Ordner
  (E3). **Token:** Header `X-Session-Token` für privilegierte Endpunkte (ADR-0009).
- **Schemas/Fehler (E2):** `Pydantic`; Fehler `{error:{code,message,details}}`; `OpenAPI` auto.

| Methode & Pfad | Tier | Zweck |
| -------------- | ---- | ----- |
| `GET /checklists` | public | Liste der Checklists |
| `GET /checklists/{id}` | public | **nested** Export (§Export) |
| `GET /search?q=` | public | flache Treffer |
| `POST /items/{id}/done` | public | `{done: bool}` — einzige öffentliche Schreib-Op |
| `POST /import/validate` | public | `{text}` → Dry-Run-Report `{valid,errors,warnings,summary}` (schreibt nichts) |
| `GET /audit?checklist_id=&limit=` | public | Audit-Log lesen (neueste zuerst; read-only) |
| `POST /checklists` (blank/import/clone) | privileged | anlegen |
| `DELETE /checklists/{id}` | privileged | löschen |
| `POST/PATCH/DELETE /categories…`, `…/items…` | privileged | CRUD |
| `POST /categories/{id}/done` | privileged | `{done: bool}` — Kategorie-Toggle (Cascade) |
| `POST /nodes/{kind}/{id}/move` | privileged | Re-Parent/Reorder |
| `GET/POST/PATCH/DELETE /vocab/{kind}…` | privileged | Vokabular-Pflege (resource_type trägt `value_optional`/`value_pattern`) |
| `POST /vocab/{kind}/{id}/duplicate` | privileged | `{name}` — Vokabular-Eintrag duplizieren |

> Die gebaute GUI wird (sofern vorhanden) unter `/app` ausgeliefert (StaticFiles, §7).

---

## 10. CLI (F, ADR-0011)

- HTTP-Client gegen den laufenden Server (Public-Surface); Port aus `runtime.json`.
- Befehle (F1): `receipt-board export [--checklist ID]`, `search QUERY`,
  `item done ID`, `item undone ID`, `validate PATH` (Dry-Run-Importprüfung),
  `audit [--checklist ID] [--limit N]` (Audit-Log lesen); Ausgabe `--json`.
- Exit-Code `0` ok, `≠0` bei Fehler (`validate` → `1`, wenn die Datei nicht importierbar ist).
  **Voraussetzung:** App läuft (sonst Fehler; Headless-Modus → Backlog).

---

## 11. Packaging, Config & First-Run (I)

- **PyInstaller (I1):** `onedir`, `--windowed` (kein Konsolenfenster); GUI-Assets **und**
  `Alembic`-Migrations via `--add-data` (`receipt_board.spec`). App-Icon optional unter
  `packaging/icon.ico` (sonst PyInstaller-Default — Backlog).
- **Pfade/Config (I2):** via `platformdirs` → `%LOCALAPPDATA%\receipt-board\` (override per
  `RECEIPT_BOARD_HOME`) mit DB (`receipt_board.sqlite`), `config.toml`
  (`[server].port` — `0` = ephemer; optional `[database].path` — `TOML`), `runtime.json`.
- **First-Run (`receipt_board.bootstrap`):** Ordner + Default-`config.toml` anlegen, DB via
  `Alembic` auf `head` (seedet Vokabular), idempotentes Re-Seed, Session-Token erzeugen,
  GUI starten. **Entry-Points:** `receipt-board-app` / `python -m receipt_board`;
  `--check` führt nur den First-Run aus (ohne Fenster).

---

## 12. Tests (I3)

- `pytest` + `pytest-cov`; Layout `tests/{unit,integration}`.
- **Unit:** Services, Cascade (Invariante/Edge-Cases), Importer (Parse/Typisierung/Atomarität).
- **Integration:** REST via `FastAPI` `TestClient` (public + privileged inkl. Token-Gate),
  CLI gegen Test-Server.
- **Fixtures:** Temp-`SQLite` (oder In-Memory); die echte `Expenses Checklist 2024_v02.md`
  als Importer-Fixture.
- **Gate:** Coverage ≥ `90 %` in **GitHub Actions** (PR-blocking).

---

## 13. Task-Breakdown

> Als GitHub Issues (Milestone `v1`) angelegt — siehe [`TASKS.md`](./TASKS.md) für die
> Issue-Verweise und die empfohlene Reihenfolge. Reihenfolge ~ Abhängigkeiten:

1. **Projekt-Bootstrap** — `uv`, `ruff`, `pytest`, `pyproject.toml`, Repo-Layout, CI-Skelett.
2. **Persistenz** — SQLAlchemy-Modelle, `Alembic`-Init + erste Migration, Pragmas, Vocab-Seeds.
3. **Core/Services** — Aggregat-Ops, Cascade, Fehler-Typen, Audit (mit Tests).
4. **Importer** — Markdown-Parser, Typisierung, atomare Validierung + Report (mit Tests).
5. **REST-API** — Router public/privileged, Pydantic-Schemas, Token-Gate, `runtime.json`.
6. **CLI** — HTTP-Client-Befehle, `--json`, Exit-Codes.
7. **GUI** — `esbuild`-Setup, Baum/Inline-Edit/DnD, Vokabular-Screen, Suche, Bestätigungen,
   Token-Injektion, Refresh.
8. **Packaging** — `PyInstaller`-Spec, First-Run/Config, Icon.
9. **CI/Coverage-Gate** — GitHub Actions, ≥ `90 %`.
10. **Doku** — README/Run-Doku; Brief/Glossar/ADRs final abgleichen.
