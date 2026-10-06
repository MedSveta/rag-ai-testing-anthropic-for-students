from __future__ import annotations

from app.chunker import MarkdownSectionChunker
from app.config import Settings, get_settings
from app.embeddings import EmbeddingModel
from app.index_manifest import build_index_manifest
from app.llm_client import AnthropicLLMClient, LLMResult, LLMUsage
from app.prompt_builder import MISSING_INFORMATION_ANSWER, SYSTEM_PROMPT, build_user_prompt
from app.retriever import Retriever
from app.vector_store import RetrievedContext, VectorStore


class RAGService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._embedder: EmbeddingModel | None = None
        self._store: VectorStore | None = None
        self._retriever: Retriever | None = None
        self._llm: AnthropicLLMClient | None = None

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._embedder = EmbeddingModel(self.settings.embedding_model)
            self._store = VectorStore(
                self.settings.resolved_chroma_path,
                self.settings.chroma_collection,
                self._embedder,
            )
        return self._store

    @property
    def retriever(self) -> Retriever:
        if self._retriever is None:
            self._retriever = Retriever(
                self.store,
                self.settings.top_k,
                self.settings.min_relevance_score,
            )
        return self._retriever

    @property
    def llm(self) -> AnthropicLLMClient:
        if self._llm is None:
            self._llm = AnthropicLLMClient(
                api_key=self.settings.anthropic_api_key or "",
                model=self.settings.anthropic_model,
                max_output_tokens=self.settings.max_output_tokens,
                input_cost_per_million=self.settings.anthropic_input_cost_per_million,
                output_cost_per_million=self.settings.anthropic_output_cost_per_million,
            )
        return self._llm

    def _expected_manifest(self) -> dict:
        path = self.settings.resolved_knowledge_path
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {path}")
        return build_index_manifest(
            knowledge_path=path,
            embedding_model=self.settings.embedding_model,
            collection=self.settings.chroma_collection,
        )

    def index_knowledge_base(self, replace: bool = True) -> int:
        path = self.settings.resolved_knowledge_path
        if not path.exists():
            raise FileNotFoundError(f"Knowledge base not found: {path}")
        chunks = MarkdownSectionChunker().load(path)
        count = self.store.index(chunks, replace=replace)
        self.store.save_manifest(self._expected_manifest())
        return count

    def index_is_current(self) -> bool:
        if self.store.count() == 0:
            return False
        return self.store.load_manifest() == self._expected_manifest()

    def ensure_indexed(self) -> None:
        if self.index_is_current():
            return
        if not self.settings.auto_index:
            raise RuntimeError(
                "Knowledge base index is missing or stale. Run the indexing script."
            )
        self.index_knowledge_base(replace=True)

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedContext]:
        self.ensure_indexed()
        return self.retriever.retrieve(question, top_k=top_k)

    def ask(self, question: str, top_k: int | None = None) -> tuple[LLMResult, list[RetrievedContext]]:
        contexts = self.retrieve(question, top_k=top_k)

        # If nothing clears the relevance threshold, do not spend money asking
        # an LLM to infer from an empty context.
        if not contexts:
            return (
                LLMResult(
                    text=MISSING_INFORMATION_ANSWER,
                    model="not-called",
                    usage=LLMUsage(input_tokens=0, output_tokens=0, approximate_cost_usd=0.0),
                ),
                contexts,
            )

        user_prompt = build_user_prompt(question, contexts)
        result = self.llm.generate(SYSTEM_PROMPT, user_prompt)
        return result, contexts
