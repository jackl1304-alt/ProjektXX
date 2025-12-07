"""Pytest-Konfiguration und Fixtures."""

import pytest
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Erstellt ein temporäres Verzeichnis für Tests.
    
    Yields:
        Path zum temporären Verzeichnis
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_settings() -> Dict[str, Any]:
    """Erstellt eine Test-Settings-Konfiguration.
    
    Returns:
        Test-Settings Dictionary
    """
    return {
        "video_folder": "./output",
        "temp_folder": "./temp",
        "reddit_subreddits": ["memes"],
        "reddit_limit": 5,
        "render_vertical": True,
        "render_video_bitrate": "6000k",
        "render_audio_bitrate": "192k",
        "render_preset": "medium",
        "render_padding_color": "black",
        "render_intro_path": "",
        "render_outro_path": "",
        "output_filename_template": "final_{timestamp}.mp4",
        "hashtags": ["memes", "compilation"],
        "default_title": "Test Compilation",
        "description_template": "Test Description",
        "youtube_privacy_status": "private",
        "youtube_category_id": "24",
        "youtube_credentials_path": "./config/client_secret.json",
        "youtube_token_path": "./config/token.json",
    }


@pytest.fixture
def mock_video_path(temp_dir: Path) -> Path:
    """Erstellt eine Mock-Video-Datei.
    
    Args:
        temp_dir: Temporäres Verzeichnis
        
    Returns:
        Path zur Mock-Video-Datei
    """
    video_file = temp_dir / "test_video.mp4"
    video_file.write_text("mock_video_data")
    return video_file
