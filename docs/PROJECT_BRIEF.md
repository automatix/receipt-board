# Receipt Board — Projekt-Brief (`v1`)

> Dieser Brief beleuchtet das Vorhaben aus verschiedenen Blickwinkeln (Idee, Architektur,
> Funktionalität, nicht-funktionale Anforderungen). Er wurde nach der
> **Domain-Modeling-Grilling-Session** mit den dort getroffenen Entscheidungen in Einklang
> gebracht.
>
> **Maßgebliche Quellen für Details:** das Glossar ([`GLOSSARY.md`](./GLOSSARY.md)) und die
> Architecture Decision Records ([`adr/`](./adr/README.md)). Bei Widersprüchen gewinnen
> Glossar + ADRs; dieser Brief ist die zusammenfassende Übersicht.
>
> Sprache: Deutsch (Domäne + Kommunikation); technische Identifier (`Feldnamen`,
> `Tabellen`, Tooling) sind Englisch und ge-backtickt.

---

## 1. Idee & Kontext

Beim Vorbereiten eines **Jahres- oder Monatsabschlusses** arbeitet der Nutzer eine
**Ausgaben-Checkliste** ab: Pro Ausgabenkategorie werden die noch fehlenden Belege
zusammengesucht, korrekt benannt und über die Dropbox an die Buchhalterin übergeben.

Heute liegt diese Checkliste als verschachtelte Markdown-Datei vor
(`local/Expenses Checklist 2024_v02.md`). Jeder abzuarbeitende Eintrag trägt in einer
informellen Klammer-Notation, wo und wie der Beleg zu beschaffen ist. Nur zwei Einträge
(`1&1`, `sim.de`) sind vollständig nach dieser Notation ausgefüllt; der Rest ist
unvollständig oder bewusst manuell.

**Ziel von Receipt Board:**

1. Die **Handhabung der Checkliste** vereinfachen und integrierbar machen — strukturierte
   Datenhaltung statt loser Markdown-Datei, mit komfortabler Bearbeitung und einer
   programmatischen Schnittstelle.
2. Den Abarbeitungs-Prozess **schrittweise automatisierbar** machen — wobei `v1` bewusst
   nur die strukturierte Basis + Schnittstelle liefert (siehe Scope).

---

## 2. Scope (`v1`) — Ziele & Nicht-Ziele

### In Scope (`v1`)

- Strukturierte Datenhaltung der `Checklist`(s) in `SQLite`.
- Desktop-GUI (`HTML`/`CSS`/`JS`), die die hierarchische Struktur beibehält.
- Programmatische Schnittstelle (`REST` + `CLI`) für **Lesen** + **Blatt-`done`-Toggling**.
- Mehrere `Checklist`s; neue per **Leer-Anlegen**, **Import** oder **Klonen**.
- Initialer, atomarer Import aus dem bestehenden Markdown-Format.
- **Audit-Log** für sämtliche schreibenden Aktionen.
- App-weite, GUI-verwaltete **Controlled Vocabularies** (`Tool`, `Resource Type`).
- Installierbar als ausführbare Datei; `config` + DB im User-Verzeichnis.

### Nicht in Scope (`v1`) — spätere Iterationen

- **Beleg-Beschaffung / Automatisierung** (Links öffnen, Tools auslösen, Downloads).
- **Datei-Handling** der eigentlichen Beleg-Dateien (PDFs) und Dropbox-Übergabe.
- Modellierung von `Receipt`/Beleg als Entität (siehe [`ADR-0001`](./adr/0001-receipt-not-modeled-in-v1.md)).
- Mehrbenutzer-Betrieb, Synchronisierung, Cloud.

---

## 3. Domänenmodell & Datenstruktur

> Kanonische Begriffe siehe [`GLOSSARY.md`](./GLOSSARY.md).

### Hierarchie

Eine **`Checklist`** ist ein Baum aus **`Node`s** beliebiger Tiefe. Jeder `Node` hat einen
**expliziten Typ** ([`ADR-0006`](./adr/0006-node-type-is-explicit-inferred-only-at-import.md)):

- **`Category`**: Gliederungsknoten; trägt `name` und eine eigene `done`-Checkbox; darf
  **gemischt** Unterkategorien *und* Items enthalten; ist inhaltlich nicht editierbar
  (keine Action-Felder); darf leer sein.
- **`Expense Item`**: das abzuarbeitende Blatt (z. B. `Amazon`, `1&1`, `Betreuungskosten`);
  trägt die Action-Felder; hat **nie** Kinder; liegt **immer unter einer `Category`**
  ([`ADR-0007`](./adr/0007-checklist-aggregate-with-separate-category-and-item-tables.md)).

Der Typ ist **nicht** aus der Kinderzahl abgeleitet — nur der **Import** leitet ihn
strukturell ab (Blätter → `Expense Item`, Vorfahren → `Category`) und speichert ihn dann
explizit.

### Felder

Jeder `Node` trägt: eine `id` (pro Tabelle eindeutige Integer — [`ADR-0010`](./adr/0010-integer-primary-keys-instead-of-uuids.md); Referenzen tragen daher zusätzlich `kind`),
`name` (nicht eindeutig), `position` (bedeutsame Reihenfolge, darf Kategorien und Items mischen) und `done`.

**`done`** sitzt auf **jedem** `Node` ([`ADR-0002`](./adr/0002-done-stored-on-every-node-with-symmetric-cascade.md)).
Das Tool ist **semantik-agnostisch** — es kennt nur Häkchen; die Bedeutung („Beleg
beschafft") lebt außerhalb.

Action-Felder (**nur** auf `Expense Item`):

| Feld           | Typ                                                        |
| -------------- | --------------------------------------------------------- |
| `resources`    | Liste typisierter **`Resource`** (`type` ∈ Vocab, optionaler `value`) |
| `tools`        | Liste von **`Tool`** (aus Vocab); **kein** Default        |
| `data`         | Freitext                                                  |
| `instructions` | Freitext                                                  |

- **`Resource`**: `type` aus dem Vocab `Resource Type` (aktuell `URL`, `Email`) plus
  **optionalem** `value` (konkrete URL bzw. Postfach; ein `Email` ohne `value` heißt „schau
  in deine Mails").
- **`Tool`**: aus dem Vocab `Tool` (aktuell `Browser`, `Thunderbird`).

### Cascade ([`ADR-0002`](./adr/0002-done-stored-on-every-node-with-symmetric-cascade.md))

Symmetrisch, mit Invariante **`Category.done ⇔ ganzer Teilbaum done`**:

- `Node` auf `true`/`false` → **alle Nachkommen** auf denselben Wert.
- Nach jeder Kind-Änderung → Vorfahren neu aufrollen (`Vorfahr.done = UND(direkte Kinder)`).
- Das Tool führt die Cascade **stur** aus; der Schutz vor versehentlichem destruktivem
  Kategorie-Abwählen ist ein **GUI**-Anliegen (Bestätigung/Undo).
- Kein Fortschrittsbalken in `v1`.

### Mehrere `Checklist`s

- `Checklist`s sind **voneinander unabhängig** (eigene Struktur, eigene `done`-Stände).
- Drei Erstellungspfade (alle **GUI-only**): **Leer-Anlegen**, **Import**, **Klonen**
  (Deep-Copy der Struktur + Felder, neue IDs, alle `done = false`).
- `Period` (Jahr/Monat) ist in `v1` **kein** strukturiertes Attribut, sondern nur Teil des
  freien `name` (z. B. `Expenses 2024`).

---

## 4. Funktionalität

### 4.1 GUI (`HTML`/`CSS`/`JS`)

- Stellt den hierarchischen Baum dar (eingerückt / aufklappbar).
- **Volle** Bearbeitung: Items/Kategorien hinzufügen, umbenennen, Action-Felder editieren,
  **umsortieren** und **verschieben/re-parenting** (`position` bedeutsam), **entfernen**.
- `done` setzen auf jeder Ebene (Kategorie-Toggle löst Cascade aus).
- Verwaltung der **Controlled Vocabularies** (`Tool`, `Resource Type`): hinzufügen,
  umbenennen; entfernen nur, wenn ungenutzt ([`ADR-0005`](./adr/0005-import-is-atomic-and-validates-controlled-vocabularies.md)).
- Auswahl der aktiven `Checklist`; Freitextsuche; JSON-Export anstoßbar.
- Die GUI ist die **einzige** Oberfläche für privilegierte Operationen
  ([`Privileged Operation`](./GLOSSARY.md)).

### 4.2 Programmatische Schnittstelle (`REST` + `CLI`) & Berechtigungen

Dieselbe Domänenlogik über eine lokale `REST`-API und ein `CLI`. Die externe Schnittstelle
ist bewusst **stark eingeschränkt** ([`ADR-0003`](./adr/0003-external-interface-toggles-leaf-checkboxes-only.md)):

| Operation                                       | GUI | `REST`/`CLI` (extern, inkl. KI) |
| ----------------------------------------------- | :-: | :-----------------------------: |
| Alles als `JSON` exportieren                    | ✅  | ✅ (lesen)                      |
| Suchen (Freitext über `name`, alle Ebenen)      | ✅  | ✅ (lesen)                      |
| Lesen                                           | ✅  | ✅ (lesen)                      |
| **`done` eines `Expense Item`** setzen/zurück   | ✅  | ✅ (einzige Schreib-Operation)  |
| `done` einer `Category` setzen                  | ✅  | ❌ (nur indirekt via Roll-up)   |
| Item/Kategorie hinzufügen / editieren / entfernen | ✅ | ❌                              |
| `Checklist` leer anlegen / importieren / klonen / löschen | ✅ | ❌                       |
| Vokabular-Pflege                                | ✅  | ❌                              |

> Technisch erzwungen über ein **GUI-Session-Token**
> ([`ADR-0009`](./adr/0009-gui-only-operations-protected-by-startup-session-token.md)): privilegierte
> Endpunkte verlangen das Token, das nur in die GUI-Seite injiziert wird.

### 4.3 Suche & 4.4 Export ([`GLOSSARY.md`](./GLOSSARY.md))

- **Suche**: Freitext über `name` **aller Ebenen**; liefert eine **flache** Trefferliste
  (je Treffer `id`, `name`, Node-Typ, `Checklist`-`id`, Vorfahren-Pfad).
- **Export**: **vollständiger, verschachtelter** JSON-Baum einer `Checklist` (alle Felder).

### 4.5 Audit-Log ([`ADR-0004`](./adr/0004-audit-logs-one-entry-per-action-with-affected-ids.md))

- **Ein** Eintrag pro Aufrufer-Aktion: Zeitstempel, Herkunft (`GUI`/`CLI`/`REST`),
  Aktionstyp, Ziel-`id`, alt → neu — **plus** die IDs aller per Cascade betroffenen Nodes.

### 4.6 Initialer Import (Strikt + Atomar)

Quelle ist das Markdown-Format (verschachtelte `- [ ]`-Checklisten). **Strikt nach
Klammer-Typ** (keine Heuristik), **atomar / all-or-nothing**
([`ADR-0005`](./adr/0005-import-is-atomic-and-validates-controlled-vocabularies.md)):

| Klammer  | Zielfeld       | Beispiel                          |
| -------- | -------------- | --------------------------------- |
| `(...)`  | `resources`    | `(https://… \| Email)`            |
| `{...}`  | `tools`        | `{Browser \| Thunderbird}`        |
| `[...]`  | `data`         | `[Login 588791127]`               |
| `<...>`  | `instructions` | `<öffne den Link …>`              |

- `name` = Text **vor** der ersten Klammergruppe; Mehrfachwerte durch `|` getrennt.
- `resources`/`tools` werden **typisiert**; `data`/`instructions` bleiben Freitext.
- Eine URL fälschlich in `[...]` landet **in `data`** (keine Umdeutung).
- `done` wird aus dem Markdown übernommen (`[x]`→`true`); in der Quelle alles `false`.
- **Nicht typisierbare Tokens** (z. B. unbekanntes `Tool`) → Import schreibt **nichts**,
  bricht ab und meldet die ungültigen Werte präzise — mit Empfehlung, das Vokabular ggf.
  über die GUI zu erweitern.
- Referenz-Beispiele aus der Quelle: `1&1`, `sim.de`.

---

## 5. Architektur

```
┌────────────────────────────────────────────────────────────┐
│  Native Fenster (pywebview)                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  GUI: HTML / CSS / JS  (REST-Client, hält Session-Token)│  │
│  └───────────────┬──────────────────────────────────────┘   │
└──────────────────┼──────────────────────────────────────────┘
                   │ HTTP (127.0.0.1, loopback)
┌──────────────────▼──────────────────────────────────────────┐
│  FastAPI (lokaler Server)                                    │
│   • Public: Lesen + Expense-Item-done-Toggle (tokenfrei)     │
│   • Privileged: Struktur/Edit/Import/Klon/Löschen/Vocab      │
│     (Token erforderlich)                                     │
│   ├─ Core / Service-Layer  ◄────────── CLI (dünner Wrapper)  │
│   │    (Domänenlogik, Cascade, Validierung, Audit)           │
│   └─ Repository  ──►  SQLite (WAL)                           │
└──────────────────────────────────────────────────────────────┘
```

- **Stack**: `Python` (Backend), `SQLite` (DB), `HTML`/`CSS`/`JS` (GUI).
- **GUI-Anbindung**: Lokaler `FastAPI`-Server (`REST`); GUI als `REST`-Client im
  `pywebview`-Fenster, hält das GUI-Session-Token.
- **CLI**: dünner Wrapper über denselben **Core/Service-Layer**; extern nur Lesen +
  Blatt-`done`-Toggle.
- **Aggregat & Persistenz** ([`ADR-0007`](./adr/0007-checklist-aggregate-with-separate-category-and-item-tables.md)):
  `Checklist` ist Aggregate Root & Invarianten-Grenze. Persistenz = flache Adjazenzliste,
  Schreibvorgänge = gezielte, transaktionale Mutationen (betroffene Zeilen + Cascade + ein
  Audit-Eintrag in **einer** Transaktion). **Zwei Tabellen**: `categories` (Kategorienbaum,
  self-ref `parent_id`) und `expense_items` (Verweis `category_id NOT NULL`); mehrwertige
  Felder (`resources`, `tools`) in eigenen Kindtabellen.
- **Concurrency** ([`ADR-0008`](./adr/0008-concurrency-one-transaction-per-action-last-write-wins.md)):
  eine `SQLite`-Transaktion pro Aktion (WAL), **last-write-wins**, kein App-Lock; die GUI
  aktualisiert nach jeder Aktion.
- **Schichten**: `GUI` → `REST`/`CLI` → `Core/Service` → `Repository` → `SQLite`.

---

## 6. Nicht-funktionale Anforderungen

- **Testabdeckung**: Unit-Tests mit **≥ `90 %`** Coverage.
- **Ein Nutzer**, lokaler Betrieb; GUI + CLI/KI können parallel schreiben.
- **Sicherheit**: `FastAPI` nur auf `127.0.0.1`; privilegierte Operationen per Token
  geschützt.
- **Nachvollziehbarkeit**: vollständiges Audit-Log aller Schreibvorgänge.
- **Datenintegrität**: strikter, atomarer Import; Cascade-Invariante; referentielle
  Integrität der Vokabulare; Validierung im Service-Layer; alles transaktional.
- **Portabilität**: Fokus `Windows` (`v1`); Architektur soll spätere Cross-Plattform nicht
  verbauen.
- **Wartbarkeit**: klare Schichtentrennung, Domänenlogik unabhängig von GUI/Transport.

---

## 7. Persistenz & Installation

- **Packaging**: `PyInstaller` → ausführbare `.exe` (Windows-Fokus).
- **Speicherorte** (Vorschlag, via `platformdirs`):
  - `config` + `SQLite`-DB unter `%LOCALAPPDATA%\receipt-board\`.
  - Programm/Executable z. B. unter `%LOCALAPPDATA%\Programs\receipt-board\`.
- DB-/Config-Pfad konfigurierbar; saubere Erst-Initialisierung bei leerer DB.

---

## 8. Offene Annahmen (für die technische Session)

- `Python` `3.12+`; Tests mit `pytest` + `pytest-cov`.
- `FastAPI` auf Loopback mit festem oder ephemerem Port; `pywebview` lädt diese URL.
- Konkretes Schema der zwei Tabellen + Kindtabellen (`item_resources`, `item_tools`),
  Audit-Tabelle, Vokabular-Tabellen.
- Genauer `REST`-Vertrag (Endpunkte, Fehlerformate, Token-Übertragung).
- Detaillierte Import-Typisierungsregeln (URL-Erkennung, `Email`-`value`-Parsing).
- Pfade/Speicherorte via `platformdirs` statt hartkodiert.

---

## 9. Entscheidungs-Log

| Thema                       | Entscheidung                                                              | Ref |
| --------------------------- | ------------------------------------------------------------------------ | --- |
| GUI ↔ Backend               | `FastAPI` (lokal, `REST`) + `pywebview`; GUI ist `REST`-Client            | —   |
| Programmatische Surface     | `REST` + `CLI`                                                            | —   |
| Packaging                   | `PyInstaller` (Windows-`.exe`)                                            | —   |
| Scope `v1`                  | Nur Store + Schnittstelle; `Receipt` nicht modelliert                     | `ADR-0001` |
| Top-Konstrukt               | **`Checklist`** (vermeide `List`, `Board`)                                | —   |
| `Checklist`-Erstellung      | Leer / Import / Klon — alle GUI-only                                      | —   |
| Blatt-Begriff               | **`Expense Item`**                                                        | `ADR-0001` |
| `done`                      | Auf **jedem** Node; semantik-agnostisch; symmetrische Cascade            | `ADR-0002` |
| Externer Schreib-Scope      | **Nur** `Expense-Item`-`done`-Toggle + Lesen; Rest GUI-only              | `ADR-0003` |
| Adressierung                | Pro-Tabelle Integer-`id` + `kind` (supersedes UUID)                      | `ADR-0010` |
| Action-Felder               | Typisiert: `Resource{type,value?}`, `Tool`; `data`/`instructions` Freitext; nur auf Items; **kein** `tools`-Default | — |
| Vokabulare                  | App-weit, GUI-verwaltet; Rename per id, Remove nur ungenutzt              | `ADR-0005` |
| Import                      | Strikt nach Klammer-Typ; **atomar**; Vocab-Validierung                   | `ADR-0005` |
| Struktur-Edit (GUI)         | Voll inkl. Umsortieren/Re-Parenting; `position` bedeutsam                 | —   |
| Audit-Log                   | Ein Eintrag/Aktion + betroffene IDs                                       | `ADR-0004` |
| Node-Typ                    | **Explizit**; beim Import strukturell abgeleitet                         | `ADR-0006` |
| Aggregat/Persistenz         | `Checklist`-Aggregat; gezielte Mutationen; **zwei Tabellen**             | `ADR-0007` |
| Concurrency                 | Eine Transaktion/Aktion (WAL); last-write-wins                           | `ADR-0008` |
| Privilegien-Schutz          | GUI-Session-Token; Public = Lesen + Item-Toggle                         | `ADR-0009` |
| `Period`                    | Nur über den `name` (kein strukturiertes Attribut)                       | —   |
| Testabdeckung               | ≥ `90 %`                                                                  | —   |

---

## 10. Nächste Schritte

1. **Technische Session**: detaillierte technische Beschreibung (konkretes DB-Schema,
   `REST`-Vertrag, GUI-Konzept, Import-Spezifikation, Build/Packaging) — auf Basis von
   diesem Brief + Glossar + ADRs.
2. Aus der technischen Beschreibung **Tasks** ableiten.
3. Implementierung gemäß Branching-/Ticket-Workflow.
