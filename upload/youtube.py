"""YouTube-Upload-Modul mit Authentifizierung und Fehlerbehandlung.

Dieses Modul bietet Funktionen zum Hochladen von Videos auf YouTube
mit automatischem Token-Refresh, Retry-Mechanismen und strukturiertem Logging.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth.exceptions

from automation.logger import log_event

logger = logging.getLogger(__name__)

SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube.upload"]
BUNDLE_NAME: str = "SocialVideoAutoPublisher"
MAX_RETRIES: int = 3
RETRY_DELAY: int = 5  # Sekunden
TIMEOUT: int = 300  # 5 Minuten für Upload-Timeout


class YouTubeUploadError(Exception):
    """Exception für YouTube-Upload-Fehler."""

    pass


class YouTubeAuthError(YouTubeUploadError):
    """Exception für YouTube-Authentifizierungsfehler."""

    pass


def _load_credentials(settings: dict[str, Any]) -> Credentials:
    """Lädt oder aktualisiert YouTube-OAuth2-Credentials.

    Verwaltet Token-Caching und automatisches Refresh. Unterstützt:
    - Token-Caching in Dateisystem
    - Automatisches Token-Refresh bei Ablauf
    - Neue Authentifizierung bei ungültigen Tokens

    Args:
        settings: Konfigurationsdictionary mit Keys:
            - youtube_credentials_path (str): Pfad zur credentials.json
            - youtube_token_path (str): Pfad zur gecachten token.json

    Returns:
        Authentifizierte Google OAuth2 Credentials

    Raises:
        YouTubeAuthError: Bei Authentifizierungsfehler
    """
    credentials_path = settings.get(
        "youtube_credentials_path", "./config/client_secret.json"
    )
    token_path = settings.get("youtube_token_path", "./config/token.json")

    logger.debug(f"YouTube-Credentials-Pfad: {credentials_path}")
    logger.debug(f"YouTube-Token-Pfad: {token_path}")

    creds: Optional[Credentials] = None

    # Versuche gecachten Token zu laden
    try:
        if Path(token_path).exists():
            logger.debug("Versuche gespeicherten Token zu laden")
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            logger.debug("Token erfolgreich geladen")
    except Exception as exc:
        logger.warning(
            f"Fehler beim Laden des gecachten Tokens: {exc} - Neue Auth erforderlich"
        )
        creds = None

    # Token validieren/aktualisieren oder neu authentifizieren
    try:
        if creds and creds.valid:
            logger.info("YouTube-Token gültig")
            return creds

        if creds and creds.expired and creds.refresh_token:
            logger.info("YouTube-Token abgelaufen, aktualisiere...")
            creds.refresh(Request())
            logger.info("YouTube-Token erfolgreich aktualisiert")
        else:
            logger.info("Starte neue YouTube-Authentifizierung")
            if not Path(credentials_path).exists():
                error_msg = (
                    f"Credentials-Datei nicht gefunden: {credentials_path}. "
                    f"Bitte herunterladen von https://console.cloud.google.com"
                )
                logger.error(error_msg)
                raise YouTubeAuthError(error_msg)

            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_console()
            logger.info("Neue Authentifizierung erfolgreich")

        # Token cachen
        try:
            token_file_path = Path(token_path)
            token_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_file_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
            logger.debug(f"Token gecacht in {token_path}")
        except Exception as exc:
            logger.warning(f"Token-Caching fehlgeschlagen (nicht kritisch): {exc}")

        return creds

    except google.auth.exceptions.GoogleAuthError as exc:
        error_msg = f"Google-Authentifizierungsfehler: {exc}"
        logger.error(error_msg, exc_info=True)
        raise YouTubeAuthError(error_msg) from exc
    except Exception as exc:
        error_msg = f"Unerwarteter Fehler bei YouTube-Authentifizierung: {exc}"
        logger.error(error_msg, exc_info=True)
        raise YouTubeAuthError(error_msg) from exc


def _validate_video_file(video_path: str) -> Path:
    """Validiert dass die Video-Datei existiert und lesbar ist.

    Args:
        video_path: Pfad zur Video-Datei

    Returns:
        Path-Objekt der Video-Datei

    Raises:
        YouTubeUploadError: Wenn Datei nicht existiert oder nicht lesbar
    """
    video_file = Path(video_path)

    if not video_file.exists():
        error_msg = f"Video-Datei nicht gefunden: {video_path}"
        logger.error(error_msg)
        raise YouTubeUploadError(error_msg)

    if not video_file.is_file():
        error_msg = f"Pfad ist keine Datei: {video_path}"
        logger.error(error_msg)
        raise YouTubeUploadError(error_msg)

    if not video_file.stat().st_size > 0:
        error_msg = f"Video-Datei ist leer: {video_path}"
        logger.error(error_msg)
        raise YouTubeUploadError(error_msg)

    file_size_mb = video_file.stat().st_size / (1024 * 1024)
    logger.info(f"Video-Datei validiert: {video_path} ({file_size_mb:.1f} MB)")

    return video_file


def upload_to_youtube(video_path: str, settings: dict[str, Any]) -> None:
    """Lädt ein Video auf YouTube hoch mit Retry-Mechanismus.

    Orchestriert den kompletten Upload-Prozess:
    1. Validiert Video-Datei
    2. Authentifiziert mit YouTube-API
    3. Erstellt Video-Metadaten aus Settings
    4. Lädt mit Retry bei transienten Fehlern hoch

    Args:
        video_path: Pfad zur hochzuladenden Video-Datei
        settings: Konfigurationsdictionary mit Keys:
            - default_title (str): Video-Titel
            - description_template (str): Video-Beschreibung
            - hashtags (list[str]): Tags für das Video
            - youtube_category_id (str): YouTube-Kategorie-ID
            - youtube_privacy_status (str): Privatsphäre-Status
            - youtube_credentials_path (str): Pfad zur credentials.json
            - youtube_token_path (str): Pfad zur token.json

    Raises:
        YouTubeUploadError: Bei kritischen Upload-Fehlern nach Retries
        YouTubeAuthError: Bei Authentifizierungsfehlern

    Logs:
        INFO: Upload-Status und Meilensteine
        WARNING: Transiente Fehler bei Retries
        ERROR: Kritische Upload-Fehler
    """
    logger.info(f"Starte YouTube-Upload für {video_path}")
    log_event("YouTube: Upload gestartet")

    try:
        # Schritt 1: Video-Datei validieren
        video_file = _validate_video_file(video_path)

        # Schritt 2: Authentifizieren
        logger.debug("Authentifiziere mit YouTube-API")
        creds = _load_credentials(settings)

        # Schritt 3: YouTube-Service erstellen
        logger.debug("Erstelle YouTube-API-Service")
        youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

        # Schritt 4: Metadaten vorbereiten
        title = settings.get("default_title", "Automated Compilation")
        description = settings.get(
            "description_template", "Automatisiert generierte Compilation."
        )
        tags = settings.get("hashtags", [])
        category_id = settings.get("youtube_category_id", "24")
        privacy_status = settings.get("youtube_privacy_status", "private")

        logger.debug(f"Video-Titel: {title}")
        logger.debug(f"Privatsphäre: {privacy_status}")

        body: dict[str, Any] = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Schritt 5: Upload mit Retry-Mechanismus
        media = MediaFileUpload(
            video_file.as_posix(), chunksize=-1, resumable=True
        )
        _upload_with_retry(youtube, body, media, video_file)

    except (YouTubeUploadError, YouTubeAuthError):
        raise
    except Exception as exc:
        error_msg = f"Unerwarteter Fehler bei YouTube-Upload: {exc}"
        logger.error(error_msg, exc_info=True)
        log_event(f"YouTube: Unerwarteter Fehler ({exc})")
        raise YouTubeUploadError(error_msg) from exc


def _upload_with_retry(
    youtube: Any, body: dict[str, Any], media: MediaFileUpload, video_file: Path
) -> None:
    """Führt YouTube-Upload mit Retry-Logik durch.

    Implementiert exponentielles Backoff für transiente Fehler:
    - Netzwerkfehler (ConnectionError, Timeout)
    - Rate-Limiting (429)
    - Server-Fehler (500-599)

    Permanente Fehler werden sofort weitergeleitet.

    Args:
        youtube: Google YouTube API Service
        body: Video-Metadaten
        media: MediaFileUpload-Objekt
        video_file: Path-Objekt der Video-Datei

    Raises:
        YouTubeUploadError: Bei kritischen Upload-Fehlern
    """
    last_exception: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"YouTube-Upload-Versuch {attempt}/{MAX_RETRIES} für {video_file.name}"
            )
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            response = None

            while response is None:
                _, response = request.next_chunk()

            video_id = response.get("id")
            logger.info(f"YouTube-Upload erfolgreich abgeschlossen (Video-ID: {video_id})")
            log_event(f"YouTube: Upload abgeschlossen ({video_id})")
            return

        except HttpError as exc:
            last_exception = exc
            error_code = exc.resp.status

            # Permanente Fehler (4xx außer 429, 408)
            if error_code < 500 and error_code not in (429, 408):
                error_msg = f"Permanenter YouTube-Fehler ({error_code}): {exc}"
                logger.error(error_msg)
                log_event(f"YouTube: Permanenter Fehler {error_code}")
                raise YouTubeUploadError(error_msg) from exc

            # Transiente Fehler (5xx, 429, 408)
            is_last_attempt = attempt == MAX_RETRIES
            if is_last_attempt:
                error_msg = f"YouTube-Upload nach {MAX_RETRIES} Versuchen fehlgeschlagen: {exc}"
                logger.error(error_msg, exc_info=True)
                log_event(
                    f"YouTube: Upload nach {MAX_RETRIES} Versuchen fehlgeschlagen"
                )
                raise YouTubeUploadError(error_msg) from exc

            wait_time = RETRY_DELAY * (2 ** (attempt - 1))  # Exponentielles Backoff
            logger.warning(
                f"Transienter YouTube-Fehler ({error_code}). "
                f"Retry nach {wait_time}s (Versuch {attempt}/{MAX_RETRIES}): {exc}"
            )
            time.sleep(wait_time)

        except (ConnectionError, TimeoutError) as exc:
            last_exception = exc
            is_last_attempt = attempt == MAX_RETRIES

            if is_last_attempt:
                error_msg = (
                    f"Netzwerkfehler nach {MAX_RETRIES} Versuchen: {exc}"
                )
                logger.error(error_msg, exc_info=True)
                log_event(f"YouTube: Netzwerkfehler nach {MAX_RETRIES} Versuchen")
                raise YouTubeUploadError(error_msg) from exc

            wait_time = RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning(
                f"Netzwerkfehler. Retry nach {wait_time}s "
                f"(Versuch {attempt}/{MAX_RETRIES}): {exc}"
            )
            time.sleep(wait_time)

