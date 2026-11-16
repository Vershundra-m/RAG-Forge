import requests
from bs4 import BeautifulSoup

from rag_forge.scrapers.base import BaseScraper


class WebPageScraper(BaseScraper):
    """Fetches and cleans text from a web page.

    content_selectors is a list of CSS selector strings. Each matched element's
    text is extracted in order. If empty, falls back to full-page text.

    Example selectors for a typical CMS page:
        ["main", "div.sidebar", "[data-aria-accordion]", "div.jump-scroll", "div.feature"]
    """

    def __init__(self, url: str, content_selectors: list[str] | None = None):
        self.url = url
        self.content_selectors = content_selectors or []

    def fetch(self) -> str:
        response = requests.get(self.url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        if soup.head:
            soup.head.decompose()
        for tag in soup.find_all(["script", "style", "noscript"]):
            tag.decompose()

        text_parts = []
        if self.content_selectors:
            for selector in self.content_selectors:
                for element in soup.select(selector):
                    text_parts.append(element.get_text())
        else:
            text_parts.append(soup.get_text())

        raw_text = "\n".join(text_parts)
        lines = [
            line.strip() for line in raw_text.split("\n") if line.strip() and len(line.strip()) > 2
        ]
        return "\n".join(lines)
