# Receipt Board — Installationsanleitung

Diese Anleitung richtet sich an **Endanwender**. Entwickler-Setup (aus dem Quellcode)
steht in der [`README.md`](../README.md).

## Voraussetzungen

- **Windows 10/11** (`v1`-Fokus).
- **Microsoft Edge WebView2 Runtime** — auf aktuellen Windows-Systemen vorinstalliert. Falls
  beim Start **kein Fenster** erscheint, die „Evergreen Standalone"-Runtime von Microsoft
  installieren: <https://developer.microsoft.com/microsoft-edge/webview2/>.

## Variante A — Gepackte Anwendung (empfohlen)

Receipt Board wird als eigenständiger Ordner ausgeliefert (PyInstaller `onedir`).

1. Auf der **Releases-Seite** das ZIP herunterladen:
   <https://github.com/automatix/receipt-board/releases> →
   `receipt-board-v1.0.1-windows.zip`. *(Privates Repo: nur Berechtigte mit Zugriff.)*
2. Entpacken; den Ordner `receipt-board` (enthält `receipt-board.exe` und den Unterordner
   `_internal/`) an einen festen Ort kopieren, z. B. `%LOCALAPPDATA%\Programs\ReceiptBoard\`.
3. `receipt-board.exe` per Doppelklick starten (optional eine Verknüpfung anlegen).
4. Beim **ersten Start** legt die App ihren Datenordner an:
   `%APPDATA%\ReceiptBoard\` (Datenbank, `config.toml`, `runtime.json`).

> Ohne Repo-Zugriff (oder für eine eigene Variante) baust du den Ordner wie in **Variante B**.

## Variante B — Selbst bauen

Voraussetzungen: `Python 3.12+`, [`uv`](https://docs.astral.sh/uv/), `Node.js`.

```bash
uv sync
cd gui-src && npm ci && npm run build && cd ..
uv run pyinstaller receipt_board.spec
```

Ergebnis: `dist/receipt-board/` — wie in **Variante A** weiterverwenden.

## Variante C — Direkt aus dem Quellcode starten

```bash
uv sync
cd gui-src && npm ci && npm run build && cd ..
uv run receipt-board-app
```

## Datenspeicherort & Backup

Alle Daten liegen in `%APPDATA%\ReceiptBoard\`:

- `receipt_board.sqlite` — die Datenbank. **Backup** = diese Datei kopieren.
- `config.toml` — Konfiguration: `[server].port` (`0` = automatischer Port) und optional
  `[database].path` (anderer DB-Speicherort).
- `runtime.json` — interner Port des laufenden Servers (wird automatisch verwaltet).

Mit der Umgebungsvariable **`RECEIPT_BOARD_HOME`** lässt sich ein anderer Datenordner wählen
(z. B. für einen portablen Betrieb).

## Erststart prüfen (ohne Fenster)

```bash
receipt-board.exe --check
```

Führt nur die Erstinitialisierung aus (Ordner + Datenbank anlegen) und beendet sich wieder —
nützlich zum Testen der Installation.

## Deinstallation

1. Den Programmordner löschen.
2. Optional `%APPDATA%\ReceiptBoard\` löschen — **entfernt alle Checklists**.

## Bedienung

Wie du mit der App arbeitest, steht in der
[Bedienungsanleitung](./USER_GUIDE.md).
