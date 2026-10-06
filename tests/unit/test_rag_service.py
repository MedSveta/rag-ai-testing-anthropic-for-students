"""RAGService tests: fake embedder and fake LLM, real chunker/manifest/ChromaDB in tmp folder."""

import pytest

from app.llm_client import AnthropicLLMClient, LLMConfigurationError, LLMRateLimitError
from app.prompt_builder import MISSING_INFORMATION_ANSWER, SYSTEM_PROMPT
from app.rag_service import RAGService
from app.retriever import Retriever
from app.vector_store import VectorStore
from tests.conftest import make_context, make_llm_result

KNOWLEDGE = """# Password
- **T14** — Password must have minimum 8 symbols
- **T15** — Password must have maximum 15 symbols

# Phone
- **T41** — Phone must have minimum 10 symbol
"""


class FakeLLM:
    def __init__(self, result=None, error=None):
        self.result = result or make_llm_result()
        self.error = error
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def knowledge_file(tmp_path):
    path = tmp_path / "requirements.md"
    path.write_text(KNOWLEDGE, encoding="utf-8")
    return path


@pytest.fixture
def make_service(make_settings, knowledge_file, fake_embedder, tmp_path):
    def _make(**overrides):
        overrides.setdefault("knowledge_path", str(knowledge_file))
        settings = make_settings(**overrides)
        service = RAGService(settings)
        service._embedder = fake_embedder
        service._store = VectorStore(tmp_path / "chroma", settings.chroma_collection, fake_embedder)
        return service

    return _make


# ---------- construction and lazy components ----------

def test_components_are_created_lazily(make_settings):
    service = RAGService(make_settings())
    assert service._store is None
    assert service._retriever is None
    assert service._llm is None


def test_uses_global_settings_by_default():
    from app.config import get_settings

    assert RAGService().settings is get_settings()


def test_retriever_uses_settings(make_service):
    service = make_service(top_k=2, min_relevance_score=0.6)
    retriever = service.retriever

    assert isinstance(retriever, Retriever)
    assert retriever.store is service.store
    assert retriever.default_top_k == 2
    assert retriever.min_relevance_score == 0.6
    assert service.retriever is retriever


def test_store_is_created_from_settings(make_settings, fake_embedder, monkeypatch, tmp_path):
    monkeypatch.setattr("app.rag_service.EmbeddingModel", lambda name: fake_embedder)
    service = RAGService(make_settings(chroma_collection="my_collection"))
    store = service.store

    assert store.path == tmp_path / "chroma"
    assert store.collection_name == "my_collection"
    assert store.embedder is fake_embedder
    assert service.store is store


def test_llm_without_api_key_raises(make_settings):
    with pytest.raises(LLMConfigurationError):
        RAGService(make_settings(anthropic_api_key=None)).llm


def test_llm_is_created_from_settings(make_settings):
    service = RAGService(
        make_settings(
            anthropic_api_key="test-key",
            anthropic_model="claude-test",
            max_output_tokens=55,
            anthropic_input_cost_per_million=1.5,
            anthropic_output_cost_per_million=7.5,
        )
    )
    llm = service.llm

    assert isinstance(llm, AnthropicLLMClient)
    assert llm.model == "claude-test"
    assert llm.max_output_tokens == 55
    assert llm.input_cost_per_million == 1.5
    assert llm.output_cost_per_million == 7.5
    assert service.llm is llm


# ---------- indexing ----------

def test_index_knowledge_base_indexes_chunks_and_saves_manifest(make_service):
    service = make_service()

    assert service.index_knowledge_base() == 3
    assert service.store.count() == 3
    assert service.store.load_manifest() == service._expected_manifest()


def test_index_missing_knowledge_file_raises(make_service, tmp_path):
    service = make_service(knowledge_path=str(tmp_path / "missing.md"))
    with pytest.raises(FileNotFoundError, match="Knowledge base not found"):
        service.index_knowledge_base()


def test_expected_manifest_missing_file_raises(make_service, tmp_path):
    service = make_service(knowledge_path=str(tmp_path / "missing.md"))
    with pytest.raises(FileNotFoundError):
        service._expected_manifest()


def test_index_is_not_current_when_store_is_empty(make_service):
    assert make_service().index_is_current() is False


def test_index_is_current_after_indexing(make_service):
    service = make_service()
    service.index_knowledge_base()
    assert service.index_is_current() is True


def test_index_is_stale_after_knowledge_change(make_service, knowledge_file):
    service = make_service()
    service.index_knowledge_base()
    knowledge_file.write_text(KNOWLEDGE + "- **T42** — Phone maximum 15\n", encoding="utf-8")

    assert service.index_is_current() is False


def test_index_is_stale_without_manifest(make_service):
    service = make_service()
    service.index_knowledge_base()
    service.store.manifest_path.unlink()

    assert service.index_is_current() is False


def test_index_is_stale_when_embedding_model_changes(make_service, fake_embedder, tmp_path):
    service = make_service()
    service.index_knowledge_base()

    other = make_service(embedding_model="another-model")
    assert other.index_is_current() is False


# ---------- ensure_indexed ----------

def test_ensure_indexed_builds_missing_index(make_service):
    service = make_service(auto_index=True)
    service.ensure_indexed()
    assert service.index_is_current() is True


def test_ensure_indexed_does_nothing_when_current(make_service, monkeypatch):
    service = make_service()
    service.index_knowledge_base()
    monkeypatch.setattr(service, "index_knowledge_base", lambda **_: pytest.fail("must not reindex"))

    service.ensure_indexed()


def test_ensure_indexed_rebuilds_stale_index(make_service, knowledge_file):
    service = make_service(auto_index=True)
    service.index_knowledge_base()
    knowledge_file.write_text("# New\n- **T1** — Only one requirement\n", encoding="utf-8")

    service.ensure_indexed()

    assert service.store.count() == 1
    assert service.index_is_current() is True


def test_ensure_indexed_without_auto_index_raises(make_service):
    service = make_service(auto_index=False)
    with pytest.raises(RuntimeError, match="missing or stale"):
        service.ensure_indexed()


# ---------- retrieve ----------

def test_retrieve_indexes_and_returns_relevant_context(make_service):
    service = make_service(min_relevance_score=0.0)
    contexts = service.retrieve("password maximum symbols", top_k=1)

    assert len(contexts) == 1
    assert contexts[0].requirement_ids == ("T15",)


def test_retrieve_uses_default_top_k(make_service):
    service = make_service(top_k=2, min_relevance_score=0.0)
    assert len(service.retrieve("password")) == 2


def test_retrieve_blank_question_raises(make_service):
    with pytest.raises(ValueError):
        make_service().retrieve("   ")


# ---------- ask ----------

def test_empty_retrieval_skips_llm_call(make_settings, monkeypatch):
    service = RAGService(make_settings(anthropic_api_key=None))
    monkeypatch.setattr(service, "retrieve", lambda question, top_k=None: [])

    result, contexts = service.ask("A completely unrelated question")

    assert contexts == []
    assert result.text == MISSING_INFORMATION_ANSWER
    assert result.model == "not-called"
    assert result.usage.input_tokens == 0
    assert result.usage.output_tokens == 0
    assert result.usage.approximate_cost_usd == 0.0


def test_ask_calls_llm_with_system_prompt_and_contexts(make_settings, monkeypatch):
    contexts = [make_context("Requirement T15: max 15", requirement_ids=("T15",))]
    service = RAGService(make_settings())
    service._llm = FakeLLM()
    monkeypatch.setattr(service, "retrieve", lambda question, top_k=None: contexts)

    result, returned_contexts = service.ask("Max length?")

    assert result is service._llm.result
    assert returned_contexts is contexts
    system_prompt, user_prompt = service._llm.calls[0]
    assert system_prompt == SYSTEM_PROMPT
    assert "Requirement T15: max 15" in user_prompt
    assert "Max length?" in user_prompt


def test_ask_passes_top_k_to_retrieve(make_settings, monkeypatch):
    seen = {}
    service = RAGService(make_settings())
    service._llm = FakeLLM()

    def fake_retrieve(question, top_k=None):
        seen["top_k"] = top_k
        return [make_context()]

    monkeypatch.setattr(service, "retrieve", fake_retrieve)
    service.ask("q", top_k=3)

    assert seen["top_k"] == 3


def test_ask_propagates_llm_errors(make_settings, monkeypatch):
    service = RAGService(make_settings())
    service._llm = FakeLLM(error=LLMRateLimitError("limit"))
    monkeypatch.setattr(service, "retrieve", lambda question, top_k=None: [make_context()])

    with pytest.raises(LLMRateLimitError):
        service.ask("q")


def test_ask_end_to_end_with_real_index(make_service):
    service = make_service(min_relevance_score=0.0, top_k=2)
    service._llm = FakeLLM()

    result, contexts = service.ask("phone minimum")

    assert result.text == "Maximum is 15 symbols [T15]."
    assert contexts[0].requirement_ids == ("T41",)
    assert len(service._llm.calls) == 1
