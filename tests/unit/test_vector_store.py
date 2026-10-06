"""VectorStore tests: real local ChromaDB in a temporary folder + fake embedder."""

import json

import pytest

from app.chunker import Chunk
from app.vector_store import RetrievedContext, VectorStore
from tests.conftest import make_context


def _chunk(chunk_id, text, ids=(), section="Section", source="kb.md"):
    return Chunk(id=chunk_id, text=text, source=source, section=section, requirement_ids=tuple(ids))


CHUNKS = [
    _chunk("t14", "password minimum 8 symbols", ("T14",), "Password"),
    _chunk("t15", "password maximum 15 symbols", ("T15",), "Password"),
    _chunk("t41", "phone number minimum 10 digits", ("T41",), "Phone"),
    _chunk("intro", "phone book website overview", (), "Overview"),
]


@pytest.fixture
def store(tmp_path, fake_embedder):
    return VectorStore(tmp_path / "chroma", "test_collection", fake_embedder)


@pytest.fixture
def indexed_store(store):
    store.index(CHUNKS)
    return store


# ---------- RetrievedContext.score ----------

@pytest.mark.parametrize(
    ("distance", "score"),
    [(0.0, 1.0), (0.2, 0.8), (1.0, 0.0), (1.5, 0.0), (-0.3, 1.0)],
)
def test_score_is_one_minus_distance_clamped(distance, score):
    assert make_context(distance=distance).score == pytest.approx(score)


def test_score_is_none_without_distance():
    assert make_context(distance=None).score is None


def test_retrieved_context_is_immutable():
    context = make_context()
    with pytest.raises(AttributeError):
        context.text = "changed"


# ---------- construction ----------

def test_store_creates_folder_and_empty_collection(tmp_path, fake_embedder):
    path = tmp_path / "nested" / "chroma"
    store = VectorStore(path, "col", fake_embedder)

    assert path.is_dir()
    assert store.count() == 0
    assert store.manifest_path == path / "col.index-manifest.json"


def test_collection_uses_cosine_distance(store):
    assert store._collection.metadata["hnsw:space"] == "cosine"


# ---------- index ----------

def test_index_returns_count_and_stores_chunks(store):
    assert store.index(CHUNKS) == len(CHUNKS)
    assert store.count() == len(CHUNKS)


def test_index_embeds_all_documents_in_one_call(store, fake_embedder):
    store.index(CHUNKS)
    assert fake_embedder.calls == [[chunk.text for chunk in CHUNKS]]


def test_reindex_with_replace_does_not_duplicate(store):
    store.index(CHUNKS)
    store.index(CHUNKS[:2], replace=True)
    assert store.count() == 2


def test_index_without_replace_adds_and_updates(store):
    store.index(CHUNKS[:2])
    store.index([_chunk("t15", "updated text"), _chunk("new", "new text")], replace=False)

    assert store.count() == 3
    stored = store._collection.get(ids=["t15"])
    assert stored["documents"] == ["updated text"]


def test_index_empty_list_with_replace_clears_store(indexed_store, fake_embedder):
    calls_before = len(fake_embedder.calls)
    assert indexed_store.index([]) == 0
    assert indexed_store.count() == 0
    assert len(fake_embedder.calls) == calls_before


def test_index_stores_metadata(indexed_store):
    stored = indexed_store._collection.get(ids=["t14"], include=["metadatas"])
    assert stored["metadatas"][0] == {
        "source": "kb.md",
        "section": "Password",
        "requirement_ids": "T14",
    }


def test_index_is_persisted_on_disk(tmp_path, fake_embedder):
    VectorStore(tmp_path / "db", "col", fake_embedder).index(CHUNKS)
    reopened = VectorStore(tmp_path / "db", "col", fake_embedder)
    assert reopened.count() == len(CHUNKS)


# ---------- search ----------

def test_search_on_empty_store_raises(store):
    with pytest.raises(RuntimeError, match="empty"):
        store.search("password", top_k=2)


def test_search_returns_most_similar_first(indexed_store):
    results = indexed_store.search("password maximum", top_k=2)

    assert [r.chunk_id for r in results] == ["t15", "t14"]
    assert results[0].distance <= results[1].distance


def test_search_converts_metadata_to_context(indexed_store):
    result = indexed_store.search("password maximum 15 symbols", top_k=1)[0]

    assert isinstance(result, RetrievedContext)
    assert result.chunk_id == "t15"
    assert result.text == "password maximum 15 symbols"
    assert result.source == "kb.md"
    assert result.section == "Password"
    assert result.requirement_ids == ("T15",)
    assert result.score == pytest.approx(1.0, abs=1e-4)


def test_search_chunk_without_requirement_ids_gives_empty_tuple(indexed_store):
    result = indexed_store.search("phone book website overview", top_k=1)[0]
    assert result.chunk_id == "intro"
    assert result.requirement_ids == ()


@pytest.mark.parametrize("top_k", [1, 2, 3])
def test_search_respects_top_k(indexed_store, top_k):
    assert len(indexed_store.search("password phone", top_k=top_k)) == top_k


def test_search_top_k_larger_than_collection(indexed_store):
    assert len(indexed_store.search("password", top_k=10)) == len(CHUNKS)


def test_search_filters_by_min_score(indexed_store):
    results = indexed_store.search("password maximum", top_k=4, min_score=0.5)

    assert results
    assert all(r.score >= 0.5 for r in results)
    assert "intro" not in [r.chunk_id for r in results]


def test_search_with_impossible_threshold_returns_nothing(indexed_store):
    assert indexed_store.search("completely unrelated words", top_k=4, min_score=0.99) == []


def test_search_embeds_query(indexed_store, fake_embedder):
    indexed_store.search("my question", top_k=1)
    assert fake_embedder.calls[-1] == ["my question"]


def test_search_with_missing_metadata_uses_defaults(store):
    store._collection.upsert(ids=["raw"], documents=["raw text"], embeddings=[store.embedder.encode(["raw text"])[0]])
    result = store.search("raw text", top_k=1)[0]

    assert result.source == "unknown"
    assert result.section == "unknown"
    assert result.requirement_ids == ()


# ---------- manifest ----------

def test_load_manifest_returns_none_when_missing(store):
    assert store.load_manifest() is None


def test_manifest_round_trip(store):
    manifest = {"b": 2, "a": "x"}
    store.save_manifest(manifest)

    assert store.load_manifest() == manifest
    assert json.loads(store.manifest_path.read_text(encoding="utf-8")) == manifest


def test_manifest_file_is_sorted_and_indented(store):
    store.save_manifest({"b": 1, "a": 2})
    assert store.manifest_path.read_text(encoding="utf-8") == '{\n  "a": 2,\n  "b": 1\n}'


def test_corrupted_manifest_is_treated_as_missing(store):
    store.manifest_path.write_text("{not json", encoding="utf-8")
    assert store.load_manifest() is None


def test_reindex_survives_failed_collection_delete(store, monkeypatch):
    def broken_delete(name):
        raise ValueError("collection does not exist")

    monkeypatch.setattr(store._client, "delete_collection", broken_delete)
    assert store.index(CHUNKS) == len(CHUNKS)
