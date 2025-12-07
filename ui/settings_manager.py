from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_PATH = Path("./config/settings.json")


def load_settings() -> dict[str, Any]:
    with SETTINGS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_settings(data: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

