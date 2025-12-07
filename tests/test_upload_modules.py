"""Unit-Tests für TikTok und Clapper Upload-Module."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from upload.tiktok import (
    upload_to_tiktok,
    _validate_config as validate_tiktok_config,
    TikTokUploadError,
    TikTokAuthError,
    TikTokNotImplementedError,
)
from upload.clapper import (
    upload_to_clapper,
    _validate_config as validate_clapper_config,
    ClapperUploadError,
    ClapperAuthError,
    ClapperNotImplementedError,
)


class TestTikTokUpload:
    """Tests für TikTok-Upload-Modul."""

    def test_validate_tiktok_config_success(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test erfolgreiche Konfigurationsvalidierung."""
        settings = {
            **sample_settings,
            "tiktok_api_key": "test_key",
            "tiktok_api_secret": "test_secret",
            "tiktok_user_id": "test_user",
        }

        # Sollte keine Exception werfen
        validate_tiktok_config(settings)

    def test_validate_tiktok_config_missing_keys(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler bei fehlenden Konfigurationsschlüsseln."""
        with pytest.raises(TikTokAuthError, match="Fehlende TikTok-Konfiguration"):
            validate_tiktok_config(sample_settings)

    def test_upload_to_tiktok_not_implemented(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test dass TikTok-Upload noch nicht implementiert ist."""
        settings = {
            **sample_settings,
            "tiktok_api_key": "test",
            "tiktok_api_secret": "test",
            "tiktok_user_id": "test",
        }

        with pytest.raises(TikTokNotImplementedError):
            upload_to_tiktok("/path/to/video.mp4", settings)

    def test_upload_to_tiktok_missing_config(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler bei fehlender Konfiguration."""
        with pytest.raises(TikTokAuthError):
            upload_to_tiktok("/path/to/video.mp4", sample_settings)


class TestClapperUpload:
    """Tests für Clapper-Upload-Modul."""

    def test_validate_clapper_config_success(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test erfolgreiche Konfigurationsvalidierung."""
        settings = {
            **sample_settings,
            "clapper_email": "test@example.com",
            "clapper_password": "password",
        }

        # Sollte keine Exception werfen
        validate_clapper_config(settings)

    def test_validate_clapper_config_missing_keys(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler bei fehlenden Konfigurationsschlüsseln."""
        with pytest.raises(ClapperAuthError, match="Fehlende Clapper-Konfiguration"):
            validate_clapper_config(sample_settings)

    def test_upload_to_clapper_not_implemented(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test dass Clapper-Upload noch nicht implementiert ist."""
        settings = {
            **sample_settings,
            "clapper_email": "test@example.com",
            "clapper_password": "password",
        }

        with pytest.raises(ClapperNotImplementedError):
            upload_to_clapper("/path/to/video.mp4", settings)

    def test_upload_to_clapper_missing_config(
        self, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler bei fehlender Konfiguration."""
        with pytest.raises(ClapperAuthError):
            upload_to_clapper("/path/to/video.mp4", sample_settings)


class TestExceptionHierarchy:
    """Tests für Exception-Hierarchien."""

    def test_tiktok_auth_error_is_upload_error(self) -> None:
        """Test Exception-Hierarchie für TikTok."""
        assert issubclass(TikTokAuthError, TikTokUploadError)
        assert issubclass(TikTokNotImplementedError, TikTokUploadError)

    def test_clapper_auth_error_is_upload_error(self) -> None:
        """Test Exception-Hierarchie für Clapper."""
        assert issubclass(ClapperAuthError, ClapperUploadError)
        assert issubclass(ClapperNotImplementedError, ClapperUploadError)
