from __future__ import annotations

import logging
from pathlib import Path

LOG_PATH = Path("./logs/autopublisher.log")
LOG_PATH.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def log_event(message: str) -> None:
    logging.getLogger("autopublisher").info(message)

