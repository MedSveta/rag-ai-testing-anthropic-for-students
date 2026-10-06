"""Shared fixtures and fakes for developer unit tests.

Unit tests must be deterministic and free:
- they never read the developer's real .env file;
- they never call the Anthropic API;
- they never load the real sentence-transformers model.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import pytest

from app.config import Settings
from app.llm_client import LLMResult, LLMUsage
from app.vector_store import RetrievedContext

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_FILE = PROJECT_ROOT / "knowledge" / "requirements.md"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    """Remove app settings from environment variables so tests behave the same on every machine."""
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
        monkeypatch.delenv(field_name, raising=False)


@pytest.fixture
def make_settings(tmp_path):
    """Build Settings that ignore .env and point storage into a temporary folder."""

    def _make(**overrides) -> Settings:
        values = {
            "anthropic_api_key": None,
            "chroma_path": str(tmp_path / "chroma"),
            "knowledge_path": str(KNOWLEDGE_FILE),
        }
        values.update(overrides)
        return Settings(_env_file=None, **values)

    return _make


class FakeEmbedder:
    """Deterministic bag-of-words embedder: texts sharing words get similar vectors.

    Every new word gets its own vector position, so different words never collide.
    """

    model_name = "fake-embedder"
    dimensions = 512

    def __init__(self):
        self.calls: list[list[str]] = []
        self.vocabulary: dict[str, int] = {}

    def encode(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in re.findall(r"[a-z0-9]+", text.lower()):
            position = self.vocabulary.setdefault(word, len(self.vocabulary) % self.dimensions)
            vector[position] += 1.0
        norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / norm for x in vector]


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


def make_context(
    text: str = "Requirement T15: Password must have maximum 15 symbols",
    *,
    chunk_id: str = "t15-password",
    source: str = "requirements.md",
    section: str = "Password Requirements",
    requirement_ids: tuple[str, ...] = ("T15",),
    distance: float | None = 0.1,
) -> RetrievedContext:
    return RetrievedContext(
        chunk_id=chunk_id,
        text=text,
        source=source,
        section=section,
        requirement_ids=requirement_ids,
        distance=distance,
    )


def make_llm_result(text: str = "Maximum is 15 symbols [T15].") -> LLMResult:
    return LLMResult(
        text=text,
        model="claude-test",
        usage=LLMUsage(input_tokens=100, output_tokens=20, approximate_cost_usd=None),
    )
