"""Update-check logic tests (issue #81): version compare + GitHub release parsing.

No real network: an ``httpx.MockTransport`` drives :func:`check_for_update`.
"""

from __future__ import annotations

import httpx
import pytest

from receipt_board.core import updates
from receipt_board.core.updates import (
    build_update_info,
    check_for_update,
    is_newer,
    parse_version,
    select_installer_asset,
)


def test_parse_version_strips_v_and_suffix():
    assert parse_version("v1.4.0") == (1, 4, 0)
    assert parse_version("1.4.0-rc1") == (1, 4, 0)
    assert parse_version("2.0") == (2, 0)
    assert parse_version("garbage") == (0,)


@pytest.mark.parametrize(
    ("latest", "current", "expected"),
    [
        ("1.4.0", "1.3.0", True),
        ("1.3.1", "1.3.0", True),
        ("1.3.0", "1.3.0", False),
        ("1.2.0", "1.3.0", False),
        ("v1.10.0", "1.9.0", True),
    ],
)
def test_is_newer(latest, current, expected):
    assert is_newer(latest, current) is expected


def _release(tag: str = "v1.4.0", *, with_asset: bool = True) -> dict:
    base = "https://github.com/automatix/receipt-board/releases"
    assets: list[dict] = []
    if with_asset:
        assets = [
            {"name": "notes.txt", "browser_download_url": "https://x/notes.txt"},
            {
                "name": f"receipt-board-{tag}-setup.exe",
                "browser_download_url": f"{base}/download/{tag}/receipt-board-{tag}-setup.exe",
            },
        ]
    return {"tag_name": tag, "html_url": f"{base}/tag/{tag}", "assets": assets}


def test_select_installer_asset_finds_setup_exe():
    url = select_installer_asset(_release())
    assert url is not None and url.endswith("-setup.exe")


def test_select_installer_asset_none_when_absent():
    assert select_installer_asset(_release(with_asset=False)) is None


def test_build_update_info_available():
    info = build_update_info("1.3.0", _release("v1.4.0"))
    assert info.update_available is True
    assert info.latest == "1.4.0"
    assert info.asset_url is not None and info.asset_url.endswith("-setup.exe")
    assert info.notes_url is not None and info.notes_url.endswith("/tag/v1.4.0")
    assert info.as_dict()["current"] == "1.3.0"


def test_build_update_info_up_to_date():
    info = build_update_info("1.4.0", _release("v1.4.0"))
    assert info.update_available is False
    assert info.current == "1.4.0" and info.latest == "1.4.0"


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_check_for_update_newer_via_mock_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/automatix/receipt-board/releases/latest"
        return httpx.Response(200, json=_release("v1.4.0"))

    with _client(handler) as client:
        info = check_for_update("1.3.0", client=client)
    assert info.update_available is True and info.latest == "1.4.0"


def test_check_for_update_honours_repo_override():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/fork/rb/releases/latest"
        return httpx.Response(200, json=_release("v9.9.9"))

    with _client(handler) as client:
        info = check_for_update("1.3.0", client=client, repo_name="fork/rb")
    assert info.latest == "9.9.9"


def test_check_for_update_raises_on_network_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    with _client(handler) as client, pytest.raises(httpx.HTTPError):
        check_for_update("1.3.0", client=client)


def test_check_for_update_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Not Found"})

    with _client(handler) as client, pytest.raises(httpx.HTTPStatusError):
        check_for_update("1.3.0", client=client)


def test_repo_env_override(monkeypatch):
    monkeypatch.setenv(updates.ENV_REPO, "fork/rb")
    assert updates.repo() == "fork/rb"
    monkeypatch.delenv(updates.ENV_REPO, raising=False)
    assert updates.repo() == updates.DEFAULT_REPO


# -- download / launch (issue #82) --------------------------------------------


def test_is_trusted_asset_url():
    base = "https://github.com/automatix/receipt-board/releases/download/v1.4.0"
    assert updates.is_trusted_asset_url(f"{base}/receipt-board-v1.4.0-setup.exe")
    assert updates.is_trusted_asset_url("https://objects.githubusercontent.com/x")
    assert not updates.is_trusted_asset_url("https://evil.example.com/x-setup.exe")
    assert not updates.is_trusted_asset_url("https://github.com.evil.com/x-setup.exe")


def test_download_installer_writes_file(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"INSTALLER-BYTES")

    url = (
        "https://github.com/automatix/receipt-board/releases/download/"
        "v1.4.0/receipt-board-v1.4.0-setup.exe"
    )
    with _client(handler) as client:
        dest = updates.download_installer(url, tmp_path / "updates", client=client)
    assert dest.name == "receipt-board-v1.4.0-setup.exe"
    assert dest.read_bytes() == b"INSTALLER-BYTES"


def test_download_installer_raises_on_http_error(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    with _client(handler) as client, pytest.raises(httpx.HTTPStatusError):
        updates.download_installer("https://github.com/x/setup.exe", tmp_path, client=client)


def test_launch_installer_invokes_popen(monkeypatch, tmp_path):
    calls: dict = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            calls["args"] = args
            calls["kwargs"] = kwargs

    monkeypatch.setattr(updates.subprocess, "Popen", FakePopen)
    path = tmp_path / "receipt-board-setup.exe"
    path.write_text("x")
    updates.launch_installer(path)
    assert calls["args"] == [str(path)]
    assert calls["kwargs"]["close_fds"] is True
