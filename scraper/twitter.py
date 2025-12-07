from __future__ import annotations

import logging
from typing import Any

from .base import ScraperBase

LOGGER = logging.getLogger(__name__)


class TwitterScraper(ScraperBase):
    """Platzhalter für X/Twitter-Scraping."""

    def __init__(self, bearer_token: str | None = None) -> None:
        self.bearer_token = bearer_token

    def authenticate(self) -> None:
        LOGGER.info("TwitterScraper: Authentifizierung noch nicht implementiert.")
        raise NotImplementedError("Twitter-Auth folgt in späterer Iteration.")

    def scrape(self, target_dir: str) -> list[str]:
        LOGGER.info("TwitterScraper: Scraping noch nicht implementiert.")
        raise NotImplementedError("Twitter-Scraping folgt in späterer Iteration.")

