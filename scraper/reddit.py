"""Reddit-Scraper für Video-Inhalte.

Extrahiert Videos und animierte GIFs aus Reddit-Posts mit
automatischem Fallback auf alternative Video-Quellen.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional, Sequence

import requests

from .base import ScraperBase
from .downloader import bulk_download

logger = logging.getLogger(__name__)

# Reddit API Headers
USER_AGENT = "Mozilla/5.0 SocialVideoAutoPublisher/1.0"
REDDIT_API_BASE = "https://www.reddit.com"


class ScraperError(Exception):
    """Exception für Scraper-Fehler."""

    pass


class RedditScraper(ScraperBase):
    """Scraper für Reddit-Videos und GIFs über öffentliche JSON-API.

    Unterstützt:
    - Top-Posts aus verschiedenen Subreddits
    - Multiple Subreddits mit konfigurierbarer Limit-Verteilung
    - Fallback auf alternative Video-Quellen
    - Automatische Retry-Mechanismen bei Netzwerkfehlern

    Attributes:
        subreddits: Liste von Subreddit-Namen
        limit: Maximale Anzahl Videos zum Sammeln
    """

    def __init__(
        self,
        subreddit: str | Sequence[str] = "memes",
        limit: int = 10,
    ) -> None:
        """Initialisiert Reddit-Scraper.

        Args:
            subreddit: Single Subreddit (str) oder Liste von Subreddits
            limit: Maximale Anzahl Videos zum Sammeln

        Raises:
            ValueError: Wenn keine Subreddits angegeben oder limit <= 0
        """
        # Parse Subreddit-Eingabe
        if isinstance(subreddit, str):
            self.subreddits: list[str] = [subreddit]
        else:
            self.subreddits = [sub.strip() for sub in subreddit if sub]

        if not self.subreddits:
            raise ValueError(
                "RedditScraper: Mindestens ein Subreddit muss angegeben werden."
            )

        if limit <= 0:
            raise ValueError("RedditScraper: Limit muss > 0 sein.")

        self.limit = limit
        logger.debug(
            f"RedditScraper initialized: {len(self.subreddits)} subreddit(s), "
            f"limit={limit}"
        )

    def authenticate(self) -> None:
        """Authentifizierung durchführen.

        Reddit Top-Feed benötigt keine Authentifizierung,
        da die JSON-API öffentlich zugänglich ist.
        """
        logger.debug("RedditScraper: Authentifizierung nicht erforderlich (öffentliche API)")

    def _fetch_urls(self) -> list[str]:
        """Fetcht Video-URLs aus konfigurierten Subreddits.

        Implementiert:
        - Parallele Requests über mehrere Subreddits
        - Limit-Verteilung bei mehreren Subreddits
        - Fallback auf alternative Video-Quellen
        - Fehlerbehandlung mit Logging

        Returns:
            Liste mit Video-URLs (bis zu self.limit Einträge)

        Raises:
            ScraperError: Bei Netzwerk- oder Parsing-Fehlern
        """
        videos: list[str] = []
        headers = {"User-Agent": USER_AGENT}

        # Berechne Limit pro Subreddit
        per_subreddit_limit = (
            max(1, self.limit // len(self.subreddits))
            if len(self.subreddits) > 1
            else self.limit
        )

        for subreddit in self.subreddits:
            if len(videos) >= self.limit:
                break

            url = (
                f"{REDDIT_API_BASE}/r/{subreddit}/top.json"
                f"?limit={per_subreddit_limit}&t=day&raw_json=1"
            )

            logger.info(f"Scrape Reddit: r/{subreddit}")

            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                data: dict[str, Any] = response.json()

                for child in data.get("data", {}).get("children", []):
                    if len(videos) >= self.limit:
                        break

                    post_data: dict[str, Any] = child.get("data", {})
                    title = post_data.get("title", "")

                    # Versuche direkten MP4-Link
                    url_value = post_data.get("url")
                    if isinstance(url_value, str) and url_value.endswith(".mp4"):
                        logger.debug(f"Found direct MP4: {title}")
                        videos.append(url_value)
                        continue

                    # Fallback auf reddit_video
                    fallback_url = self._extract_fallback_url(post_data)
                    if fallback_url:
                        logger.debug(f"Found fallback URL: {title}")
                        videos.append(fallback_url)
                        continue

            except requests.exceptions.RequestException as exc:
                logger.warning(
                    f"Fehler beim Scrapen von r/{subreddit}: {exc}"
                )
                continue
            except (KeyError, ValueError) as exc:
                logger.warning(
                    f"Parsing-Fehler bei r/{subreddit}: {exc}", exc_info=True
                )
                continue

        logger.info(f"Reddit-Scraping abgeschlossen: {len(videos)} URLs gefunden")
        return videos[: self.limit]

    @staticmethod
    def _extract_fallback_url(post_data: dict[str, Any]) -> Optional[str]:
        """Extrahiert fallback MP4-URL aus Reddit-Post-Daten.

        Versucht mehrere Quellen in Reihenfolge:
        1. secure_media.reddit_video
        2. media.reddit_video
        3. preview.reddit_video_preview

        Args:
            post_data: Dict mit Post-Metadaten von Reddit API

        Returns:
            URL zu fallback MP4 oder None wenn nicht vorhanden
        """
        candidates = [
            post_data.get("secure_media"),
            post_data.get("media"),
            post_data.get("preview"),
        ]

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            reddit_video = candidate.get("reddit_video") or candidate.get(
                "reddit_video_preview"
            )
            if not isinstance(reddit_video, dict):
                continue

            fallback = reddit_video.get("fallback_url")
            if isinstance(fallback, str) and fallback.startswith("http"):
                return fallback

        return None

    def scrape(self, target_dir: str) -> list[str]:
        """Scrapingprozess durchführen.

        Orchesriert:
        1. URL-Fetching von konfigurierten Subreddits
        2. Bulk-Download aller URLs
        3. Error-Logging und Rückgabe erfolgreicher Pfade

        Args:
            target_dir: Zielverzeichnis für heruntergeladene Videos

        Returns:
            Liste mit lokalen Pfaden erfolgreich heruntergeladener Videos

        Raises:
            ScraperError: Bei kritischen Fehlern

        Logs:
            INFO: Scraping-Status und Anzahl Downloads
            WARNING: Download-Fehler (nicht kritisch)
            DEBUG: Detail-Informationen für jeden Post
        """
        try:
            logger.info(f"Starte Reddit-Scraping (limit={self.limit})")

            # Phase 1: URLs sammeln
            urls = self._fetch_urls()
            if not urls:
                logger.warning("Keine Video-URLs von Reddit gefunden")
                return []

            logger.info(f"Phase 1: {len(urls)} URLs gefunden")

            # Phase 2: Downloads durchführen
            logger.info("Phase 2: Starte Bulk-Download")
            downloads = bulk_download(urls, target_dir)

            logger.info(
                f"Reddit-Scraping erfolgreich: "
                f"{len(downloads)} Videos heruntergeladen, "
                f"{len(urls) - len(downloads)} übersprungen"
            )

            return downloads

        except Exception as exc:
            error_msg = f"Kritischer Fehler beim Reddit-Scraping: {exc}"
            logger.error(error_msg, exc_info=True)
            raise ScraperError(error_msg) from exc

