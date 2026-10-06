"""Read final_cases.json: which case of each joint model is the current final version."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
REGISTRY = PROJECT / "final_cases.json"


def load() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def case(model: str) -> str:
    """Final case folder name of a model key in final_cases.json (e.g. 'solid', 'shell_history')."""
    return load()[model]["case"]


def raw(model: str) -> str:
    """Raw-export folder name (the shell's raw folders are named differently from its processed ones)."""
    entry = load()[model]
    return entry.get("raw", entry["case"])


def ppt_folder() -> Path:
    return PROJECT / load()["ppt_folder"]
