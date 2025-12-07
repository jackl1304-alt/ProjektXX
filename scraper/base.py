class ScraperBase:
    """Abstrakte Basisklasse für alle Scraper."""

    def authenticate(self) -> None:
        """Verantwortlich für Logins oder Token-Handling."""
        raise NotImplementedError

    def scrape(self, target_dir: str) -> list[str]:
        """Liefert eine Liste lokaler Pfade für heruntergeladene Medien."""
        raise NotImplementedError

