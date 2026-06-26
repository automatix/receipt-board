"""Thin HTTP client for the CLI (ADR-0011).

Talks to the running local app over the public surface; the port comes from
``runtime.json``. Friendly errors when the app is not running or unreachable.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from receipt_board.api.runtime import read_port


class CliError(Exception):
    """A user-facing CLI error (rendered to stderr; exit code 1)."""


class ApiClient:
    def __init__(self, base_url: str, *, timeout: float = 10.0) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"X-Receipt-Board-Client": "cli"},
        )

    @classmethod
    def from_runtime(cls, runtime_path: str | Path) -> ApiClient:
        try:
            port = read_port(runtime_path)
        except FileNotFoundError as exc:
            raise CliError(
                f"Receipt Board does not appear to be running (no {runtime_path}). "
                "Start the app first."
            ) from exc
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            raise CliError(f"The runtime file {runtime_path} is invalid.") from exc
        return cls(f"http://127.0.0.1:{port}")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: object) -> object:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.ConnectError as exc:
            raise CliError(
                "Could not connect to the running Receipt Board app. Is it running?"
            ) from exc
        if response.status_code >= 400:
            raise CliError(self._error_message(response))
        return response.json() if response.content else None

    @staticmethod
    def _error_message(response: httpx.Response) -> str:
        try:
            error = response.json().get("error", {})
            return error.get("message") or f"HTTP {response.status_code}"
        except (json.JSONDecodeError, ValueError):
            return f"HTTP {response.status_code}"

    def list_checklists(self) -> list[dict]:
        return self._request("GET", "/checklists")

    def export(self, checklist_id: int) -> dict:
        return self._request("GET", f"/checklists/{checklist_id}")

    def search(self, query: str) -> list[dict]:
        return self._request("GET", "/search", params={"q": query})

    def set_item_done(self, item_id: int, done: bool) -> dict:
        return self._request("POST", f"/items/{item_id}/done", json={"done": done})

    def validate_import(self, text: str) -> dict:
        return self._request("POST", "/import/validate", json={"text": text})

    def list_audit(self, checklist_id: int | None = None, limit: int = 100) -> list[dict]:
        params: dict = {"limit": limit}
        if checklist_id is not None:
            params["checklist_id"] = checklist_id
        return self._request("GET", "/audit", params=params)
