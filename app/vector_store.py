from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from app.chunker import Chunk
from app.embeddings import EmbeddingModel


@dataclass(frozen=True)
class RetrievedContext:
    chunk_id: str
    text: str
    source: str
    section: str
    requirement_ids: tuple[str, ...]
    distance: float | None

    @property
    def score(self) -> float | None:
        if self.distance is None:
            return None
        # Chroma cosine distance is lower-is-better. For teaching/debugging we
        # expose a simple 0..1 similarity-like score.
        return max(0.0, min(1.0, 1.0 - self.distance))


class VectorStore:
    def __init__(self, path: Path, collection_name: str, embedder: EmbeddingModel):
        import chromadb

        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(path))
        self.collection_name = collection_name
        self.embedder = embedder
        self._collection = self._get_or_create_collection()

    @property
    def manifest_path(self) -> Path:
        return self.path / f"{self.collection_name}.index-manifest.json"

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _reset_collection(self) -> None:
        try:
            self._client.delete_collection(name=self.collection_name)
        except Exception:
            # A first-time index may not have a persisted collection yet.
            pass
        self._collection = self._get_or_create_collection()

    def count(self) -> int:
        return self._collection.count()

    def index(self, chunks: list[Chunk], replace: bool = True) -> int:
        if replace:
            # Recreate, rather than merely deleting rows, so a change of
            # embedding model/dimension cannot leave an incompatible collection.
            self._reset_collection()
        if not chunks:
            return 0

        documents = [chunk.text for chunk in chunks]
        embeddings = self.embedder.encode(documents)
        metadatas = [
            {
                "source": chunk.source,
                "section": chunk.section,
                "requirement_ids": ",".join(chunk.requirement_ids),
            }
            for chunk in chunks
        ]
        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def load_manifest(self) -> dict | None:
        if not self.manifest_path.exists():
            return None
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def search(
        self,
        query: str,
        top_k: int,
        min_score: float = 0.0,
        candidate_multiplier: int = 3,
    ) -> list[RetrievedContext]:
        if self.count() == 0:
            raise RuntimeError("Vector store is empty. Index the knowledge base first.")

        query_embedding = self.embedder.encode([query])[0]
        candidate_k = min(max(top_k * candidate_multiplier, top_k), self.count())
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=candidate_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        contexts: list[RetrievedContext] = []
        for chunk_id, doc, meta, distance in zip(ids, docs, metas, distances):
            raw_ids = (meta or {}).get("requirement_ids", "")
            context = RetrievedContext(
                chunk_id=chunk_id,
                text=doc,
                source=(meta or {}).get("source", "unknown"),
                section=(meta or {}).get("section", "unknown"),
                requirement_ids=tuple(x for x in raw_ids.split(",") if x),
                distance=float(distance) if distance is not None else None,
            )
            score = context.score
            if score is None or score >= min_score:
                contexts.append(context)
            if len(contexts) >= top_k:
                break
        return contexts
