"""Basis-Scraper-Abstraktion für alle Scraper-Implementierungen."""

from abc import ABC, abstractmethod
from typing import Any


class ScraperBase(ABC):
    """Abstrakte Basisklasse für alle Scraper.
    
    Definiert die Interface-Methoden, die alle Scraper-Implementierungen
    bereitstellen müssen. Nutzt ABC für enforce-Architektur.
    """

    @abstractmethod
    def authenticate(self) -> None:
        """Authentifizierung durchführen.
        
        Für öffentliche APIs (z.B. Reddit): Kann ein Noop sein.
        Für geschützte APIs (z.B. Instagram): OAuth-Flow implementieren.
        
        Raises:
            ScraperAuthError: Bei Authentifizierungsfehlern
        """
        pass

    @abstractmethod
    def scrape(self, target_dir: str) -> list[str]:
        """Scrapingprozess durchführen.
        
        Extrahiert Inhalte aus Quellen und lädt sie lokal herunter.
        
        Args:
            target_dir: Zielverzeichnis für heruntergeladene Dateien
            
        Returns:
            Liste mit lokalen Dateipfaden der gescrapten Medien
            
        Raises:
            ScraperError: Bei Scraping-Fehlern
        """
        pass

