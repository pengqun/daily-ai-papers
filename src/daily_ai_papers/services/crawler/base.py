"""Abstract base class for paper crawlers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CrawledPaper:
    """Represents a paper fetched from an external source."""

    source: str
    source_id: str
    title: str
    abstract: str | None = None
    pdf_url: str | None = None
    published_at: datetime | None = None
    categories: list[str] = field(default_factory=list)
    author_names: list[str] = field(default_factory=list)


class BaseCrawler(ABC):
    """Abstract interface for paper source crawlers."""

    @abstractmethod
    async def fetch_recent_papers(
        self,
        categories: list[str],
        max_results: int = 100,
        days_back: int = 1,
    ) -> list[CrawledPaper]:
        """Fetch recently published papers from this source.

        Args:
            categories: Subject categories to search (e.g., ["cs.AI", "cs.CL"]).
            max_results: Maximum number of papers to return.
            days_back: How many days back to search.

        Returns:
            List of crawled paper metadata.
        """
        ...
