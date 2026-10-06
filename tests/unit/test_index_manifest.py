import hashlib

import pytest

from app.chunker import CHUNKER_VERSION
from app.index_manifest import INDEX_MANIFEST_VERSION, build_index_manifest, sha256_file


@pytest.fixture
def knowledge(tmp_path):
    path = tmp_path / "requirements.md"
    path.write_text("T1 first", encoding="utf-8")
    return path


def _manifest(path, embedding_model="model-a", collection="collection"):
    return build_index_manifest(
        knowledge_path=path,
        embedding_model=embedding_model,
        collection=collection,
    )


# ---------- sha256_file ----------

def test_sha256_matches_hashlib(knowledge):
    assert sha256_file(knowledge) == hashlib.sha256(knowledge.read_bytes()).hexdigest()


def test_sha256_of_empty_file(tmp_path):
    path = tmp_path / "empty.md"
    path.write_bytes(b"")
    assert sha256_file(path) == hashlib.sha256(b"").hexdigest()


def test_sha256_of_file_larger_than_read_block(tmp_path):
    path = tmp_path / "big.md"
    data = b"x" * (3 * 1024 * 1024 + 7)
    path.write_bytes(data)
    assert sha256_file(path) == hashlib.sha256(data).hexdigest()


def test_sha256_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        sha256_file(tmp_path / "missing.md")


# ---------- build_index_manifest ----------

def test_manifest_contains_all_fields(knowledge):
    assert _manifest(knowledge) == {
        "manifest_version": INDEX_MANIFEST_VERSION,
        "knowledge_sha256": sha256_file(knowledge),
        "embedding_model": "model-a",
        "chunker_version": CHUNKER_VERSION,
        "collection": "collection",
    }


def test_manifest_is_stable_for_same_inputs(knowledge):
    assert _manifest(knowledge) == _manifest(knowledge)


def test_manifest_changes_when_knowledge_changes(knowledge):
    first = _manifest(knowledge)
    knowledge.write_text("T1 second", encoding="utf-8")
    second = _manifest(knowledge)

    assert first["knowledge_sha256"] != second["knowledge_sha256"]
    assert first != second


def test_manifest_changes_when_embedding_model_changes(knowledge):
    assert _manifest(knowledge, embedding_model="model-a") != _manifest(
        knowledge, embedding_model="model-b"
    )


def test_manifest_changes_when_collection_changes(knowledge):
    assert _manifest(knowledge, collection="a") != _manifest(knowledge, collection="b")


def test_manifest_changes_when_chunker_version_changes(knowledge, monkeypatch):
    first = _manifest(knowledge)
    monkeypatch.setattr("app.index_manifest.CHUNKER_VERSION", "999")
    assert _manifest(knowledge) != first
