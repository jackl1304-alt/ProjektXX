from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth.exceptions

from automation.logger import log_event

LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BUNDLE_NAME = "SocialVideoAutoPublisher"


def _load_credentials(settings: dict[str, Any]):
    credentials_path = settings.get("youtube_credentials_path", "./config/client_secret.json")
    token_path = settings.get("youtube_token_path", "./config/token.json")

    creds = None
    if Path(token_path).exists():
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except google.auth.exceptions.GoogleAuthError as exc:
            LOGGER.warning("YouTube: Token ungültig, erneute Auth erforderlich: %s", exc)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_console()
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return creds


def upload_to_youtube(video_path: str, settings: dict[str, Any]) -> None:
    """Lädt ein Video auf YouTube hoch."""
    log_event("YouTube: Upload gestartet")
    creds = _load_credentials(settings)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    body = {
        "snippet": {
            "title": settings.get("default_title", "Automated Compilation"),
            "description": settings.get("description_template", "Automatisiert generierte Compilation."),
            "tags": settings.get("hashtags", []),
            "categoryId": settings.get("youtube_category_id", "24"),
        },
        "status": {
            "privacyStatus": settings.get("youtube_privacy_status", "private"),
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()
        log_event(f"YouTube: Upload abgeschlossen ({response.get('id')})")
    except HttpError as exc:
        LOGGER.error("YouTube: Upload fehlgeschlagen: %s", exc)
        log_event(f"YouTube: Fehler {exc}")
        raise

