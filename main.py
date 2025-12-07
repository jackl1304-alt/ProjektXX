from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Iterable

from automation.cleanup import cleanup
from automation.logger import log_event
from automation.scheduler import start_scheduler
from ui import settings_manager
from render.pipeline import render_videos
from scraper.reddit import RedditScraper
from upload.clapper import upload_to_clapper
from upload.tiktok import upload_to_tiktok
from upload.youtube import upload_to_youtube


UPLOAD_FUNCTIONS = {
    "youtube": upload_to_youtube,
    "tiktok": upload_to_tiktok,
    "clapper": upload_to_clapper,
}


def _collect_clips(settings: dict) -> tuple[list[str], Path, Path]:
    video_folder = Path(settings.get("video_folder", "./output"))
    video_folder.mkdir(parents=True, exist_ok=True)

    temp_folder = Path(settings.get("temp_folder", "./temp"))
    temp_folder.mkdir(parents=True, exist_ok=True)

    subreddit_setting = settings.get("reddit_subreddits") or settings.get("reddit_subreddit", "memes")
    scraper = RedditScraper(
        subreddit=subreddit_setting,
        limit=settings.get("reddit_limit", 10),
    )
    scraper.authenticate()
    clips = scraper.scrape(temp_folder.as_posix())
    return clips, temp_folder, video_folder


def run_once(settings: dict, *, platforms: Iterable[str] | None = None) -> str:
    """Führt die komplette Pipeline einmal aus."""
    clips, temp_folder, video_folder = _collect_clips(settings)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_template = settings.get("output_filename_template", "final_{timestamp}.mp4")
    final_filename = filename_template.format(timestamp=timestamp)
    final_video_path = video_folder.joinpath(final_filename).as_posix()

    final_video = render_videos(
        clips,
        output_path=final_video_path,
        vertical=settings.get("render_vertical", True),
        settings=settings,
    )

    selected_platforms = list(platforms) if platforms else list(UPLOAD_FUNCTIONS.keys())
    for platform in selected_platforms:
        upload_func = UPLOAD_FUNCTIONS.get(platform)
        if not upload_func:
            log_event(f"Unbekannte Plattform '{platform}' – kein Upload durchgeführt.")
            continue

        try:
            upload_func(final_video, settings)
        except NotImplementedError as exc:
            log_event(f"{platform}: Funktion noch nicht implementiert ({exc}).")
        except Exception as exc:  # pragma: no cover
            log_event(f"{platform}: Upload fehlgeschlagen ({exc}).")

    cleanup(temp_folder.as_posix(), delete_extensions={".mp4"})
    cleanup(video_folder.as_posix(), preserve_files={Path(final_video).name})

    return final_video


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Social Video AutoPublisher")
    parser.add_argument(
        "--mode",
        choices=("once", "schedule"),
        default="once",
        help="Ausführungsmodus: einmalig oder dauerhafter Scheduler",
    )
    parser.add_argument(
        "--platform",
        action="append",
        help="Zielplattform(en) für den Upload. Ohne Angabe werden alle verfügbaren Plattformen genutzt.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    settings = settings_manager.load_settings()

    if args.mode == "schedule":
        tasks = {
            platform: (lambda platform=platform: run_once(settings_manager.load_settings(), platforms=[platform]))
            for platform in settings.get("upload_times", {})
            if platform in UPLOAD_FUNCTIONS
        }
        if not tasks:
            raise SystemExit("Keine gültigen Plattformen für den Scheduler konfiguriert.")
        start_scheduler(tasks, settings)
    else:
        run_once(settings, platforms=args.platform)


if __name__ == "__main__":
    main()

