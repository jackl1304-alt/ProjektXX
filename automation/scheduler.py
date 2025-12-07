from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler

LOGGER = logging.getLogger(__name__)


def _build_scheduler(settings: Mapping[str, Any]) -> BlockingScheduler:
    """Erzeugt einen BlockingScheduler mit optionaler Persistenz."""
    jobstores = {}
    jobstore_url = settings.get("scheduler_jobstore_url")
    if jobstore_url:
        try:
            from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

            jobstores["default"] = SQLAlchemyJobStore(url=jobstore_url)
        except Exception as exc:  # pragma: no cover - direkte Fehlermeldung genügt
            LOGGER.error("Scheduler: Jobstore konnte nicht initialisiert werden: %s", exc)
            raise

    executors = {
        "default": ThreadPoolExecutor(settings.get("scheduler_max_workers", 4)),
    }
    job_defaults = {
        "coalesce": True,
        "max_instances": settings.get("scheduler_max_instances", 1),
        "misfire_grace_time": settings.get("scheduler_misfire_grace_seconds", 300),
    }

    kwargs: dict[str, Any] = {
        "executors": executors,
        "job_defaults": job_defaults,
        "timezone": settings.get("timezone", "UTC"),
    }
    if jobstores:
        kwargs["jobstores"] = jobstores

    return BlockingScheduler(**kwargs)


def _parse_schedule_entry(entry: Any) -> tuple[str, str | None]:
    """Normalized schedule entry -> (HH:MM, day_of_week)"""
    if isinstance(entry, str):
        return entry, None
    if isinstance(entry, Mapping):
        time_val = entry.get("time")
        days = entry.get("days")
        if not time_val:
            raise ValueError("Scheduler: 'time' fehlt in Upload-Zeit-Eintrag.")
        if days and isinstance(days, (list, tuple, set)):
            days = ",".join(days)
        return str(time_val), days
    raise TypeError(f"Scheduler: Ungültiger Upload-Zeit-Eintrag: {entry!r}")


def start_scheduler(tasks: Mapping[str, Callable[[], None]], settings: dict) -> None:
    """Startet den dauerhaften Scheduler mit den angegebenen Tasks."""
    scheduler = _build_scheduler(settings)

    for platform, entry in settings.get("upload_times", {}).items():
        try:
            time_str, day_of_week = _parse_schedule_entry(entry)
            hour, minute = [int(part) for part in time_str.split(":")]
        except (ValueError, TypeError):
            LOGGER.warning("Scheduler: Ungültige Konfiguration für %s: %s", platform, entry)
            continue

        if platform not in tasks:
            LOGGER.warning("Scheduler: Keine Task-Funktion für Plattform %s gefunden.", platform)
            continue

        trigger_args = {"hour": hour, "minute": minute}
        if day_of_week:
            trigger_args["day_of_week"] = day_of_week

        scheduler.add_job(
            func=tasks[platform],
            trigger="cron",
            id=f"upload_{platform}",
            name=f"{platform}-upload",
            **trigger_args,
        )
        LOGGER.info(
            "Scheduler: Job für %s geplant (%s, days=%s)",
            platform,
            time_str,
            day_of_week or "*",
        )

    scheduler.print_jobs()
    LOGGER.info("Scheduler: Starte BlockingScheduler (CTRL+C zum Beenden).")
    scheduler.start()

