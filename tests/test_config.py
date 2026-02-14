"""Unit tests for application configuration."""

from daily_ai_papers.config import Settings


class TestCrawlCategoryList:
    """Test the crawl_category_list property."""

    def test_default_categories(self) -> None:
        s = Settings(crawl_categories="cs.AI,cs.CL,cs.CV,cs.LG,stat.ML")
        assert s.crawl_category_list == ["cs.AI", "cs.CL", "cs.CV", "cs.LG", "stat.ML"]

    def test_single_category(self) -> None:
        s = Settings(crawl_categories="cs.AI")
        assert s.crawl_category_list == ["cs.AI"]

    def test_whitespace_is_stripped(self) -> None:
        s = Settings(crawl_categories="cs.AI , cs.CL , cs.CV")
        assert s.crawl_category_list == ["cs.AI", "cs.CL", "cs.CV"]


class TestTranslationLanguageList:
    """Test the translation_language_list property."""

    def test_default_languages(self) -> None:
        s = Settings(translation_languages="zh,ja,es")
        assert s.translation_language_list == ["zh", "ja", "es"]

    def test_single_language(self) -> None:
        s = Settings(translation_languages="zh")
        assert s.translation_language_list == ["zh"]

    def test_whitespace_is_stripped(self) -> None:
        s = Settings(translation_languages=" zh , ja , es ")
        assert s.translation_language_list == ["zh", "ja", "es"]
