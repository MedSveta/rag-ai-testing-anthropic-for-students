from app.vector_store import RetrievedContext, VectorStore


class Retriever:
    def __init__(
        self,
        store: VectorStore,
        default_top_k: int = 4,
        min_relevance_score: float = 0.35,
    ):
        self.store = store
        self.default_top_k = default_top_k
        self.min_relevance_score = min_relevance_score

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedContext]:
        question = question.strip()
        if not question:
            raise ValueError("Question must not be blank.")
        return self.store.search(
            question,
            top_k or self.default_top_k,
            min_score=self.min_relevance_score,
        )
