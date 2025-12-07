"""Social Video AutoPublisher - Haupteinstiegspunkt für die Automatisierungspipeline.

Dieses Modul orchestriert die komplette Workflow-Pipeline:
- Scraping von Inhalten (z.B. Reddit)
- Rendering von Videos
- Upload auf verschiedene Plattformen
- Scheduler für periodische Ausführung
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from automation.cleanup import cleanup
from automation.logger import log_event
from automation.scheduler import start_scheduler
from ui import settings_manager
from render.pipeline import render_videos
from scraper.reddit import RedditScraper
from upload.clapper import upload_to_clapper
from upload.tiktok import upload_to_tiktok
from upload.youtube import upload_to_youtube

# Logger für dieses Modul
logger = logging.getLogger(__name__)

# Type Alias für Upload-Funktionen
UploadFunction = Callable[[str, dict], None]

UPLOAD_FUNCTIONS: dict[str, UploadFunction] = {
    "youtube": upload_to_youtube,
    "tiktok": upload_to_tiktok,
    "clapper": upload_to_clapper,
}


class PipelineError(Exception):
    """Basisexception für Pipeline-Fehler."""

    pass


class ScraperError(PipelineError):
    """Exception bei Scraping-Fehlern."""

    pass


class RenderError(PipelineError):
    """Exception bei Rendering-Fehlern."""

    pass


class UploadError(PipelineError):
    """Exception bei Upload-Fehlern."""

    pass


def _collect_clips(settings: dict) -> tuple[list[str], Path, Path]:
    """Sammelt Clips aus Reddit und bereitet Ordnerstruktur vor.

    Args:
        settings: Konfigurationsdictionary mit Ordner- und Scraper-Einstellungen

    Returns:
        Tuple aus (Clips-Liste, Temp-Ordner-Path, Video-Ordner-Path)

    Raises:
        ScraperError: Bei Fehler beim Scraping oder der Authentifizierung
    """
    try:
        # Ordner vorbereiten
        video_folder = Path(settings.get("video_folder", "./output"))
        video_folder.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Video-Ordner erstellt/überprüft: {video_folder}")

        temp_folder = Path(settings.get("temp_folder", "./temp"))
        temp_folder.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Temp-Ordner erstellt/überprüft: {temp_folder}")

        # Scraper initialisieren
        subreddit_setting = (
            settings.get("reddit_subreddits") 
            or settings.get("reddit_subreddit", "memes")
        )
        scraper = RedditScraper(
            subreddit=subreddit_setting,
            limit=settings.get("reddit_limit", 10),
        )
        
        logger.info(f"Starte Reddit-Scraper für Subreddit(s): {subreddit_setting}")
        scraper.authenticate()
        logger.debug("Authentifizierung erfolgreich")
        
        clips = scraper.scrape(temp_folder.as_posix())
        logger.info(f"Erfolgreich {len(clips)} Clips gescraped")
        
        return clips, temp_folder, video_folder
        
    except Exception as exc:
        error_msg = f"Fehler beim Scraping: {exc}"
        logger.error(error_msg, exc_info=True)
        raise ScraperError(error_msg) from exc


def run_once(settings: dict, *, platforms: Iterable[str] | None = None) -> str:
    """Führt die komplette Pipeline einmal aus.

    Orchestriert den gesamten Workflow:
    1. Sammelt Clips durch Scraping
    2. Rendert finale Video-Datei
    3. Lädt auf ausgewählte Plattformen hoch
    4. Räumt temporäre Dateien auf

    Args:
        settings: Konfigurationsdictionary
        platforms: Optionale Liste von Zielplattformen. Wenn None, alle verfügbaren.

    Returns:
        Pfad zur finalen Video-Datei

    Raises:
        ScraperError: Bei Scraping-Fehlern
        RenderError: Bei Video-Rendering-Fehlern
    """
    logger.info("Starte Pipeline-Ausführung (once)")
    
    try:
        # Phase 1: Clips sammeln
        logger.debug("Phase 1: Clip-Sammlung startet")
        clips, temp_folder, video_folder = _collect_clips(settings)
        
        if not clips:
            error_msg = "Keine Clips gesammelt - Pipeline abgebrochen"
            logger.error(error_msg)
            raise ScraperError(error_msg)
        
        # Phase 2: Video rendern
        logger.debug("Phase 2: Video-Rendering startet")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_template = settings.get("output_filename_template", "final_{timestamp}.mp4")
        final_filename = filename_template.format(timestamp=timestamp)
        final_video_path = video_folder.joinpath(final_filename).as_posix()
        
        try:
            final_video = render_videos(
                clips,
                output_path=final_video_path,
                vertical=settings.get("render_vertical", True),
                settings=settings,
            )
            logger.info(f"Video erfolgreich gerendert: {final_video}")
        except Exception as exc:
            error_msg = f"Video-Rendering fehlgeschlagen: {exc}"
            logger.error(error_msg, exc_info=True)
            raise RenderError(error_msg) from exc

        # Phase 3: Uploads durchführen
        logger.debug("Phase 3: Plattform-Uploads starten")
        selected_platforms = list(platforms) if platforms else list(UPLOAD_FUNCTIONS.keys())
        upload_failures: dict[str, str] = {}
        
        for platform in selected_platforms:
            upload_func = UPLOAD_FUNCTIONS.get(platform)
            if not upload_func:
                msg = f"Unbekannte Plattform '{platform}' – kein Upload durchgeführt"
                logger.warning(msg)
                log_event(msg)
                continue

            logger.info(f"Starte Upload zu {platform}")
            try:
                upload_func(final_video, settings)
                logger.info(f"Upload zu {platform} erfolgreich")
            except NotImplementedError as exc:
                msg = f"{platform}: Funktion noch nicht implementiert"
                logger.warning(f"{msg}: {exc}")
                log_event(f"{msg} ({exc})")
                upload_failures[platform] = str(exc)
            except Exception as exc:
                msg = f"{platform}: Upload fehlgeschlagen"
                logger.error(f"{msg}: {exc}", exc_info=True)
                log_event(f"{msg} ({exc})")
                upload_failures[platform] = str(exc)
        
        if upload_failures:
            logger.warning(f"Uploads zu {len(upload_failures)} Plattformen fehlgeschlagen")

        # Phase 4: Cleanup
        logger.debug("Phase 4: Cleanup startet")
        try:
            cleanup(temp_folder.as_posix(), delete_extensions={".mp4"})
            cleanup(video_folder.as_posix(), preserve_files={Path(final_video).name})
            logger.debug("Cleanup erfolgreich")
        except Exception as exc:
            logger.error(f"Cleanup-Fehler (nicht kritisch): {exc}")
        
        logger.info("Pipeline-Ausführung erfolgreich abgeschlossen")
        return final_video
        
    except PipelineError:
        logger.critical("Pipeline durch kritischen Fehler abgebrochen")
        raise
    except Exception as exc:
        error_msg = f"Unerwarteter Fehler in Pipeline: {exc}"
        logger.critical(error_msg, exc_info=True)
        raise PipelineError(error_msg) from exc


def _parse_args() -> argparse.Namespace:
    """Parsed Kommandozeilen-Argumente.

    Returns:
        Namespace mit geparsten Argumenten

    Raises:
        SystemExit: Bei ungültigen Argumenten
    """
    parser = argparse.ArgumentParser(
        description="Social Video AutoPublisher - Automatische Video-Erstellung und Verbreitung",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=("once", "schedule"),
        default="once",
        help="Ausführungsmodus: 'once' für einmalige Ausführung, 'schedule' für dauerhaften Scheduler",
    )
    parser.add_argument(
        "--platform",
        action="append",
        dest="platforms",
        help="Zielplattform(en) für den Upload. Kann mehrfach angegeben werden. "
             "Ohne Angabe werden alle verfügbaren Plattformen genutzt.",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        default="INFO",
        help="Logging-Level (Standard: INFO)",
    )
    
    return parser.parse_args()


def main() -> None:
    """Haupteinstiegspunkt der Anwendung.

    Orchestriert die Ausführungsmodi und konfiguriert das Logging.

    Raises:
        SystemExit: Bei kritischen Fehlern
    """
    # Argumente parsen
    args = _parse_args()
    
    # Logging-Level konfigurieren
    if hasattr(args, 'log_level'):
        logging.getLogger().setLevel(args.log_level)
        logger.info(f"Logging-Level gesetzt auf {args.log_level}")
    
    logger.info("="*60)
    logger.info("Social Video AutoPublisher gestartet")
    logger.info(f"Modus: {args.mode}")
    
    try:
        # Einstellungen laden
        settings = settings_manager.load_settings()
        logger.debug(f"Einstellungen geladen erfolgreich")
        
        if args.mode == "schedule":
            logger.info("Starte Scheduler-Modus")
            _run_scheduler_mode(settings)
        else:
            logger.info("Starte einmalige Ausführung (once)")
            _run_once_mode(settings, args.platforms)
            
        logger.info("Anwendung erfolgreich abgeschlossen")
        
    except KeyboardInterrupt:
        logger.warning("Anwendung durch Benutzer unterbrochen (Ctrl+C)")
        sys.exit(0)
    except PipelineError as exc:
        logger.error(f"Pipeline-Fehler: {exc}")
        sys.exit(1)
    except Exception as exc:
        logger.critical(f"Kritischer Fehler: {exc}", exc_info=True)
        sys.exit(2)
    finally:
        logger.info("="*60)


def _run_once_mode(settings: dict, platforms: list[str] | None) -> None:
    """Führt die Pipeline in 'once'-Modus aus.

    Args:
        settings: Konfigurationsdictionary
        platforms: Optionale Liste von Zielplattformen

    Raises:
        PipelineError: Bei Pipeline-Fehlern
    """
    try:
        final_video = run_once(settings, platforms=platforms)
        log_event(f"Video erfolgreich erstellt und verarbeitet: {final_video}")
    except PipelineError as exc:
        log_event(f"Pipeline fehlgeschlagen: {exc}")
        raise


def _run_scheduler_mode(settings: dict) -> None:
    """Führt die Pipeline im Scheduler-Modus aus.

    Args:
        settings: Konfigurationsdictionary

    Raises:
        SystemExit: Wenn keine gültigen Plattformen konfiguriert sind
    """
    upload_times = settings.get("upload_times", {})
    
    if not upload_times:
        error_msg = "Keine Scheduler-Einstellungen unter 'upload_times' gefunden"
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    # Tasks für Scheduler vorbereiten
    tasks: dict[str, Callable[[], None]] = {}
    for platform in upload_times:
        if platform not in UPLOAD_FUNCTIONS:
            logger.warning(f"Plattform '{platform}' nicht unterstützt, wird übersprungen")
            continue
        
        # Closure für jede Plattform erstellen
        def create_task(plat: str) -> Callable[[], None]:
            def task() -> None:
                try:
                    logger.info(f"Scheduler-Task für {plat} ausgelöst")
                    run_once(
                        settings_manager.load_settings(),
                        platforms=[plat]
                    )
                except Exception as exc:
                    logger.error(f"Scheduler-Task für {plat} fehlgeschlagen: {exc}", exc_info=True)
            return task
        
        tasks[platform] = create_task(platform)
    
    if not tasks:
        error_msg = "Keine gültigen Plattformen für den Scheduler konfiguriert"
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    logger.info(f"Starte Scheduler mit {len(tasks)} Task(s)")
    start_scheduler(tasks, settings)


if __name__ == "__main__":
    main()

