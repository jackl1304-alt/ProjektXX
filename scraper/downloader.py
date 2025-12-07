"""Media-Download-Modul mit Retry-Mechanismus und Fehlerbehandlung."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Iterable, Optional
from uuid import uuid4

import requests

logger = logging.getLogger(__name__)

CHUNK_SIZE: int = 2 ** 20  # 1 MB
MAX_RETRIES: int = 3
RETRY_DELAY: int = 5  # Sekunden
TIMEOUT: int = 60  # Sekunden für Download-Timeout


class DownloadError(Exception):
    """Exception für Download-Fehler."""

    pass


def download_media(url: str, target_dir: str, max_retries: int = MAX_RETRIES) -> str:
    """Lädt eine Mediendatei herunter mit Retry-Mechanismus.

    Implementiert exponentielles Backoff und differenziert zwischen
    transienten und permanenten Fehlern.

    Args:
        url: Download-URL
        target_dir: Zielverzeichnis für die Datei
        max_retries: Maximale Anzahl Wiederholungen bei transienten Fehlern

    Returns:
        Pfad zur heruntergeladenen Datei

    Raises:
        DownloadError: Bei permanenten oder wiederholten transienten Fehlern

    Logs:
        DEBUG: Download-Anfang und Chunk-Verarbeitung
        INFO: Erfolgreiche Downloads
        WARNING: Transiente Fehler mit Retry-Versuch
        ERROR: Permanente Fehler
    """
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid4().hex}.mp4"
    target_path = Path(target_dir) / file_name

    logger.debug(f"Starte Download: {url} → {target_path}")

    for attempt in range(1, max_retries + 1):
        try:
            with requests.get(
                url, stream=True, timeout=TIMEOUT
            ) as response:
                response.raise_for_status()

                file_size = 0
                with target_path.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            file.write(chunk)
                            file_size += len(chunk)

                logger.info(
                    f"Download erfolgreich: {url} ({file_size / (1024*1024):.1f} MB) "
                    f"→ {target_path.name}"
                )
                return target_path.as_posix()

        except requests.exceptions.Timeout as exc:
            is_last = attempt == max_retries
            if is_last:
                error_msg = f"Download-Timeout nach {max_retries} Versuchen: {url}"
                logger.error(error_msg)
                raise DownloadError(error_msg) from exc

            wait_time = RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"Download-Timeout für {url}. Retry nach {wait_time}s "
                f"(Versuch {attempt}/{max_retries})"
            )
            time.sleep(wait_time)

        except requests.exceptions.ConnectionError as exc:
            is_last = attempt == max_retries
            if is_last:
                error_msg = f"Netzwerkfehler nach {max_retries} Versuchen: {url}"
                logger.error(error_msg)
                raise DownloadError(error_msg) from exc

            wait_time = RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"Netzwerkfehler für {url}. Retry nach {wait_time}s "
                f"(Versuch {attempt}/{max_retries})"
            )
            time.sleep(wait_time)

        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code

            # Permanente Fehler (4xx außer 408)
            if status_code < 500 and status_code != 408:
                error_msg = f"Permanenter HTTP-Fehler {status_code}: {url}"
                logger.error(error_msg)
                # Datei löschen wenn teilweise heruntergeladen
                if target_path.exists():
                    target_path.unlink()
                raise DownloadError(error_msg) from exc

            # Transiente Fehler (5xx, 408)
            is_last = attempt == max_retries
            if is_last:
                error_msg = (
                    f"HTTP-Fehler {status_code} nach {max_retries} Versuchen: {url}"
                )
                logger.error(error_msg)
                if target_path.exists():
                    target_path.unlink()
                raise DownloadError(error_msg) from exc

            wait_time = RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"HTTP-Fehler {status_code} für {url}. Retry nach {wait_time}s "
                f"(Versuch {attempt}/{max_retries})"
            )
            if target_path.exists():
                target_path.unlink()
            time.sleep(wait_time)

        except Exception as exc:
            error_msg = f"Unerwarteter Download-Fehler: {url} - {exc}"
            logger.error(error_msg, exc_info=True)
            if target_path.exists():
                target_path.unlink()
            raise DownloadError(error_msg) from exc

    # Sollte nicht erreicht werden, aber für Sicherheit
    raise DownloadError(f"Download fehlgeschlagen nach {max_retries} Versuchen: {url}")


def bulk_download(
    urls: Iterable[str], target_dir: str, skip_on_error: bool = True
) -> list[str]:
    """Lädt mehrere URLs herunter mit Fehlerbehandlung.

    Args:
        urls: Iterable mit Download-URLs
        target_dir: Zielverzeichnis für alle Dateien
        skip_on_error: Bei True: Fehler überspringen und weitermachen
                      Bei False: Beim ersten Fehler abbrechen

    Returns:
        Liste mit lokalen Pfaden erfolgreich heruntergeladener Dateien

    Raises:
        DownloadError: Bei skip_on_error=False und Download-Fehler

    Logs:
        INFO: Anzahl gelöster/fehlgeschlagener Downloads
        WARNING: Download-Fehler (wenn skip_on_error=True)
    """
    paths: list[str] = []
    failed_urls: list[tuple[str, str]] = []

    for url in urls:
        try:
            path = download_media(url, target_dir)
            paths.append(path)
        except DownloadError as exc:
            if not skip_on_error:
                raise
            logger.warning(f"Download übersprungen: {url} ({exc})")
            failed_urls.append((url, str(exc)))

    logger.info(
        f"Bulk-Download abgeschlossen: {len(paths)} erfolgreich, "
        f"{len(failed_urls)} übersprungen"
    )

    if failed_urls:
        logger.debug(f"Fehlgeschlagene Downloads: {failed_urls}")

    return paths

