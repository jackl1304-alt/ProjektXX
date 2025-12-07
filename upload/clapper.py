from __future__ import annotations

import logging
from typing import Any

from automation.logger import log_event

LOGGER = logging.getLogger(__name__)


def upload_to_clapper(video_path: str, settings: dict[str, Any]) -> None:
    """Stub für Clapper-Uploads via Selenium."""
    LOGGER.info("Clapper: Upload-Stub aufgerufen für %s", video_path)
    log_event("Clapper: Upload-Stub – Implementierung erforderlich.")
    raise NotImplementedError(
        "Implementiere Clapper-Upload (Empfehlung: Selenium + Headless-Chromium mit gespeicherten Cookies)."
    )

