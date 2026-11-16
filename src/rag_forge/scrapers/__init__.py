from rag_forge.scrapers.base import BaseScraper
from rag_forge.scrapers.web_page import WebPageScraper
from rag_forge.scrapers.urp_scraper import URPScraper

SCRAPER_REGISTRY = {
    "web_page": WebPageScraper,
    "urp": URPScraper,
}

__all__ = ["BaseScraper", "WebPageScraper", "URPScraper", "SCRAPER_REGISTRY"]
