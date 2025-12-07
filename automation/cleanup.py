from __future__ import annotations

import logging
import os
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def cleanup(
    folder: str,
    *,
    delete_extensions: set[str] | None = None,
    preserve_files: set[str] | None = None,
) -> None:
    """Entfernt temporäre Dateien im angegebenen Verzeichnis."""
    root = Path(folder)
    if not root.exists():
        LOGGER.info("Cleanup: Verzeichnis %s existiert nicht.", root)
        return

    delete_extensions = delete_extensions or {".tmp"}
    preserve_files = preserve_files or set()

    for entry in root.iterdir():
        if entry.name in preserve_files:
            continue

        if entry.is_file() and (entry.suffix in delete_extensions or entry.name.startswith("temp")):
            try:
                entry.unlink()
                LOGGER.debug("Cleanup: %s gelöscht.", entry)
            except OSError as exc:
                LOGGER.warning("Cleanup: %s konnte nicht gelöscht werden: %s", entry, exc)

