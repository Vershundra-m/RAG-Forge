from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    def fetch(self) -> str:
        """Fetch content from the data source and return clean text.

        Chunking is the pipeline's responsibility, not the scraper's.
        """
