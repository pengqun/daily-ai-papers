"""Unit tests for arXiv crawler parsing helpers.

Tests _parse_datetime and _parse_entry with fixture data — no network calls.
"""

from datetime import UTC, datetime
from types import SimpleNamespace

from daily_ai_papers.services.crawler.arxiv import _parse_datetime, _parse_entry


class _FeedLink(dict):  # type: ignore[type-arg]
    """Mimics feedparser link objects which are dicts with attribute access."""

    def __init__(self, **kwargs: str) -> None:
        super().__init__(**kwargs)
        self.__dict__.update(kwargs)


def _make_feed_entry(
    *,
    paper_id: str = "2401.00001",
    title: str = "Attention Is All You Need",
    summary: str = "We propose a new architecture.",
    published: tuple[int, ...] = (2024, 1, 15, 12, 0, 0, 0, 15, 0),
    categories: list[str] | None = None,
    authors: list[str] | None = None,
    has_pdf: bool = True,
) -> SimpleNamespace:
    """Build a minimal feedparser-like entry object."""
    links: list[_FeedLink] = [
        _FeedLink(href=f"https://arxiv.org/abs/{paper_id}", type="text/html")
    ]
    if has_pdf:
        links.append(
            _FeedLink(href=f"https://arxiv.org/pdf/{paper_id}", type="application/pdf")
        )

    return SimpleNamespace(
        id=f"http://arxiv.org/abs/{paper_id}",
        title=title,
        summary=summary,
        published_parsed=published,
        links=links,
        tags=[SimpleNamespace(term=c) for c in (categories or ["cs.AI", "cs.CL"])],
        authors=[SimpleNamespace(name=n) for n in (authors or ["Alice", "Bob"])],
    )


class TestParseDatetime:
    """Test conversion of feedparser time structs to datetime."""

    def test_basic_conversion(self) -> None:
        time_struct = (2024, 1, 15, 12, 30, 45, 0, 15, 0)
        result = _parse_datetime(time_struct)
        assert result == datetime(2024, 1, 15, 12, 30, 45, tzinfo=UTC)

    def test_midnight(self) -> None:
        time_struct = (2024, 6, 1, 0, 0, 0, 5, 153, 0)
        result = _parse_datetime(time_struct)
        assert result == datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC)

    def test_returns_utc(self) -> None:
        result = _parse_datetime((2024, 1, 1, 0, 0, 0, 0, 1, 0))
        assert result.tzinfo is UTC


class TestParseEntry:
    """Test conversion of feedparser entries to CrawledPaper."""

    def test_basic_parsing(self) -> None:
        entry = _make_feed_entry()
        paper = _parse_entry(entry)

        assert paper.source == "arxiv"
        assert paper.source_id == "2401.00001"
        assert paper.title == "Attention Is All You Need"
        assert paper.abstract == "We propose a new architecture."
        assert paper.pdf_url == "https://arxiv.org/pdf/2401.00001"
        assert paper.categories == ["cs.AI", "cs.CL"]
        assert paper.author_names == ["Alice", "Bob"]

    def test_explicit_paper_id_overrides_entry_id(self) -> None:
        entry = _make_feed_entry(paper_id="2401.00001")
        paper = _parse_entry(entry, paper_id="custom-id")
        assert paper.source_id == "custom-id"

    def test_title_newlines_stripped(self) -> None:
        entry = _make_feed_entry(title="Multi\nLine\n  Title")
        paper = _parse_entry(entry)
        assert paper.title == "Multi Line   Title"

    def test_no_pdf_link(self) -> None:
        entry = _make_feed_entry(has_pdf=False)
        paper = _parse_entry(entry)
        assert paper.pdf_url is None

    def test_published_datetime_is_utc(self) -> None:
        entry = _make_feed_entry(published=(2023, 12, 25, 10, 0, 0, 0, 359, 0))
        paper = _parse_entry(entry)
        assert paper.published_at == datetime(2023, 12, 25, 10, 0, 0, tzinfo=UTC)

    def test_multiple_categories(self) -> None:
        entry = _make_feed_entry(categories=["cs.AI", "cs.CL", "cs.CV", "stat.ML"])
        paper = _parse_entry(entry)
        assert paper.categories == ["cs.AI", "cs.CL", "cs.CV", "stat.ML"]

    def test_multiple_authors(self) -> None:
        entry = _make_feed_entry(authors=["Alice", "Bob", "Charlie"])
        paper = _parse_entry(entry)
        assert paper.author_names == ["Alice", "Bob", "Charlie"]

    def test_empty_abstract_becomes_none(self) -> None:
        """Empty string is falsy, so _parse_entry returns None for abstract."""
        entry = _make_feed_entry(summary="")
        paper = _parse_entry(entry)
        assert paper.abstract is None
