# Technische Session — Fragenkatalog

> **So beantwortest du:** Schick mir eine **Map `Frage:Option`**, z. B.
> `A1:1, A2:1, B2:2, F2:2 …`. **Nicht genannt = Option `1` (Empfehlung).** Freitext nur zu
> den wenigen Fragen, die wirklich einen Kommentar brauchen (z. B. `B2:2 (sparse steps 100)`).
> Block **J** ist Freitext.
>
> Ich verdaue anschließend die komplette Antwort, prüfe Querbezüge/Widersprüche und erzeuge
> daraus `docs/TECH_SPEC.md`, ggf. neue ADRs und eine Task-Liste.
>
> Basis: [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md), [`GLOSSARY.md`](./GLOSSARY.md),
> [`adr/`](./adr/README.md). Option `1` ist jeweils meine Empfehlung und mit den bisherigen
> ADRs konsistent.

---

## A — Projekt-Setup & Tooling

### A1 — Dependency-Management
1. **(Empfehlung)** `uv` — schnell, Lockfile, modern
2. `poetry`
3. `pip` + `requirements.txt` (+ `pip-tools`)

### A2 — Lint / Format / Types
1. **(Empfehlung)** `ruff` (Lint+Format) + `mypy` (strict) + `pre-commit`
2. `ruff` allein (Lint+Format, kein `mypy`)
3. `black` + `flake8` + `mypy`

### A3 — Repo-Layout
1. **(Empfehlung)** `src/receipt_board/` mit `core`/`persistence`/`api`/`cli`/`importer`/`gui` + `tests/`
2. Flaches `receipt_board/`-Package (ohne `src/`-Layout)
3. Mehrere Top-Level-Packages (z. B. `backend`/`frontend` getrennt)

### A4 — Python-Version (Mindestversion)
1. **(Empfehlung)** `3.12+`
2. `3.11+`
3. `3.13+`

---

## B — DB-Schema

### B1 — Tabellen & Spalten
1. **(Empfehlung)** Schema gemäß ADR-0007: `checklists`, `categories`, `expense_items`, `item_resources`, `item_tools`, `resource_types`, `tools`, `audit_log`
2. Wie 1, aber Vokabular in **einer** Tabelle `vocabulary(kind, value)` zusammengefasst
3. Freitext-Variante

### B2 — `position`-Schema (Interleaving Kategorien + Items)
1. **(Empfehlung)** Gemeinsamer Integer-`position` je Elternknoten über beide Tabellen; contiguous, Umsortieren schreibt betroffene Geschwister neu
2. Gemeinsamer Integer mit **Lücken** (Schritte z. B. 100), weniger Rewrites
3. **Fraktionale** Positionen (LexoRank-artig), keine Rewrites

### B3 — IDs & FK-Verhalten
1. **(Empfehlung)** `uuid4` als `TEXT`-PK; FKs aktiv; Eltern/`Checklist` `ON DELETE CASCADE`; Vokabular `ON DELETE RESTRICT`
2. Integer-`AUTOINCREMENT`-PKs (pro Tabelle) statt UUID
3. `uuid4`, aber Löschkaskaden in der App statt DB-seitig

### B4 — Indizes & SQLite-Pragmas
1. **(Empfehlung)** FK-Indizes + `name`-Index (`LIKE`-Suche); `WAL`, `foreign_keys=ON`, `busy_timeout=5000`
2. Wie 1, zusätzlich **FTS5**-Virtualtabelle für die Suche
3. Minimal (nur PKs), Indizes später

### B5 — Migrations
1. **(Empfehlung)** `Alembic`
2. Handgerollte SQL-Migrationsskripte + Versionstabelle
3. Keine Migrations in `v1` (Schema ad hoc)

---

## C — Domänen-/Service-Layer

### C1 — Aggregat-Operationen
1. **(Empfehlung)** `ChecklistService` + `VocabularyService` + `ImportService` + `AuditService` (jede Schreib-Op transaktional + Audit)
2. Eine einzige Fassaden-Service-Klasse
3. Freitext-Variante

### C2 — Cascade-Umsetzung
1. **(Empfehlung)** App-seitige Traversierung für Writes, SQL-CTE für Lese-/Roll-up-Abfragen
2. Reine rekursive SQL-CTE für beides
3. Rein app-seitig (Teilbaum laden, mutieren, speichern)

### C3 — Fehlertypen
1. **(Empfehlung)** Domänen-Exceptions, zentral auf REST/CLI gemappt
2. Result/Either-Rückgabetypen (keine Exceptions)
3. HTTP-artige Fehlercodes durchgängig

---

## D — Import-Spezifikation

### D1 — Markdown-Grammatik
1. **(Empfehlung)** Einrückungsbasiert, Einheit auto-erkannt, Tabs/Spaces normalisiert
2. Strikt nur 2-Spaces (oder nur Tab); inkonsistente Einrückung wird abgelehnt
3. Freitext-Variante

### D2 — Typisierungsregeln
1. **(Empfehlung)** `URL` via `^https?://`; `Email`-Literal (case-insensitive) + optionaler `value`; `tools` case-insensitive gegen Vokabular
2. Strenger: `URL` muss voll validieren, `Email` muss Postfach haben
3. Freitext-Variante

### D3 — Fehlerreport (Import bleibt atomar, ADR-0005)
1. **(Empfehlung)** **Alle** Fehler sammeln (Zeile + Token + Vokabular), dann abbrechen; sonst Insert in einer Transaktion
2. Fail-fast beim ersten Fehler (weiterhin atomar)
3. Freitext-Variante

---

## E — REST-Vertrag

### E1 — Endpunktstil
1. **(Empfehlung)** Ressourcen-REST: `GET /checklists`, `GET /checklists/{id}` (nested), `GET /search?q=`, `POST /items/{id}/done`; Privileged: CRUD + `move`/`import`/`clone`/Vokabular
2. RPC-Stil: ein Endpunkt mit `action`-Feld
3. Freitext-Variante

### E2 — Schemas & Fehlerformat
1. **(Empfehlung)** `Pydantic`-Modelle; Fehler `{error:{code,message,details}}`; `OpenAPI` automatisch
2. Schlichte Dicts, minimale Validierung
3. Freitext-Variante

### E3 — Token, Bind & Port
1. **(Empfehlung)** Header `X-Session-Token`; Bind `127.0.0.1`; **ephemerer** Port + `runtime.json` (nur Port) zur Discovery
2. **Fester**, konfigurierbarer Port (z. B. `8765`)
3. Freitext-Variante

---

## F — CLI

### F1 — Befehle & Output
1. **(Empfehlung)** `export [--checklist ID]`, `search QUERY`, `item done ID`, `item undone ID`; `--json`
2. Andere Gruppierung (z. B. `done`/`undone` als Top-Level-Befehle)
3. Freitext-Variante

### F2 — Anbindung
1. **(Empfehlung)** In-Process-Core direkt auf `SQLite` (kein laufender Server nötig; WAL deckt Parallelität)
2. CLI spricht **HTTP** gegen den laufenden Server (braucht Server + `runtime.json`)
3. Freitext-Variante

---

## G — GUI

### G1 — Tech innerhalb HTML/CSS/JS
1. **(Empfehlung)** Vanilla `JS` (ES-Module), **kein** Build-Step
2. Kleines No-Build-Framework via CDN/ESM (z. B. `Preact`/`Vue`)
3. Volles Framework mit Build (z. B. `Vite` + `Vue`/`React`)

### G2 — Baum, Inline-Edit, Drag&Drop
1. **(Empfehlung)** Verschachtelte Listen, Inline-Edit, natives HTML5-Drag&Drop
2. Tree-Komponenten-Library
3. Kein Drag&Drop (Umsortieren/Verschieben per Buttons/Menü)

### G3 — Destruktive Bestätigungen / Undo
1. **(Empfehlung)** Bestätigungsdialoge (Kategorie-Abwählen mit Anzahl, Remove, Checklist-Löschen); Undo später
2. Bestätigungsdialoge **+ Undo** in `v1`
3. Keine Bestätigungen (nur Audit-Log)

### G4 — Vokabular-Screen, Suche, Token, Refresh
1. **(Empfehlung)** Settings-Screen fürs Vokabular; Such-Box; Token beim Laden injiziert; Reload nach jeder Aktion + Refresh-Button
2. Wie 1, zusätzlich Live-Polling externer Änderungen
3. Freitext-Variante

---

## H — Audit & Concurrency

### H1 — `audit_log`-Schema
1. **(Empfehlung)** `id`, `ts`, `origin`, `action_type`, `target_kind`, `target_id`, `checklist_id`, `payload`(`old`/`new` JSON), `affected_ids`(JSON)
2. Wie 1 + zusätzliche Metadaten (z. B. App-Version, Session-id)
3. Minimal (`ts`, `action`, `target`)

### H2 — Sammeln der `affected_ids`
1. **(Empfehlung)** Cascade-Routine liefert die geänderten IDs; **ein** Audit-Eintrag in derselben Transaktion
2. `affected_ids` separat nachträglich ermitteln
3. Freitext-Variante

### H3 — GUI-Refresh bei parallelen Änderungen
1. **(Empfehlung)** Manuelles/aktionsbezogenes Reload + Refresh-Button (kein Live-Update in `v1`)
2. Polling alle N Sekunden
3. WebSocket/SSE Live-Updates

---

## I — Packaging, Config & Tests

### I1 — PyInstaller
1. **(Empfehlung)** `onedir` + `--windowed` (kein Konsolenfenster) + Icon + GUI-Assets via `--add-data`
2. `onefile`
3. Freitext-Variante

### I2 — First-Run, Config & Pfade
1. **(Empfehlung)** `%APPDATA%\ReceiptBoard\` bei Erststart; DB per Migrations auf `head`; `config.toml` via `platformdirs`
2. Config als `JSON`/Env statt `TOML`
3. Freitext-Variante

### I3 — Test-Strategie (≥ 90 %)
1. **(Empfehlung)** `pytest` + `pytest-cov`; Unit + Integration (`TestClient`, CLI); Temp-/In-Memory-`SQLite`; echte Markdown-Quelle als Fixture; Coverage-Gate ≥ `90 %` in **GitHub-Actions-CI**
2. Wie 1, aber **ohne** CI-Gate (nur lokal)
3. Freitext-Variante

---

## J — Sonstiges / dein Input (Freitext)

> Themen, die ich übersehen habe oder die dir wichtig sind — z. B. Logging, i18n,
> DB-Backup/Restore, Release-Artefakte/GitHub Releases, Lizenz, Branch-/CI-Setup.

**Antwort:**
