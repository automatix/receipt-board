"""In-app update check against public GitHub Releases (issue #81, ADR-0013).

The repository is **public**, so the latest release is read from the GitHub REST API
**unauthenticated** — no personal access token. We compare the running version against the
latest release tag and, when newer, expose the installer asset URL so the GUI can offer a
one-click update.

This module is transport-agnostic: callers pass an ``httpx.Client`` so tests can drive it
with a mock transport (no real network in CI).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

GITHUB_API = "https://api.github.com"
DEFAULT_REPO = "automatix/receipt-board"
ENV_REPO = "RECEIPT_BOARD_GITHUB_REPO"
INSTALLER_SUFFIX = "-setup.exe"
REQUEST_TIMEOUT = 10.0


def repo() -> str:
    """The ``owner/name`` slug to query (override via env for tests/forks)."""
    return os.environ.get(ENV_REPO) or DEFAULT_REPO


def parse_version(text: str) -> tuple[int, ...]:
    """Parse a dotted numeric version into a comparable tuple.

    A leading ``v`` and any pre-release/build suffix (``-rc1``, ``+meta``) are ignored;
    unparsable input degrades to ``(0,)`` so it never sorts above a real version.
    """
    core = text.strip().lstrip("vV").split("-", 1)[0].split("+", 1)[0]
    parts = tuple(int(p) for p in core.split(".") if p.isdigit())
    return parts or (0,)


def is_newer(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str | None
    update_available: bool
    notes_url: str | None
    asset_url: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def select_installer_asset(release: dict) -> str | None:
    """Return the ``browser_download_url`` of the ``*-setup.exe`` asset, if present."""
    for asset in release.get("assets", []) or []:
        name = asset.get("name", "")
        if name.endswith(INSTALLER_SUFFIX):
            url = asset.get("browser_download_url")
            if url:
                return url
    return None


def fetch_latest_release(client: httpx.Client, *, repo_name: str | None = None) -> dict:
    """GET the latest release JSON for the repo (raises on HTTP/transport error)."""
    name = repo_name or repo()
    response = client.get(
        f"{GITHUB_API}/repos/{name}/releases/latest",
        headers={"Accept": "application/vnd.github+json"},
    )
    response.raise_for_status()
    return response.json()


def build_update_info(current: str, release: dict) -> UpdateInfo:
    """Turn a GitHub release payload into an :class:`UpdateInfo` (pure, no I/O)."""
    tag = release.get("tag_name") or ""
    latest = tag.lstrip("vV") or None
    available = latest is not None and is_newer(latest, current)
    return UpdateInfo(
        current=current,
        latest=latest,
        update_available=available,
        notes_url=release.get("html_url"),
        asset_url=select_installer_asset(release),
    )


def check_for_update(
    current: str, *, client: httpx.Client, repo_name: str | None = None
) -> UpdateInfo:
    """Fetch the latest release and compare it to ``current``."""
    release = fetch_latest_release(client, repo_name=repo_name)
    return build_update_info(current, release)


def is_trusted_asset_url(url: str) -> bool:
    """Only download installers served by GitHub (release pages + asset CDN).

    Guards against following an attacker-controlled URL: GitHub release assets live on
    ``github.com`` and redirect to ``*.githubusercontent.com``.
    """
    host = (httpx.URL(url).host or "").lower()
    return host == "github.com" or host.endswith(".githubusercontent.com")


def download_installer(url: str, dest_dir: Path, *, client: httpx.Client) -> Path:
    """Stream the installer to ``dest_dir`` and return the written path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = url.rsplit("/", 1)[-1] or "receipt-board-setup.exe"
    dest = dest_dir / filename
    with client.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)
    return dest


def launch_installer(path: Path) -> subprocess.Popen:
    """Start the downloaded installer detached so it survives this process exiting."""
    creationflags = 0
    if os.name == "nt":  # pragma: no cover - Windows-only flags
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen([str(path)], creationflags=creationflags, close_fds=True)
