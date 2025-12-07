from __future__ import annotations

import logging
from typing import Any

from automation.logger import log_event

LOGGER = logging.getLogger(__name__)


def upload_to_tiktok(video_path: str, settings: dict[str, Any]) -> None:
    """Stub für TikTok-Uploads via Appium oder offizielle API."""
    LOGGER.info("TikTok: Upload-Stub aufgerufen für %s", video_path)
    log_event("TikTok: Upload-Stub – Implementierung erforderlich.")
    raise NotImplementedError(
        "Implementiere TikTok-Upload (Empfehlung: Appium + Emulator oder TikTok-API für Business-Konten)."
    )

