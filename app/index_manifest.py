from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from app.chunker import CHUNKER_VERSION

INDEX_MANIFEST_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_index_manifest(
    *,
    knowledge_path: Path,
    embedding_model: str,
    collection: str,
) -> dict[str, str | int]:
    return {
        "manifest_version": INDEX_MANIFEST_VERSION,
        "knowledge_sha256": sha256_file(knowledge_path),
        "embedding_model": embedding_model,
        "chunker_version": CHUNKER_VERSION,
        "collection": collection,
    }
