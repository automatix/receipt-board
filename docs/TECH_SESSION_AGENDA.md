# Technische Session — Fragenkatalog

> **So beantwortest du:** Schreibe deine Antwort hinter `**Antwort:**`. **Leer lassen
> (oder „Empfehlung")** = meine Empfehlung wird übernommen. Du kannst auch nur Teile
> kommentieren/abweichen. Antworte gern **en bloc**; ich verdaue anschließend die komplette
> Datei und erzeuge daraus `docs/TECH_SPEC.md`, ggf. neue ADRs und eine Task-Liste.
>
> Basis: [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md), [`GLOSSARY.md`](./GLOSSARY.md),
> [`adr/`](./adr/README.md). Adaptiv — einzelne Punkte können sich beim Verdauen
> verzweigen.

---

## A — Projekt-Setup & Tooling

### A1 — Dependency-Management
**Empfehlung:** `uv` (schnell, Lockfile, modern).
**Antwort:**

### A2 — Lint / Format / Types
**Empfehlung:** `ruff` (Lint + Format) + `mypy` (strict) + `pre-commit`-Hooks.
**Antwort:**

### A3 — Repo-Layout
**Empfehlung:** `src/receipt_board/` mit Subpackages `core` (Domäne + Services),
`persistence` (Repository, Schema, Migrations), `api` (FastAPI), `cli`, `importer`,
`gui` (statische Assets); dazu `tests/`.
**Antwort:**

### A4 — Python-Version
**Empfehlung:** `3.12+` als Mindestversion.
**Antwort:**

---

## B — DB-Schema

### B1 — Tabellen & Spalten
**Empfehlung:** `checklists`, `categories` (self-ref `parent_id`), `expense_items`
(`category_id NOT NULL`), `item_resources`, `item_tools`, `resource_types`, `tools`,
`audit_log` — Spalten gemäß Brief/ADR-0007; je Tabelle `created_at`/`updated_at`.
**Antwort:**

### B2 — `position`-Schema (Interleaving Kategorien + Items)
**Empfehlung:** Ein gemeinsamer Integer-`position` je Elternknoten über **beide** Tabellen
hinweg; Anzeige = nach `position` gemischte Kinder. Umsortieren schreibt die betroffenen
Geschwister neu (contiguous ints). (Alternative: fraktionale Positionen.)
**Antwort:**

### B3 — IDs & FK-Verhalten
**Empfehlung:** `uuid4` als `TEXT`-PK; FK-Constraints aktiv; `ON DELETE CASCADE` für
Eltern→Kinder und `Checklist`→alles; Vokabular-FKs `ON DELETE RESTRICT` (deckt „Remove nur
ungenutzt").
**Antwort:**

### B4 — Indizes & SQLite-Pragmas
**Empfehlung:** Indizes auf FKs (`checklist_id`, `parent_id`, `category_id`, `item_id`) und
auf `name` (Suche); `WAL`, `foreign_keys=ON`, `busy_timeout=5000`.
**Antwort:**

### B5 — Migrations
**Empfehlung:** `Alembic` (robuste Schema-Versionierung über App-Releases hinweg).
**Antwort:**

---

## C — Domänen-/Service-Layer

### C1 — Aggregat-Operationen (Signaturen)
**Empfehlung:** `ChecklistService` (`toggle_item_done`, `add_category`, `add_item`,
`edit_node`, `remove_node`, `move_node`, `clone_checklist`, `create_blank`, `delete_checklist`),
`VocabularyService` (`add`/`rename`/`remove` mit In-Use-Check), `ImportService`,
`AuditService`. Jede schreibende Op transaktional + Audit.
**Antwort:**

### C2 — Cascade-Umsetzung
**Empfehlung:** App-seitige Traversierung im Service (klar testbar; Datenmenge klein),
gebündelte `UPDATE`s in **einer** Transaktion; rekursive SQL-CTE nur für Lese-/Roll-up-Abfragen.
**Antwort:**

### C3 — Fehlertypen
**Empfehlung:** Domänen-Exceptions (`NotFoundError`, `ValidationError`,
`VocabularyInUseError`, `InvalidImportError`), zentral auf REST-/CLI-Fehler gemappt.
**Antwort:**

---

## D — Import-Spezifikation

### D1 — Markdown-Grammatik
**Empfehlung:** Einrückung bestimmt Hierarchie (Tab/Spaces normalisiert, Einheit
auto-erkannt); jede `- [ ]`/`- [x]`-Zeile = Node; Typ aus Verschachtelung; `name` getrimmt.
**Antwort:**

### D2 — Typisierungsregeln
**Empfehlung:** resource-Token = `URL`, wenn `^https?://`; Literal `Email`
(case-insensitive) → Typ `Email`, optionaler `value` = Rest nach „Email"; tool-Token
case-insensitive gegen das `tools`-Vokabular gematcht.
**Antwort:**

### D3 — Atomarität & Fehlerreport
**Empfehlung:** Zwei-Phasen: erst komplett parsen + validieren (**alle** Fehler mit
Zeilennummer + Token + betroffenem Vokabular sammeln); bei Fehlern Abbruch ohne Schreiben;
sonst Insert in **einer** Transaktion.
**Antwort:**

---

## E — REST-Vertrag

### E1 — Endpunktliste (Public vs. Privileged)
**Empfehlung:** Public: `GET /checklists`, `GET /checklists/{id}` (nested),
`GET /search?q=`, `POST /items/{id}/done`. Privileged: CRUD auf
`checklists`/`categories`/`items`, `move`, `import`, `clone`, Vokabular-CRUD.
**Antwort:**

### E2 — Schemas & Fehlerformat
**Empfehlung:** `Pydantic`-Modelle; Fehler `{error:{code,message,details}}`; `OpenAPI`
automatisch.
**Antwort:**

### E3 — Token, Bind & Port-Discovery
**Empfehlung:** Header `X-Session-Token`; Bind nur `127.0.0.1`; ephemerer Port beim Start,
in `%APPDATA%\ReceiptBoard\runtime.json` (**nur Port**, kein Token) für HTTP-Clients
geschrieben.
**Antwort:**

---

## F — CLI

### F1 — Befehle & Output
**Empfehlung:** `receipt-board export [--checklist ID]`, `search QUERY`, `item done ID`,
`item undone ID`; `--json` als Standardausgabe.
**Antwort:**

### F2 — Anbindung & Exit-Codes
**Empfehlung:** CLI nutzt den **In-Process-Core** direkt auf der `SQLite`-DB (kein laufender
Server nötig; WAL deckt Parallelität mit der GUI ab); nur Public-Operationen; Exit-Code `0`
ok, `≠0` bei Fehler. (Die REST-API bleibt für GUI + HTTP/KI-Clients.)
**Antwort:**

---

## G — GUI

### G1 — Tech innerhalb HTML/CSS/JS
**Empfehlung:** Vanilla `JS` (ES-Module), **kein** Build-Step (einfachstes Bundling in
`PyInstaller`); kleine Helfer nur bei Bedarf.
**Antwort:**

### G2 — Baum, Inline-Edit, Drag&Drop
**Empfehlung:** Verschachtelte Listen; Inline-Editing; natives HTML5-Drag&Drop für
Umsortieren/Re-Parenting.
**Antwort:**

### G3 — Destruktive Bestätigungen / Undo
**Empfehlung:** Bestätigungsdialoge für Kategorie-Abwählen (mit Anzahl betroffener Items),
Remove und Checklist-Löschen; **Undo** auf später vertagt (Audit-Log deckt
Nachvollziehbarkeit).
**Antwort:**

### G4 — Vokabular-Screen, Suche, Token-Injektion, Refresh
**Empfehlung:** Settings-Screen fürs Vokabular; Such-Box; Token beim Laden via `pywebview`
injiziert; Refresh = aktive `Checklist` nach jeder mutierenden Aktion neu laden + manueller
Refresh-Button (kein Live-Polling in `v1`).
**Antwort:**

---

## H — Audit & Concurrency

### H1 — `audit_log`-Schema
**Empfehlung:** `id`, `ts`, `origin` (`GUI`/`CLI`/`REST`), `action_type`, `target_kind`,
`target_id`, `checklist_id`, `payload` (`old`/`new` als `JSON`), `affected_ids` (`JSON`).
**Antwort:**

### H2 — Sammeln der `affected_ids`
**Empfehlung:** Die Cascade-Routine liefert die Menge geänderter Node-IDs zurück; **ein**
Audit-Eintrag in derselben Transaktion.
**Antwort:**

### H3 — GUI-Refresh bei parallelen Änderungen
**Empfehlung:** In `v1` manuelles/aktionsbezogenes Reload + Refresh-Button; kein
WebSocket/Polling (optional später).
**Antwort:**

---

## I — Packaging, Config & Tests

### I1 — PyInstaller
**Empfehlung:** `onedir` + `--windowed` (kein Konsolenfenster), App-Icon; GUI-Assets via
`--add-data` bündeln.
**Antwort:**

### I2 — First-Run, Config & Pfade
**Empfehlung:** Bei Erststart `%APPDATA%\ReceiptBoard\` anlegen, DB per Migrations auf
`head`; Config `config.toml` (Port-Override, DB-Pfad) via `platformdirs`.
**Antwort:**

### I3 — Test-Strategie (≥ 90 %)
**Empfehlung:** `pytest` + `pytest-cov`; Unit (Services, Importer, Cascade), Integration
(`FastAPI` `TestClient`, CLI), Temp-/In-Memory-`SQLite`-Fixtures, echte Markdown-Quelle als
Importer-Fixture, Coverage-Gate ≥ `90 %` in CI (GitHub Actions).
**Antwort:**

---

## J — Sonstiges / dein Input

> Platz für Themen, die ich übersehen habe oder die dir wichtig sind (z. B. Logging,
> i18n, Backup/Export der DB, GitHub-Actions-CI, Release-Artefakte).

**Antwort:**
