from __future__ import annotations

import logging
from typing import Any

from .base import ScraperBase

LOGGER = logging.getLogger(__name__)


class InstagramScraper(ScraperBase):
    """Platzhalter für Instagram-Scraping via API oder Automation."""

    def __init__(self, session: Any | None = None) -> None:
        self.session = session

    def authenticate(self) -> None:
        LOGGER.info("InstagramScraper: Authentifizierung noch nicht implementiert.")
        raise NotImplementedError("Instagram-Login noch zu implementieren.")

    def scrape(self, target_dir: str) -> list[str]:
        LOGGER.info("InstagramScraper: Scraping noch nicht implementiert.")
        raise NotImplementedError("Instagram-Scraping folgt in einer späteren Iteration.")

