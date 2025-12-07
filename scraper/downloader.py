from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable
from uuid import uuid4

import requests

LOGGER = logging.getLogger(__name__)

CHUNK_SIZE = 2 ** 20  # 1 MB


def download_media(url: str, target_dir: str) -> str:
    """Lädt eine Mediendatei herunter und speichert sie lokal."""
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid4().hex}.mp4"
    target_path = Path(target_dir) / file_name

    LOGGER.debug("Download: %s -> %s", url, target_path)

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with target_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    file.write(chunk)

    return target_path.as_posix()


def bulk_download(urls: Iterable[str], target_dir: str) -> list[str]:
    """Lädt mehrere URLs herunter und gibt lokale Pfade zurück."""
    paths: list[str] = []
    for url in urls:
        try:
            paths.append(download_media(url, target_dir))
        except requests.RequestException as exc:
            LOGGER.warning("Download fehlgeschlagen (%s): %s", url, exc)
    return paths

