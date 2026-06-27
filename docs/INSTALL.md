# Receipt Board — Installationsanleitung

Diese Anleitung richtet sich an **Endanwender**. Entwickler-Setup (aus dem Quellcode bauen,
den Installer selbst erzeugen) steht in der [`README.md`](../README.md) und in
[`docs/dev-testing.md`](./dev-testing.md).

## Voraussetzungen

- **Windows 11** (der Installer ist für Windows 11 ausgelegt).
- **Microsoft Edge WebView2 Runtime** — auf Windows 11 vorinstalliert. Falls beim Start
  **kein Fenster** erscheint, die „Evergreen Standalone"-Runtime von Microsoft installieren:
  <https://developer.microsoft.com/microsoft-edge/webview2/>.

## Installation (empfohlen) — `setup.exe`

Receipt Board wird als **Windows-Installer** ausgeliefert (Inno Setup, per-machine).

1. Auf der **Releases-Seite** den Installer herunterladen:
   <https://github.com/automatix/receipt-board/releases> →
   `receipt-board-v1.3.0-setup.exe`. *(Privates Repo: nur Berechtigte mit Zugriff.)*
2. Die `setup.exe` per Doppelklick starten.
3. Windows fragt per **Benutzerkontensteuerung (UAC)** nach Administratorrechten —
   bestätigen (die Installation erfolgt nach `C:\Program Files\Receipt Board\`, also
   per-machine).
4. Dem Assistenten folgen (optional ein **Desktop-Symbol** anhaken). Nach Abschluss liegt
   **Receipt Board** im **Startmenü** (und ggf. auf dem Desktop).
5. Beim **ersten Start** legt die App ihren Datenordner an:
   `%LOCALAPPDATA%\receipt-board\` (Datenbank, `config.toml`, `runtime.json`, Log). Der
   Programmordner unter `Program Files` bleibt unverändert (schreibgeschützt-tauglich).

### Windows SmartScreen / „Unbekannte App"

Der Installer ist **nicht code-signiert**, deshalb zeigt Windows beim Start ggf.
**„Der Computer wurde durch Windows geschützt" (Microsoft Defender SmartScreen)**. Das ist
für eine unsignierte, aus dem Internet geladene Datei erwartbar:

- **Einmalig zulassen:** im Dialog **„Weitere Informationen" → „Trotzdem ausführen"**.
- **Dauerhaft vermeiden:** die `setup.exe` vor dem Start **entsperren** — Rechtsklick →
  **Eigenschaften** → unten **„Zulassen"/„Unblock"** ankreuzen → OK; oder per PowerShell:

  ```powershell
  Unblock-File "$HOME\Downloads\receipt-board-v1.3.0-setup.exe"
  ```

> Selbst-signierte Zertifikate helfen SmartScreen **nicht**. Eine vollständig warnungsfreie
> Auslieferung an Dritte erfordert ein (kostenpflichtiges) **Code-Signing-Zertifikat**
> (Authenticode, idealerweise EV); für den lokalen Eigenbetrieb genügt das Entsperren oben.

## Deinstallation

Über **Einstellungen → Apps → Installierte Apps** (oder klassisch **Systemsteuerung →
Programme und Features**) **Receipt Board** auswählen und deinstallieren. Der Uninstaller
entfernt das Programm und die Verknüpfungen.

**Benutzerdaten:** Am Ende der Deinstallation fragt der Uninstaller, ob auch die
**Benutzerdaten und Konfiguration** entfernt werden sollen (`%LOCALAPPDATA%\receipt-board\`
— `receipt_board.sqlite`, `config.toml`, `runtime.json`, `receipt-board.log`):

- **Standard = Nein (behalten)** — so findet eine spätere Neuinstallation die alten Daten
  wieder.
- **Ja** löscht den Datenordner endgültig (alle Checklists weg).
- Bei einer **stillen** Deinstallation (`/VERYSILENT`) erscheint **keine** Abfrage und es
  werden **keine** Daten gelöscht.

## Datenspeicherort & Backup

Alle Daten liegen in `%LOCALAPPDATA%\receipt-board\`:

- `receipt_board.sqlite` — die Datenbank. **Backup** = diese Datei kopieren.
- `config.toml` — Konfiguration: `[server].port` (`0` = automatischer Port) und optional
  `[database].path` (anderer DB-Speicherort).
- `runtime.json` — interner Port des laufenden Servers (wird automatisch verwaltet).

Mit der Umgebungsvariable **`RECEIPT_BOARD_HOME`** lässt sich ein anderer Datenordner wählen
(z. B. für einen portablen Betrieb).

## Erststart prüfen (ohne Fenster)

```powershell
& "$env:ProgramFiles\Receipt Board\receipt-board.exe" --check
```

Führt nur die Erstinitialisierung aus (Ordner + Datenbank anlegen) und beendet sich wieder —
nützlich zum Testen der Installation.

## Variante (Legacy) — portabler Ordner ohne Installer

Wer keinen Installer nutzen möchte, kann die App weiterhin als portablen `onedir`-Ordner
selbst bauen und direkt starten — siehe **„Selbst bauen"** in der
[`README.md`](../README.md) (`uv run pyinstaller receipt_board.spec` →
`dist/receipt-board/receipt-board.exe`). Bis einschließlich `v1.1.0` wurde Receipt Board als
ZIP (`receipt-board-vX.Y.Z-windows.zip`) ausgeliefert; ab `v1.2.0` ist der **Installer** der
empfohlene Weg.

## Bedienung

Wie du mit der App arbeitest, steht in der
[Bedienungsanleitung](./USER_GUIDE.md).
