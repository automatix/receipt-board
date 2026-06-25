# Receipt Board — Bedienungsanleitung

Diese Anleitung beschreibt die Bedienung der Desktop-App für **Endanwender**.
Installation: siehe [`INSTALL.md`](./INSTALL.md). Begriffe im Detail:
[`GLOSSARY.md`](./GLOSSARY.md).

## 1. Wozu dient Receipt Board?

Beim Jahres- oder Monatsabschluss arbeitest du eine **Ausgaben-Checkliste** ab: pro
Ausgabe(-nquelle) werden die fehlenden Belege zusammengesucht. Receipt Board hält diese
Checkliste **strukturiert** statt als lose Markdown-Datei.

Die App ist **semantik-agnostisch** — sie kennt nur Häkchen. Was „erledigt" bedeutet
(„Beleg beschafft"), entscheidest du.

## 2. Grundbegriffe

- **Checklist** — eine eigenständige Liste (z. B. „Expenses 2024"). Es kann mehrere geben.
- **Category (Kategorie)** — Gliederungsknoten; darf Unterkategorien **und** Einträge
  gemischt enthalten.
- **Expense Item (Eintrag)** — das abzuarbeitende Blatt (z. B. „Amazon", „1&1"); trägt die
  Aktionsfelder; hat nie Unterpunkte.
- **done** — ein Häkchen auf **jedem** Knoten.
- **Aktionsfelder** (nur am Eintrag): **resources** (typisierte Fundorte — `URL`/`Email`),
  **tools** (Werkzeuge — z. B. `Browser`, `Thunderbird`), **data** (Freitext, z. B. ein
  Login), **instructions** (Freitext-Hinweis).
- **Vokabular** — app-weite Listen erlaubter Werte für **Resource Type** und **Tool**.

> **Wo darf was geändert werden?** Struktur-Änderungen (anlegen, bearbeiten, entfernen,
> importieren, klonen, löschen, Vokabular) gehen **nur in der GUI**. Die CLI/Schnittstelle
> darf nur **lesen** und das **`done` eines Eintrags** umschalten.

## 3. Die Oberfläche

Oben die **Werkzeugleiste**:

| Element | Funktion |
| ------- | -------- |
| **Auswahl** (Dropdown) | aktive Checklist wählen |
| **Neu** | leere Checklist anlegen |
| **Import** | Checklist aus Markdown importieren (siehe §6) |
| **Klonen** | aktive Checklist kopieren (Struktur + Felder, alle Häkchen zurückgesetzt) |
| **Löschen** | aktive Checklist löschen (mit Bestätigung) |
| **Export** | aktive Checklist als JSON-Datei herunterladen |
| **Aktualisieren** | Ansicht neu laden |
| **Suchfeld** | Freitextsuche (mit `Enter`) |
| **Vokabular / Checklist** | zwischen Baum- und Vokabular-Ansicht umschalten |

Darunter der **Baum** der aktiven Checklist (bzw. die Vokabular-Verwaltung).

## 4. Mit dem Baum arbeiten

- **Auf-/Zuklappen:** das Dreieck **▸ / ▾** vor einer Kategorie.
- **Erledigt setzen:** die **Checkbox** am Knoten.
  - **Eintrag:** schaltet nur diesen Eintrag.
  - **Kategorie:** schaltet den **ganzen Teilbaum** (Cascade). Sind alle Kinder erledigt,
    wird die Kategorie automatisch erledigt; ein offenes Kind hält sie offen.
  - **Eine Kategorie abwählen** ist destruktiv (setzt den Teilbaum zurück) und wird mit
    einem Dialog bestätigt, der die **Anzahl betroffener erledigter Einträge** zeigt.
- **Umbenennen:** **Doppelklick** auf den Namen → tippen → `Enter` (`Esc` bricht ab).
- **Eintrag bearbeiten:** das **✎** am Eintrag öffnet den Dialog *„Eintrag bearbeiten"* für
  **Name**, **Data**, **Instructions**, **Resources** (Typ aus dem Vokabular + optionaler
  Wert; *„+ Resource"* für weitere Zeilen) und **Tools** (Mehrfachauswahl). **Speichern**
  übernimmt.
- **Hinzufügen:** unter jeder Kategorie **„+ Kategorie"** / **„+ Eintrag"**; auf oberster
  Ebene **„+ Kategorie"** (Einträge liegen immer unter einer Kategorie).
- **Entfernen:** das **🗑** (mit Bestätigung).
- **Verschieben / Umsortieren (Drag & Drop):**
  - einen Knoten auf eine **Kategorie-Zeile** ziehen → **in** diese Kategorie verschieben
    (ans Ende);
  - einen Knoten auf eine **Einfügelinie** zwischen Geschwistern ziehen → an diese
    **Position** umsortieren bzw. umhängen.
  - Eine Kategorie kann **nicht** in ihren eigenen Teilbaum verschoben werden.

Nach jeder Aktion wird die aktive Checklist neu geladen. Externe Änderungen (z. B. per CLI)
erscheinen nach **Aktualisieren**.

## 5. Checklists anlegen

Drei Wege (alle in der GUI):

- **Neu** — leere Checklist (Name eingeben).
- **Import** — aus dem Markdown-Format (siehe §6).
- **Klonen** — Tiefenkopie der aktiven Checklist; alle Häkchen werden zurückgesetzt.

## 6. Checklist importieren (Markdown-Format)

Über **Import** den Namen vergeben und die Markdown-Checkliste einfügen. Regeln:

- Jede Zeile: `- [ ] Name …` (bzw. `- [x]` = erledigt). Die **Einrückung** bestimmt die
  Hierarchie.
- **Typ automatisch:** Zeilen **ohne** Unterpunkte werden **Einträge**, Zeilen **mit**
  Unterpunkten werden **Kategorien**.
- **Name** = Text **vor** der ersten Klammer.
- **Felder nach Klammertyp** (nur bei Einträgen):

  | Klammer | Feld | Beispiel |
  | ------- | ---- | -------- |
  | `( … )` | resources | `(https://… \| Email)` |
  | `{ … }` | tools | `{Browser \| Thunderbird}` |
  | `[ … ]` | data | `[Login 588791127]` |
  | `< … >` | instructions | `<öffne den Link …>` |

  - Mehrere Werte mit `|` trennen.
  - **resources:** `https://…` → Typ `URL`; `Email` (optional gefolgt von einem Postfach) →
    Typ `Email`.
  - **tools:** müssen bereits im **Vokabular** stehen (sonst Abbruch).
- **Reservierte Zeichen:** Die acht Zeichen `( ) [ ] { } < >` sind **Steuerzeichen** und im
  **Freitext** (Namen, Werte) **nicht erlaubt**. Beispiel: `Taxi (klassisch)` ist ungültig —
  die Klammer würde als resources-Feld gelesen.
- **Alles-oder-nichts:** Bei **irgendeinem** Fehler wird **nichts** importiert; du erhältst
  einen genauen Bericht (Zeile + Wert). Behebe die Werte oder erweitere das Vokabular und
  importiere erneut.

**Gültiges Beispiel** (Einrückung = Tabs):

```text
- [ ] Verbindung
	- [ ] Festnetz&DSL
		- [ ] 1&1 (https://control-center.1und1.de/invoice.html#/current | Email) {Browser | Thunderbird} [Login 588791127] <öffne den Link im Browser>
```

Ergibt: Kategorie *Verbindung* › Kategorie *Festnetz&DSL* › Eintrag *1&1* mit zwei
Resources (`URL`, `Email`), zwei Tools, `data` „Login 588791127" und einer Instruktion.

## 7. Vokabular verwalten

Mit **Vokabular** umschalten. Zwei Listen: **Resource Types** (z. B. `URL`, `Email`) und
**Tools** (z. B. `Browser`, `Thunderbird`).

- **Hinzufügen:** Namen eingeben → **„Hinzufügen"**.
- **Umbenennen:** in das Namensfeld schreiben → `Enter`. Da Einträge per `id` referenzieren,
  wirkt das Umbenennen überall.
- **Entfernen:** **„Entfernen"** — nur möglich, wenn der Wert von **keinem** Eintrag genutzt
  wird (sonst Hinweis).

## 8. Suchen

Suchbegriff oben eingeben → `Enter`. Ergebnis: eine **flache** Trefferliste über **alle**
Ebenen, je Treffer mit Symbol (📁 Kategorie / 📄 Eintrag), Name und **Pfad**. **„Schließen"**
kehrt zum Baum zurück.

## 9. Export

**Export** lädt die aktive Checklist als vollständigen, **verschachtelten JSON-Baum**
herunter (alle Felder).

## 10. Daten & Nachvollziehbarkeit

Alle Daten liegen lokal in `%APPDATA%\ReceiptBoard\receipt_board.sqlite`. **Jede**
schreibende Aktion wird in einem **Audit-Log** protokolliert (Zeitpunkt, Herkunft, Aktion,
betroffene Knoten). Backup: siehe [`INSTALL.md`](./INSTALL.md).

## 11. Für Fortgeschrittene: Kommandozeile (CLI)

Bei **laufender** App kann eine Kommandozeile lesend zugreifen und das `done` eines Eintrags
umschalten (z. B. für Automatisierung/KI):

```bash
receipt-board export [--checklist ID] [--json]
receipt-board search "Begriff" [--json]
receipt-board item done|undone ID
```

Die CLI ist in der Entwickler-Installation enthalten (siehe [`README.md`](../README.md));
Struktur-Änderungen bleiben der GUI vorbehalten.
