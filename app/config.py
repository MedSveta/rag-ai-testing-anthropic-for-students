from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "PhoneBook RAG AI Testing"
    app_version: str = "0.3.0"

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    max_output_tokens: int = 700

    knowledge_path: str = "knowledge/requirements.md"
    chroma_path: str = ".chroma"
    chroma_collection: str = "phonebook_requirements"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 4
    min_relevance_score: float = 0.35
    auto_index: bool = True

    # Keep zero by default: prices change. Set current values in .env if cost reporting is desired.
    anthropic_input_cost_per_million: float = 0.0
    anthropic_output_cost_per_million: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

    @property
    def resolved_knowledge_path(self) -> Path:
        return self.resolve_path(self.knowledge_path)

    @property
    def resolved_chroma_path(self) -> Path:
        return self.resolve_path(self.chroma_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
