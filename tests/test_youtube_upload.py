"""Unit-Tests für YouTube-Upload-Modul."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from upload.youtube import (
    upload_to_youtube,
    _load_credentials,
    _validate_video_file,
    _upload_with_retry,
    YouTubeUploadError,
    YouTubeAuthError,
)


class TestValidateVideoFile:
    """Tests für _validate_video_file Funktion."""

    def test_validate_video_file_exists(self, mock_video_path: Path) -> None:
        """Test Validierung existierende Video-Datei."""
        result = _validate_video_file(str(mock_video_path))
        assert result == mock_video_path

    def test_validate_video_file_not_found(self) -> None:
        """Test Fehler bei nicht-existierende Datei."""
        with pytest.raises(YouTubeUploadError, match="nicht gefunden"):
            _validate_video_file("/nonexistent/video.mp4")

    def test_validate_video_file_empty(self, temp_dir: Path) -> None:
        """Test Fehler bei leerer Datei."""
        empty_file = temp_dir / "empty.mp4"
        empty_file.write_text("")

        with pytest.raises(YouTubeUploadError, match="leer"):
            _validate_video_file(str(empty_file))

    def test_validate_video_file_is_directory(self, temp_dir: Path) -> None:
        """Test Fehler wenn Pfad ein Verzeichnis ist."""
        with pytest.raises(YouTubeUploadError, match="keine Datei"):
            _validate_video_file(str(temp_dir))


class TestLoadCredentials:
    """Tests für _load_credentials Funktion."""

    @patch("upload.youtube.Credentials.from_authorized_user_file")
    def test_load_credentials_from_cache(
        self, mock_from_file: Mock, sample_settings: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test Laden von gecachten Credentials."""
        # Setup
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_from_file.return_value = mock_creds

        token_path = temp_dir / "token.json"
        token_path.write_text('{"token": "test"}')

        settings = {
            **sample_settings,
            "youtube_token_path": str(token_path),
        }

        # Ausführung
        result = _load_credentials(settings)

        # Assertions
        assert result == mock_creds
        mock_from_file.assert_called_once()

    @patch("upload.youtube.InstalledAppFlow")
    def test_load_credentials_needs_auth(
        self, mock_flow_class: Mock, sample_settings: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test neue Authentifizierung wenn Token fehlt."""
        # Setup
        mock_flow = MagicMock()
        mock_creds = MagicMock()
        mock_flow.run_console.return_value = mock_creds
        mock_creds.to_json.return_value = '{"token": "test"}'
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        creds_path = temp_dir / "client_secret.json"
        creds_path.write_text('{"client_id": "test"}')

        token_path = temp_dir / "token.json"

        settings = {
            **sample_settings,
            "youtube_credentials_path": str(creds_path),
            "youtube_token_path": str(token_path),
        }

        # Ausführung
        with patch("upload.youtube.Path.exists", return_value=False):
            result = _load_credentials(settings)

        # Assertions
        assert result == mock_creds

    def test_load_credentials_missing_credentials_file(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler bei fehlender Credentials-Datei."""
        settings = {
            **sample_settings,
            "youtube_credentials_path": "/nonexistent/client_secret.json",
        }

        with pytest.raises(YouTubeAuthError, match="nicht gefunden"):
            _load_credentials(settings)


class TestUploadToYoutube:
    """Tests für upload_to_youtube Funktion."""

    @patch("upload.youtube._load_credentials")
    @patch("upload.youtube._validate_video_file")
    @patch("upload.youtube._upload_with_retry")
    @patch("upload.youtube.build")
    def test_upload_to_youtube_success(
        self,
        mock_build: Mock,
        mock_upload_retry: Mock,
        mock_validate: Mock,
        mock_load_creds: Mock,
        sample_settings: Dict[str, Any],
        mock_video_path: Path,
    ) -> None:
        """Test erfolgreicher Upload."""
        # Setup
        mock_creds = MagicMock()
        mock_load_creds.return_value = mock_creds
        mock_validate.return_value = mock_video_path
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Ausführung
        upload_to_youtube(str(mock_video_path), sample_settings)

        # Assertions
        mock_validate.assert_called_once()
        mock_load_creds.assert_called_once()
        mock_upload_retry.assert_called_once()

    @patch("upload.youtube._validate_video_file")
    def test_upload_to_youtube_invalid_file(
        self, mock_validate: Mock, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler bei ungültiger Datei."""
        mock_validate.side_effect = YouTubeUploadError("File not found")

        with pytest.raises(YouTubeUploadError):
            upload_to_youtube("/nonexistent/video.mp4", sample_settings)

    @patch("upload.youtube._load_credentials")
    @patch("upload.youtube._validate_video_file")
    def test_upload_to_youtube_auth_error(
        self,
        mock_validate: Mock,
        mock_load_creds: Mock,
        sample_settings: Dict[str, Any],
        mock_video_path: Path,
    ) -> None:
        """Test Fehlerbehandlung bei Auth-Fehler."""
        mock_validate.return_value = mock_video_path
        mock_load_creds.side_effect = YouTubeAuthError("Auth failed")

        with pytest.raises(YouTubeAuthError):
            upload_to_youtube(str(mock_video_path), sample_settings)
