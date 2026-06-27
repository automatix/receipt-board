# In-app updater via public GitHub Releases

The app can update itself: it checks the latest **public** GitHub Release and, on the user's
confirmation, downloads that release's installer and launches it. The repository is public, so
the GitHub REST API is read **unauthenticated** — no personal access token is stored or
required (the earlier private-repo idea that needed a PAT is dropped).

How it works: `GET /update/check` reads `…/releases/latest` and compares the tag to the running
version (`receipt_board.__version__`). When the tag is newer it returns the release-notes URL
and the `*-setup.exe` asset URL. `POST /update/install` re-resolves the latest release
**server-side** (it never trusts a URL supplied by the client), verifies the asset is hosted on
GitHub, downloads it to a temp directory, launches the installer, and then closes the window so
the running app releases its files for replacement. Both endpoints are **token-gated** (GUI-only,
ADR-0009): updating is a privileged local action.

The GUI offers a manual "check for updates" action and runs a silent check on startup; when a
newer version exists it shows a **non-blocking banner** (version + notes link, Install / Later).
Installing is always explicit — the app never auto-installs. The installer is the existing
per-machine Inno Setup `setup.exe`, which requires elevation (UAC), so the in-place file swap is
performed by the installer, not the app.

Consequence: users update from inside the app without visiting GitHub. Trade-off: making the repo
public is a prerequisite (chosen over storing a PAT in the local config or running a separate
public release channel). The actual elevated install + file swap is driven by the UAC installer
and cannot be exercised headlessly in CI; the download/launch/quit wiring is unit-tested with a
mock transport and a stubbed launcher.

Considered and not chosen: bundling a PAT in `config.toml` (keeps the repo private but stores a
secret in cleartext locally) and a separate public release channel (more infrastructure).
Silent/background auto-update was rejected — updates touch Program Files via UAC and should be
user-initiated.
