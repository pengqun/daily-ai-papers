"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/daily_ai_papers"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    llm_provider: str = "openai"  # "openai", "anthropic", or "fake" (for testing)
    llm_api_key: str = ""
    llm_base_url: str = ""  # Custom base URL for OpenAI-compatible APIs (e.g. Groq, OpenRouter)
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Crawler
    crawl_schedule_hour: int = 6
    crawl_categories: str = "cs.AI,cs.CL,cs.CV,cs.LG,stat.ML"
    crawl_max_results: int = 100
    crawl_days_back: int = 1

    # Translation
    translation_languages: str = "zh,ja,es"

    @property
    def crawl_category_list(self) -> list[str]:
        return [c.strip() for c in self.crawl_categories.split(",")]

    @property
    def translation_language_list(self) -> list[str]:
        return [lang.strip() for lang in self.translation_languages.split(",")]


settings = Settings()
