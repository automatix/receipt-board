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
- **Aktionsfelder** (nur am Eintrag): **Ressourcen** (typisierte Fundorte — `URL`/`Email`),
  **Werkzeuge** (z. B. `Browser`, `Thunderbird`), **Daten** (Freitext, z. B. ein Login),
  **Anweisungen** (Freitext-Hinweis).
- **Vokabular** — app-weite Listen erlaubter Werte für **Ressourcentypen** und **Werkzeuge**.

> **Wo darf was geändert werden?** Struktur-Änderungen (anlegen, bearbeiten, entfernen,
> importieren, klonen, löschen, Vokabular) gehen **nur in der GUI**. Die CLI/Schnittstelle
> darf nur **lesen** und das **`done` eines Eintrags** umschalten.

## 3. Die Oberfläche

> **Sprache:** Die App startet auf **Englisch**. Über den **Sprach-Button** (🌐 **EN/DE**)
> rechts in der Werkzeugleiste schaltest du auf **Deutsch** (die Wahl bleibt gespeichert).
> Diese Anleitung nennt die **deutschen** Beschriftungen.

Oben die **Werkzeugleiste** (die Buttons tragen jeweils ein **Symbol**):

| Element | Funktion |
| ------- | -------- |
| **‹ / ›** (Zurück/Vorwärts) | im Navigations-Verlauf zurück/vorwärts (Ansicht, aktive Checklist, offene Suche) — auch per `Alt`+`←`/`→` und den **Maus-Seitentasten** |
| **Auswahl** (Dropdown) | aktive Checklist wählen |
| **Neu** | leere Checklist anlegen |
| **Import** | Checklist aus Markdown importieren (siehe §6) |
| **Klonen** | aktive Checklist kopieren (Struktur + Felder, alle Häkchen zurückgesetzt) |
| **Löschen** | aktive Checklist löschen (mit Bestätigung) |
| **Export** | aktive Checklist speichern — Format-Dialog **Markdown** (vorausgewählt) oder **JSON**, dann „Speichern unter“ |
| **Suchfeld** | Freitextsuche (mit `Enter`) |
| **Vokabular / Checklist** | zwischen Baum- und Vokabular-Ansicht umschalten |
| **Ressourcen / Checklist** | alle **URL-Ressourcen** der aktiven Checklist als Tabelle (`URL` / Eintrag / Pfad, in Baum-Reihenfolge) — dritter im Bunde der Ansichts-Umschalter |
| **Audit** | das Audit-Log einsehen (siehe §10) |
| **Updates** | nach einer neuen Version suchen (siehe §12) |
| **🌐 EN/DE** | Sprache umschalten (Englisch ↔ Deutsch) |
| **Design** (System/Hell/Dunkel) | Farbschema umschalten |

> **Schmale Fenster:** Reicht die Breite nicht für eine Zeile, bricht die Werkzeugleiste
> in **maximal zwei Zeilen** um — Navigation und Checklist-Aktionen oben, Suchfeld und
> Ansichts-/System-Buttons darunter. Wird das Fenster noch schmaler, werden am rechten
> Rand so viele Buttons ausgeblendet wie nötig (nie mehr als zwei Zeilen); beim
> Verbreitern erscheinen sie wieder.

Darunter der **Baum** der aktiven Checklist (bzw. die Vokabular-Verwaltung).

> **Textsuche auf der Seite:** `Strg`+`F` öffnet die übliche Suchleiste (oben rechts) für
> den gerade angezeigten Inhalt — alle Treffer werden hervorgehoben, ein Zähler zeigt
> `aktuell/gesamt`. `Enter` bzw. `F3` springt zum nächsten, `Umschalt`+`Enter` bzw.
> `Umschalt`+`F3` zum vorigen Treffer, `Esc` schließt. (Das **Suchfeld** in der
> Werkzeugleiste durchsucht dagegen die ganze Checklist inkl. zugeklappter Kategorien.)

Ganz unten zeigt eine **schmale graue Info-Leiste** rechts die installierte **App-Version**
(z. B. `v1.6.0`).

## 4. Mit dem Baum arbeiten

- **Auf-/Zuklappen:** das Dreieck **▸ / ▾** vor einer Kategorie.
- **Erledigt setzen:** die **Checkbox** am Knoten.
  - **Eintrag:** schaltet nur diesen Eintrag.
  - **Kategorie:** schaltet den **ganzen Teilbaum** (Cascade). Sind alle Kinder erledigt,
    wird die Kategorie automatisch erledigt; ein offenes Kind hält sie offen.
  - **Eine Kategorie abwählen** ist destruktiv (setzt den Teilbaum zurück) und wird mit
    einem Dialog bestätigt, der die **Anzahl betroffener erledigter Einträge** zeigt.
- **Umbenennen (Kategorie):** **Doppelklick** auf den Namen → tippen → `Enter` (`Esc`
  bricht ab). Einträge werden im Bearbeiten-Dialog umbenannt.
- **Eintrag bearbeiten:** ein **Klick auf die Eintrags-Zeile** öffnet den Bearbeiten-Dialog
  (die Überschrift zeigt den **Eintragsnamen** und folgt dem Namensfeld live beim Tippen)
  für **Name**, **Daten**, **Anweisungen** (mehrzeiliges, in der Höhe
  vergrößerbares Textfeld), die Checkbox **„manuell“** auf Eintragsebene (der ganze
  Eintrag ist manuell zu bearbeiten, Import-Marker `~manually~` außerhalb der Klammern),
  **Ressourcen** (Typ aus dem
  Vokabular + optionaler Wert + Checkbox **„manuell“** = nicht automatisierbar;
  *„+ Ressource“* für weitere Zeilen) und **Werkzeuge** (Mehrfachauswahl). Der Cursor steht direkt im Feld **Name** (am Ende). **Speichern**
  übernimmt; `Esc`, **Abbrechen** oder ein Klick neben den Dialog verwerfen die Eingaben.
- **Feld-Vorschau:** hinter dem Eintrags-Namen fasst eine graue Vorschau die Felder in
  ihrer Import-Notation zusammen (siehe §6): `~manually~` (falls gesetzt), `(Ressourcen)`,
  `{Werkzeuge}`, `[Daten]`, `<Anweisungen>`. Die Inhalte werden abgekürzt: `URL`-Ressourcen als `URL:...`,
  Ressourcen ohne Wert nur mit dem Typnamen (z. B. `Email`), sonst `Typ:Wert`; **Daten**
  maximal `25` Zeichen, **Anweisungen** maximal `50` Zeichen (jeweils mit `…`).
- **Hinzufügen:** die dezenten Buttons **„+ Kategorie“** / **„+ Eintrag“** erscheinen beim
  Überfahren einer **Kategorie-Zeile** (direkt hinter dem Kategorienamen); auf oberster Ebene sitzt
  **„+ Kategorie“** neben dem **Checklist-Titel** (Einträge liegen immer unter einer
  Kategorie). **„+ Eintrag“** öffnet denselben Dialog wie *„Eintrag bearbeiten“* — alle
  Felder (Name, Data, Instructions, Resources, Tools) lassen sich direkt in einem Schritt
  setzen.
- **Entfernen:** das **Papierkorb-Symbol 🗑** (mit Bestätigung) — es erscheint beim
  Überfahren direkt hinter dem Zeileninhalt: bei Kategorien in der Reihe der
  `+`-Buttons, bei Einträgen hinter der Feld-Vorschau.
- **Verschieben / Umsortieren (Drag & Drop):**
  - einen Knoten auf eine **Kategorie-Zeile** ziehen → **in** diese Kategorie verschieben
    (ans Ende);
  - einen Knoten auf eine **Einfügelinie** zwischen Geschwistern ziehen → an diese
    **Position** umsortieren bzw. umhängen.
  - Eine Kategorie kann **nicht** in ihren eigenen Teilbaum verschoben werden.

Die Ansicht aktualisiert sich **automatisch live**: Eigene Aktionen und externe Änderungen
(z. B. per CLI oder Automatisierung) erscheinen ohne Zutun innerhalb weniger Sekunden – ein
manuelles Aktualisieren ist nicht nötig.

## 5. Checklists anlegen

Drei Wege (alle in der GUI):

- **Neu** — leere Checklist (Name eingeben).
- **Import** — aus dem Markdown-Format (siehe §6).
- **Klonen** — Tiefenkopie der aktiven Checklist; alle Häkchen werden zurückgesetzt.

Der **Name ist überall Pflicht**: Ein leeres Namensfeld schließt den Dialog nicht mehr,
sondern markiert das Feld und zeigt einen Hinweis (gilt auch für neue Kategorien und das
Duplizieren von Vokabular-Einträgen).

## 6. Checklist importieren (Markdown-Format)

Über **Import** den Namen vergeben und die Markdown-Checkliste einfügen — entweder direkt in
das Textfeld **einfügen**, oder eine Datei **laden**: per Button **„Datei wählen…"** oder
indem du die Datei **in den Dialog ziehst**. Der Dateiname erscheint dann neben dem Button,
der Inhalt im Textfeld (beides bleibt vor dem Import editierbar). **Name und Inhalt sind
Pflichtfelder** (mit `*` markiert): **„Importieren"** prüft die Eingaben zuerst — genau wie
**„Prüfen"** — und schließt den Dialog nur, wenn der Import wirklich läuft; bei leeren
Pflichtfeldern oder Fehlern im Inhalt bleibt der Dialog offen und zeigt die Meldungen an.
Regeln:

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
    Typ `Email`. Der Marker **`~manually~`** im Token (z. B.
    `(https://… ~manually~ | Email)`) markiert die Ressource als **manuell zu bearbeiten**
    (nicht automatisierbar); andere `~…~`-Marker sind ungültig.
  - **tools:** müssen bereits im **Vokabular** stehen (sonst Abbruch).
- **Eintrag als „manuell“ markieren:** `~manually~` **außerhalb** der Klammern — nach dem
  Namen oder zwischen den Feldern — markiert den **ganzen Eintrag** als manuell zu
  bearbeiten, z. B. `- [ ] Taxi ~manually~` (im Dialog: die Checkbox **„manuell“** auf
  Eintragsebene).
- **Reservierte Zeichen:** Die neun Zeichen `( ) [ ] { } < > ~` sind **Steuerzeichen** und
  im **Freitext** (Namen, Werte) **nicht erlaubt**. Beispiel: `Taxi (klassisch)` ist
  ungültig — die Klammer würde als resources-Feld gelesen. Die Tilde ist nur als
  `~manually~`-Marker erlaubt — pro Ressource innerhalb von `( … )` oder pro Eintrag
  außerhalb der Klammern (eine URL mit `~` ist daher nicht importierbar).
- **Alles-oder-nichts:** Bei **irgendeinem** Fehler wird **nichts** importiert; du erhältst
  einen genauen Bericht (Zeile + Wert). Behebe die Werte oder erweitere das Vokabular und
  importiere erneut.
- **Vorab prüfen (Dry-Run):** Der Knopf **„Prüfen"** im Import-Dialog testet die Datei
  **ohne** zu importieren — er zeigt entweder „✓ Importierbar: N Kategorien, M Einträge"
  oder die genaue Fehlerliste (Zeile · Wert · Meldung). Erst **„Importieren"** schreibt.
  Dasselbe geht per CLI: `receipt-board validate DATEI` (Exit 0 = importierbar, sonst 1).

**Gültiges Beispiel** (Einrückung = Tabs):

```text
- [ ] Verbindung
	- [ ] Festnetz&DSL
		- [ ] 1&1 (https://control-center.1und1.de/invoice.html#/current | Email) {Browser | Thunderbird} [Login 588791127] <öffne den Link im Browser>
```

Ergibt: Kategorie *Verbindung* › Kategorie *Festnetz&DSL* › Eintrag *1&1* mit zwei
Resources (`URL`, `Email`), zwei Tools, `data` „Login 588791127" und einer Instruktion.

## 7. Vokabular verwalten

Mit **Vokabular** umschalten. Zwei **Tabellen** mit beschrifteten Spalten:
**Ressourcentypen** (z. B. `URL`, `Email`) und **Werkzeuge** (z. B. `Browser`,
`Thunderbird`).

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

**Export** öffnet einen Dialog mit der Formatwahl (**Markdown**, vorausgewählt, oder
**JSON**) und lädt dann die aktive Checklist herunter:

- **Markdown** — die Checklist in der **Import-Notation** (§6, kanonische Form: Tabs,
  `- [ ]`/`- [x]`, `~manually~`, Feldgruppen `( ) { } [ ] < >`). Eine unverändert
  importierte, notationskonforme Datei exportiert **eins zu eins**. Ausnahmen: beim Import
  **ignorierte** Kategorie-Felder fehlen (§6-Warnung); Zeilenumbrüche in Daten/Anweisungen
  (nur über die GUI möglich) werden zu Leerzeichen; über die GUI eingegebene Namen mit
  Steuerzeichen exportieren zwar, sind aber nicht re-importierbar.
- **JSON** — der vollständige, **verschachtelte JSON-Baum** (alle Felder).

## 10. Daten & Nachvollziehbarkeit

Alle Daten liegen lokal in `%LOCALAPPDATA%\receipt-board\receipt_board.sqlite`. **Jede**
schreibende Aktion wird in einem **Audit-Log** protokolliert (Zeitpunkt, Herkunft, Aktion,
betroffene Knoten). Das Log ist einsehbar über den Button **„Audit"** (Tabelle, neueste
zuerst) sowie per CLI (`receipt-board audit`). Backup: siehe [`INSTALL.md`](./INSTALL.md).

## 11. Für Fortgeschrittene: Kommandozeile (CLI)

Eine Kommandozeile kann lesend zugreifen und das `done` eines Eintrags umschalten (z. B. für
Automatisierung/KI). Die CLI ist **in der normalen Installation enthalten** als
`receipt-board-cli` und liegt im `PATH`, ist also aus jedem Terminal aufrufbar (in der
Entwickler-Installation: `uv run receipt-board …`):

```bash
receipt-board-cli export [--checklist ID] [--json]
receipt-board-cli search "Begriff" [--json]
receipt-board-cli urls CHECKLIST_ID [--json]   # alle URL-Ressourcen der Checklist
receipt-board-cli item done|undone ID
receipt-board-cli validate DATEI
receipt-board-cli audit [--checklist ID] [--limit N]
```

Die Schreib-Befehle setzen einen **laufenden Server** voraus — entweder die geöffnete
Desktop-App **oder** der **Headless-Modus**:

```bash
receipt-board-cli serve        # startet den Server ohne GUI-Fenster (Strg+C beendet)
```

`serve` initialisiert dieselben Daten/DB wie die App und schreibt `runtime.json`, sodass die
anderen CLI-Befehle (und beliebige REST-Clients) ihn finden. Der Server bleibt **alleiniger
Besitzer der Datenbank** — die CLI spricht ausschließlich die REST-API an, nie direkt die DB.
Struktur-Änderungen bleiben der GUI vorbehalten.

## 12. Updates (aus der App heraus)

Die App kann sich **selbst aktualisieren**: Beim Start prüft sie still, ob auf GitHub eine
neuere Version vorliegt, und zeigt dann ein **Hinweis-Banner** (Version + „Was ist neu?").
Manuell startest du die Prüfung über den Button **„Updates"** — ein bereits angezeigtes
Hinweis-Banner verschwindet dabei kurz und kommt mit dem (ggf. frischen) Ergebnis zurück,
sodass sichtbar ist, dass neu geprüft wurde.

Mit **„Jetzt installieren"** lädt die App die neue `setup.exe` herunter und startet sie;
Windows fragt per **UAC** nach Adminrechten, dann beendet sich die App, damit der Installer
die Dateien ersetzen kann. **„Später"** blendet das Banner aus. Es wird **nie automatisch**
installiert, und deine Daten bleiben erhalten. Details: [`INSTALL.md`](./INSTALL.md).
