"""``runtime.json`` read/write (TECH_SPEC §9 E3).

Holds only the ephemeral port the local server bound to, so the CLI (and any client)
can discover where the running app listens.
"""

from __future__ import annotations

import json
from pathlib import Path


def write_runtime(path: str | Path, port: int) -> None:
    Path(path).write_text(json.dumps({"port": port}), encoding="utf-8")


def read_port(path: str | Path) -> int:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return int(data["port"])
