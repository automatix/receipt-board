# Receipt Board — Projekt-Brief (`v1`)

> Dieser Brief ist der **Startschuss** des Projekts. Er beleuchtet das Vorhaben aus
> verschiedenen Blickwinkeln (Idee, Architektur, Funktionalität, nicht-funktionale
> Anforderungen) und bildet die Grundlage für die **nächste Session**, in der wir eine
> detaillierte technische Beschreibung ausarbeiten und daraus Tasks ableiten.
>
> Sprache: Deutsch (Domäne + Kommunikation); technische Identifier (`Feldnamen`,
> `Tabellen`, Tooling) sind Englisch und ge-backtickt — konsistent mit der
> Code-in-English-Regel.

---

## 1. Idee & Kontext

Beim Vorbereiten eines **Jahres- oder Monatsabschlusses** arbeitet der Nutzer eine
**Ausgaben-Checkliste** ab: Pro Ausgabenkategorie werden die noch fehlenden Belege
zusammengesucht, korrekt benannt und über die Dropbox an die Buchhalterin übergeben.

Heute liegt diese Checkliste als verschachtelte Markdown-Datei vor
(`local/Expenses Checklist 2024_v02.md`). Jeder abzuarbeitende Eintrag (das **Blatt**
der Hierarchie) trägt in einer informellen Klammer-Notation, wo und wie der Beleg zu
beschaffen ist. Nur zwei Einträge (`1&1`, `sim.de`) sind vollständig nach dieser
Notation ausgefüllt; der Rest ist unvollständig (Prozess noch „im Kopf") oder bewusst
manuell.

**Ziel von Receipt Board:**

1. Die **Handhabung der Liste** vereinfachen und integrierbar machen — strukturierte
   Datenhaltung statt loser Markdown-Datei, mit komfortabler Bearbeitung und einer
   programmatischen Schnittstelle.
2. Den Abarbeitungs-Prozess **schrittweise automatisierbar** machen — wobei `v1`
   bewusst nur die strukturierte Basis + Schnittstelle liefert (siehe Scope unten).

---

## 2. Scope (`v1`) — Ziele & Nicht-Ziele

### In Scope (`v1`)

- Strukturierte Datenhaltung der Checkliste(n) in `SQLite`.
- Desktop-GUI (`HTML`/`CSS`/`JS`) zur Anzeige und Bearbeitung, die die hierarchische
  Listenstruktur beibehält.
- Programmatische Schnittstelle (`REST` + `CLI`) für Lesen + `done`-Toggling.
- Mehrere Listen verwaltbar; neue Liste per **Import** oder **Klonen**.
- Initialer Import aus dem bestehenden Markdown-Format.
- **Audit-Log** für sämtliche schreibenden Aktionen.
- Installierbar als ausführbare Datei; `config` + DB im User-Verzeichnis.

### Nicht in Scope (`v1`) — spätere Iterationen

- **Beleg-Beschaffung / Automatisierung**: automatisches Öffnen von Links, Auslösen von
  Tools, Herunterladen von Rechnungen.
- **Datei-Handling**: Ablegen, Umbenennen und Übergabe der eigentlichen Beleg-Dateien
  (PDFs) an die Dropbox.
- Mehrbenutzer-Betrieb, Synchronisierung, Cloud.

---

## 3. Domänenmodell & Datenstruktur

### Hierarchie

Eine **Liste** ist ein Baum aus Knoten beliebiger Tiefe:

- **Kategorie-Knoten**: dienen nur der Gliederung, haben Kinder, sind **nicht**
  bearbeitbar (außer Struktur-Operationen in der GUI). Tragen einen `name`.
- **Blatt-Knoten** (unterste Ebene, keine Kinder): die eigentlichen, abzuarbeitenden
  Einträge. Nur diese sind inhaltlich bearbeitbar und tragen die Action-Felder.

Ein Knoten gilt als **Blatt**, wenn er keine Kinder hat — unabhängig davon, ob seine
Action-Felder ausgefüllt sind (manuelle Kategorien wie `Betreuungskosten` sind ebenfalls
Blätter mit leeren Action-Feldern).

### Spalten / Felder eines Blatts

| Feld           | Bedeutung                                    | Default     |
| -------------- | -------------------------------------------- | ----------- |
| `done`         | Checkbox — Beleg beschafft/erledigt          | `false`     |
| `name`         | Bezeichnung des Eintrags (alle Ebenen)       | —           |
| `resources`    | Wo der Beleg liegt (z. B. URL, `Email`)      | leer        |
| `tools`        | Womit (z. B. `Browser`, `Thunderbird`)       | `"Browser"` |
| `data`         | Hilfsdaten (z. B. Login-Kennung)             | leer        |
| `instructions` | Anweisungen zum Vorgehen                      | leer        |

> Hinweis zur ursprünglichen Spalten-Angabe: Die dort gelistete namenlose Spalte mit
> Default `"Browser"` war ein Tippfehler — der Default `"Browser"` gehört zu `tools`.
> Es gibt **keine** zusätzliche `channel`-Spalte.

`name` gilt für **alle** Ebenen (Kategorien und Blätter); die übrigen Felder nur für
Blätter.

### Mehrere Listen

- Listen sind **voneinander unabhängig** (eigene Struktur, eigene `done`-Stände).
- Eine neue Liste wird beim Anlegen auf **eine von zwei Arten** befüllt:
  1. **Import** aus einer Markdown-Quelle, oder
  2. **Klonen/Duplizieren** einer bestehenden Liste — Struktur wird übernommen, alle
     `done` werden auf `false` zurückgesetzt.
- Typischer Anwendungsfall: pro Periode (z. B. Jahr `2024`, `2025`) eine Liste, die
  durch Klonen der Vorperiode entsteht.

---

## 4. Funktionalität

### 4.1 GUI (`HTML`/`CSS`/`JS`)

- Stellt die **hierarchische Listenstruktur** dar (eingerückter Baum / aufklappbar).
- Nur die **unterste Ebene (Blätter)** ist inhaltlich bearbeitbar; Spalten: `done`,
  `name`, `resources`, `tools`, `data`, `instructions`.
- Die GUI darf **alles**: Listen anlegen (Import/Klonen), Einträge & Kategorien
  hinzufügen, editieren, **entfernen** (Remove ist ausschließlich GUI), `done` setzen.
- Auswahl der aktiven Liste; Freitextsuche; JSON-Export anstoßbar.

### 4.2 Programmatische Schnittstelle (`REST` + `CLI`) & Berechtigungen

Dieselbe Funktionslogik steht über eine lokale `REST`-API und ein `CLI` zur Verfügung.
Die externe Schnittstelle ist bewusst **stark eingeschränkt**:

| Operation                                   | GUI | `REST`/`CLI` (extern, inkl. KI) |
| ------------------------------------------- | :-: | :-----------------------------: |
| Alles als `JSON` exportieren                | ✅  | ✅ (lesen)                      |
| Eintrag suchen (Freitext über `name`, alle Ebenen) | ✅  | ✅ (lesen)               |
| Einträge/Felder lesen                       | ✅  | ✅ (lesen)                      |
| `done` eines Blatts setzen / zurücksetzen   | ✅  | ✅ (einzige Schreib-Operation)  |
| Eintrag/Kategorie **hinzufügen**            | ✅  | ❌                              |
| Eintrag/Felder **editieren**                | ✅  | ❌                              |
| Eintrag **entfernen** (Remove)              | ✅  | ❌                              |
| Liste **importieren** / **klonen**          | ✅  | ❌                              |

> **Bewusste Abweichung von der ursprünglichen Anforderung:** Die ursprüngliche
> Schnittstellen-Liste nannte `editieren`, `hinzufügen` und `initialer Import` als
> programmatische Funktionen. Nach Rückfrage gilt: extern sind **nur Lesen + `done`-
> Toggling** erlaubt; alle übrigen Schreib-Operationen (inkl. Import/Klonen) sind
> GUI-only. „Remove" war bereits ursprünglich GUI-only.

### 4.3 Suche

- **Freitextsuche** über die `name`-Felder **aller Ebenen** (Kategorien und Blätter).
- Liefert Treffer auf beliebiger Ebene; verfügbar in GUI, `REST` und `CLI`.

### 4.4 Export

- Vollständiger Export der aktiven Liste (oder aller Listen) als `JSON`, das die
  **verschachtelte Struktur** widerspiegelt.

### 4.5 Audit-Log

- **Jede** schreibende Aktion wird protokolliert — `done`-Toggles (extern & GUI),
  GUI-Edits, Add/Remove, Import, Klonen.
- Protokolliert mindestens: Zeitstempel, Aktion, betroffener Knoten/Liste, alter →
  neuer Wert, Herkunft (GUI / `CLI` / `REST`).

### 4.6 Initialer Import (Strikt nach Klammer-Notation)

Quelle ist das bestehende Markdown-Format (verschachtelte `- [ ]`-Checklisten). Pro
Blattzeile wird **strikt nach Klammer-Typ** geparst (keine Heuristik):

| Klammer  | Zielfeld       | Beispiel                          |
| -------- | -------------- | --------------------------------- |
| `(...)`  | `resources`    | `(https://… \| Email)`            |
| `{...}`  | `tools`        | `{Browser \| Thunderbird}`        |
| `[...]`  | `data`         | `[Login 588791127]`               |
| `<...>`  | `instructions` | `<öffne den Link …>`              |

- `name` = Text **vor** der ersten Klammergruppe.
- Mehrfachwerte innerhalb einer Klammer sind durch `|` getrennt.
- Steht z. B. eine URL fälschlich in `[...]` (wie `Amazon [https://…]`), landet sie
  **in `data`** — die strikte Zuordnung bleibt erhalten, es findet **keine** Umdeutung
  zu `resources` statt.
- Unvollständige Zeilen bleiben entsprechend lückenhaft; fehlende Felder bleiben leer
  (`tools` greift auf Default `"Browser"` zurück, sofern so festgelegt).
- Vollständige Referenz-Beispiele aus der Quelle: `1&1`, `sim.de`.

---

## 5. Architektur

```
┌────────────────────────────────────────────────────────────┐
│  Native Fenster (pywebview)                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  GUI: HTML / CSS / JS  (REST-Client)                  │   │
│  └───────────────┬──────────────────────────────────────┘   │
└──────────────────┼──────────────────────────────────────────┘
                   │ HTTP (127.0.0.1, loopback)
┌──────────────────▼──────────────────────────────────────────┐
│  FastAPI (lokaler Server)                                    │
│   • REST-Endpunkte (Lesen + done-Toggle = öffentlich;        │
│     Struktur-/Edit-/Import-Ops = GUI-privilegiert)           │
│   ├─ Core / Service-Layer  ◄────────── CLI (dünner Wrapper)  │
│   │    (Domänenlogik, Validierung, Audit)                    │
│   └─ Repository  ──►  SQLite                                 │
└──────────────────────────────────────────────────────────────┘
```

- **Stack**: `Python` (Backend), `SQLite` (DB), `HTML`/`CSS`/`JS` (GUI).
- **GUI-Anbindung**: Lokaler `FastAPI`-Server stellt eine `REST`-API bereit; die
  GUI ist ein `REST`-Client, dargestellt in einem nativen Fenster via `pywebview`.
- **CLI**: dünner Wrapper über denselben **Core/Service-Layer** — bietet extern nur
  Lesen + `done`-Toggling an.
- **Einheitliche Logik**: GUI, `CLI` und KI greifen auf dieselbe Domänenlogik zu;
  Berechtigungen werden zentral durchgesetzt.
- **Schichten**: `GUI` → `REST`/`CLI` → `Core/Service` → `Repository` → `SQLite`.

### Architektur-Schlüsselfrage (für die technische Session)

Da GUI und externe Aufrufer dieselbe lokale `REST`-API nutzen, muss verhindert werden,
dass externe Aufrufer (`CLI`/KI) die **GUI-privilegierten** Operationen (Add/Edit/
Remove/Import/Klonen) auslösen. Lösungsidee: Ein **GUI-only Session-Token**, das nur in
die GUI-Seite injiziert wird und privilegierte Endpunkte schützt; die öffentliche
Schnittstelle exponiert nur Lesen + `done`-Toggle. Detail-Design folgt.

---

## 6. Nicht-funktionale Anforderungen

- **Testabdeckung**: Unit-Tests mit **≥ `90 %`** Coverage.
- **Ein Nutzer**, lokaler Betrieb; keine Authentifizierung über Loopback hinaus.
- **Sicherheit**: `FastAPI` nur auf `127.0.0.1` (kein externer Zugriff); privilegierte
  Operationen GUI-geschützt.
- **Nachvollziehbarkeit**: vollständiges Audit-Log aller Schreibvorgänge.
- **Datenintegrität**: strikte Import-Regeln; Validierung im Service-Layer.
- **Portabilität**: Fokus `Windows` (`v1`); Architektur soll spätere Cross-Plattform
  nicht verbauen.
- **Wartbarkeit**: klare Schichtentrennung, Domänenlogik unabhängig von GUI/Transport.

---

## 7. Persistenz & Installation

- **Packaging**: `PyInstaller` → ausführbare `.exe` (Windows-Fokus).
- **Speicherorte** (Vorschlag, via `platformdirs`):
  - `config` + `SQLite`-DB unter `%APPDATA%\ReceiptBoard\`.
  - Programm/Executable an geeigneter Stelle (z. B. `%LOCALAPPDATA%\Programs\ReceiptBoard\`).
- DB- und Config-Pfad konfigurierbar; saubere Erst-Initialisierung bei leerer DB.

---

## 8. Annahmen (von mir gesetzt — bitte in der nächsten Session bestätigen)

- `Python` `3.12+`; Tests mit `pytest` + `pytest-cov`.
- `FastAPI` auf Loopback mit festem oder ephemerem Port; `pywebview` lädt diese URL.
- Datenmodell als **Adjazenzliste** (`id`, `parent_id`, `list_id`, `type`
  [`category`|`leaf`], `name`, `position`, `done`, `resources`, `tools`, `data`,
  `instructions`, Zeitstempel).
- Audit-Log als eigene `SQLite`-Tabelle.
- Kategorien zeigen in der GUI optional einen **abgeleiteten Fortschritt** (z. B.
  „x/y erledigt") — rein darstellend, nicht persistiert.
- Pfade/Speicherorte via `platformdirs` statt hartkodiert.

---

## 9. Entscheidungs-Log (Kickoff)

| Thema                       | Entscheidung                                                              |
| --------------------------- | ------------------------------------------------------------------------ |
| GUI ↔ Backend               | `FastAPI` (lokal, `REST`) + `pywebview`-Fenster; GUI ist `REST`-Client    |
| Programmatische Surface     | `REST` + `CLI`                                                            |
| Packaging                   | `PyInstaller` (Windows-`.exe`)                                            |
| Scope `v1`                  | Nur strukturierter Store + Schnittstelle (keine Automatisierung/Dateien)  |
| Mehrere Listen              | Unabhängig; neue Liste per **Import** **oder** **Klonen** (`done` reset)   |
| Spalten                     | `done`, `name`, `resources`, `tools` (Default `"Browser"`), `data`, `instructions` |
| Import-Parsing              | **Strikt** nach Klammer-Typ, keine Heuristik                              |
| Externer Schreib-Scope      | **Nur** `done`-Toggle (Blätter) + Lesen; Rest GUI-only                    |
| Remove                      | Ausschließlich GUI                                                        |
| Audit-Log                   | Für **alle** Schreibaktionen                                             |
| Testabdeckung               | ≥ `90 %`                                                                  |

---

## 10. Nächste Schritte

1. **Nächste Session**: aus diesem Brief eine **detaillierte technische Beschreibung**
   ausarbeiten (Datenmodell, API-Vertrag, GUI-Konzept, Audit-Schema, Import-Spezifikation,
   Token-/Berechtigungs-Design, Build/Packaging).
2. Aus der technischen Beschreibung **Tasks** ableiten.
3. Implementierung gemäß Branching-/Ticket-Workflow.
