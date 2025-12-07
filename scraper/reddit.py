from __future__ import annotations

import logging
from typing import Any, Iterable, Sequence

import requests

from .base import ScraperBase
from .downloader import bulk_download

LOGGER = logging.getLogger(__name__)


class RedditScraper(ScraperBase):
    """Scraper für Reddit-Memes über die öffentliche JSON-API."""

    def __init__(self, subreddit: str | Sequence[str] = "memes", limit: int = 10) -> None:
        if isinstance(subreddit, str):
            self.subreddits: list[str] = [subreddit]
        else:
            self.subreddits = [sub.strip() for sub in subreddit if sub]
        if not self.subreddits:
            raise ValueError("RedditScraper: Mindestens ein Subreddit muss angegeben werden.")
        self.limit = limit

    def authenticate(self) -> None:
        """Reddit-Topfeed benötigt keine Authentifizierung."""
        LOGGER.debug("RedditScraper: keine Authentifizierung erforderlich.")

    def _fetch_urls(self) -> Iterable[str]:
        videos: list[str] = []
        headers = {"User-Agent": "Mozilla/5.0 SocialVideoAutoPublisher/0.1"}
        per_subreddit_limit = max(1, self.limit // len(self.subreddits)) if len(self.subreddits) > 1 else self.limit

        for subreddit in self.subreddits:
            url = (
                f"https://www.reddit.com/r/{subreddit}/top.json"
                f"?limit={per_subreddit_limit}&t=day&raw_json=1"
            )
            LOGGER.info("RedditScraper: Fetch %s", url)

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data: dict[str, Any] = response.json()

            for child in data.get("data", {}).get("children", []):
                post_data: dict[str, Any] = child.get("data", {})
                url_value = post_data.get("url")
                if isinstance(url_value, str) and url_value.endswith(".mp4"):
                    videos.append(url_value)
                    continue

                fallback_url = self._extract_fallback_url(post_data)
                if fallback_url:
                    videos.append(fallback_url)

                if len(videos) >= self.limit:
                    break

            if len(videos) >= self.limit:
                break

        LOGGER.info("RedditScraper: %s Video-URLs gefunden", len(videos))
        return videos[: self.limit]

    @staticmethod
    def _extract_fallback_url(post_data: dict[str, Any]) -> str | None:
        """Extrahiert die beste MP4-Fallback-URL aus Reddit-Postdaten."""
        candidates = [
            post_data.get("secure_media"),
            post_data.get("media"),
            post_data.get("preview"),
        ]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            reddit_video = candidate.get("reddit_video") or candidate.get("reddit_video_preview")
            if not isinstance(reddit_video, dict):
                continue
            fallback = reddit_video.get("fallback_url")
            if isinstance(fallback, str) and fallback.startswith("http"):
                return fallback
        return None

    def scrape(self, target_dir: str) -> list[str]:
        """Lädt Top-Videos und speichert sie lokal."""
        urls = self._fetch_urls()
        downloads = bulk_download(urls, target_dir)
        LOGGER.info("RedditScraper: %s Videos heruntergeladen", len(downloads))
        return downloads

