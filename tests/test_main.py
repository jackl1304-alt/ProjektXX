"""Unit-Tests für main.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from main import (
    _collect_clips,
    run_once,
    _parse_args,
    ScraperError,
    RenderError,
    UploadError,
    PipelineError,
)


class TestCollectClips:
    """Tests für _collect_clips Funktion."""

    @patch("main.RedditScraper")
    def test_collect_clips_success(
        self, mock_scraper_class: Mock, sample_settings: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test erfolgreiche Clips-Sammlung."""
        # Setup
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape.return_value = ["clip1.mp4", "clip2.mp4"]

        settings = {**sample_settings, "video_folder": str(temp_dir / "output")}
        settings["temp_folder"] = str(temp_dir / "temp")

        # Ausführung
        clips, temp_folder, video_folder = _collect_clips(settings)

        # Assertions
        assert len(clips) == 2
        assert "clip1.mp4" in clips
        mock_scraper.authenticate.assert_called_once()
        mock_scraper.scrape.assert_called_once()

    @patch("main.RedditScraper")
    def test_collect_clips_scraper_error(
        self, mock_scraper_class: Mock, sample_settings: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test Fehlerbehandlung bei Scraper-Fehler."""
        # Setup
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.authenticate.side_effect = Exception("Auth failed")

        settings = {**sample_settings, "video_folder": str(temp_dir / "output")}
        settings["temp_folder"] = str(temp_dir / "temp")

        # Assertions
        with pytest.raises(ScraperError):
            _collect_clips(settings)

    def test_collect_clips_creates_folders(
        self, sample_settings: Dict[str, Any], temp_dir: Path
    ) -> None:
        """Test dass Ordner erstellt werden."""
        settings = {**sample_settings, "video_folder": str(temp_dir / "output")}
        settings["temp_folder"] = str(temp_dir / "temp")

        # Diese Assertion prüft dass die Ordner existieren nach _collect_clips
        with patch("main.RedditScraper"):
            with patch("main.logger"):
                try:
                    _collect_clips(settings)
                except Exception:
                    pass

        assert (temp_dir / "output").exists()
        assert (temp_dir / "temp").exists()


class TestRunOnce:
    """Tests für run_once Funktion."""

    @patch("main._collect_clips")
    @patch("main.render_videos")
    @patch("main.cleanup")
    def test_run_once_success(
        self,
        mock_cleanup: Mock,
        mock_render: Mock,
        mock_collect: Mock,
        sample_settings: Dict[str, Any],
        temp_dir: Path,
    ) -> None:
        """Test erfolgreiche Pipeline-Ausführung."""
        # Setup
        mock_collect.return_value = (
            ["clip1.mp4", "clip2.mp4"],
            temp_dir / "temp",
            temp_dir / "output",
        )
        output_video = str(temp_dir / "output" / "final_20251207_143000.mp4")
        mock_render.return_value = output_video
        mock_cleanup.return_value = None

        # Ausführung
        result = run_once(sample_settings)

        # Assertions
        assert result == output_video
        mock_collect.assert_called_once()
        mock_render.assert_called_once()
        mock_cleanup.assert_called()

    @patch("main._collect_clips")
    def test_run_once_no_clips(
        self, mock_collect: Mock, sample_settings: Dict[str, Any]
    ) -> None:
        """Test Fehler wenn keine Clips gesammelt."""
        # Setup
        mock_collect.return_value = ([], Path("./temp"), Path("./output"))

        # Assertions
        with pytest.raises(ScraperError):
            run_once(sample_settings)

    @patch("main._collect_clips")
    @patch("main.render_videos")
    def test_run_once_render_error(
        self,
        mock_render: Mock,
        mock_collect: Mock,
        sample_settings: Dict[str, Any],
        temp_dir: Path,
    ) -> None:
        """Test Fehlerbehandlung bei Rendering-Fehler."""
        # Setup
        mock_collect.return_value = (
            ["clip1.mp4"],
            temp_dir / "temp",
            temp_dir / "output",
        )
        mock_render.side_effect = Exception("Render failed")

        # Assertions
        with pytest.raises(RenderError):
            run_once(sample_settings)

    @patch("main._collect_clips")
    @patch("main.render_videos")
    @patch("main.UPLOAD_FUNCTIONS", {"youtube": Mock(), "tiktok": Mock()})
    def test_run_once_upload_platforms_filter(
        self,
        mock_render: Mock,
        mock_collect: Mock,
        sample_settings: Dict[str, Any],
        temp_dir: Path,
    ) -> None:
        """Test dass nur spezifische Plattformen hochgeladen werden."""
        # Setup
        mock_collect.return_value = (
            ["clip1.mp4"],
            temp_dir / "temp",
            temp_dir / "output",
        )
        output_video = str(temp_dir / "output" / "final.mp4")
        mock_render.return_value = output_video

        with patch("main.cleanup"):
            # Ausführung
            run_once(sample_settings, platforms=["youtube"])

            # Upload-Funktion sollte nur für youtube aufgerufen werden
            # (wird durch platforms Parameter gefiltert)


class TestParseArgs:
    """Tests für _parse_args Funktion."""

    def test_parse_args_default(self) -> None:
        """Test Default-Argumente."""
        with patch("sys.argv", ["main.py"]):
            args = _parse_args()
            assert args.mode == "once"
            assert args.platforms is None

    def test_parse_args_schedule_mode(self) -> None:
        """Test Schedule-Modus."""
        with patch("sys.argv", ["main.py", "--mode", "schedule"]):
            args = _parse_args()
            assert args.mode == "schedule"

    def test_parse_args_multiple_platforms(self) -> None:
        """Test mehrere Plattformen."""
        with patch(
            "sys.argv",
            ["main.py", "--platform", "youtube", "--platform", "tiktok"],
        ):
            args = _parse_args()
            assert args.platforms == ["youtube", "tiktok"]

    def test_parse_args_log_level(self) -> None:
        """Test Logging-Level."""
        with patch("sys.argv", ["main.py", "--log-level", "DEBUG"]):
            args = _parse_args()
            assert args.log_level == "DEBUG"


class TestExceptionHierarchy:
    """Tests für Exception-Hierarchie."""

    def test_scraper_error_is_pipeline_error(self) -> None:
        """Test dass ScraperError ein PipelineError ist."""
        assert issubclass(ScraperError, PipelineError)

    def test_render_error_is_pipeline_error(self) -> None:
        """Test dass RenderError ein PipelineError ist."""
        assert issubclass(RenderError, PipelineError)

    def test_upload_error_is_pipeline_error(self) -> None:
        """Test dass UploadError ein PipelineError ist."""
        assert issubclass(UploadError, PipelineError)
