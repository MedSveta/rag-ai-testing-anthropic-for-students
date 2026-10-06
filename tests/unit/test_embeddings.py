"""EmbeddingModel tests with a fake sentence_transformers module (no model download)."""

import sys
from types import ModuleType

import pytest

from app.embeddings import EmbeddingModel


class FakeArray:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class FakeSentenceTransformer:
    instances = []

    def __init__(self, model_name):
        self.model_name = model_name
        self.encode_calls = []
        FakeSentenceTransformer.instances.append(self)

    def encode(self, texts, **kwargs):
        self.encode_calls.append((texts, kwargs))
        return FakeArray([[float(len(text)), 1.0] for text in texts])


@pytest.fixture(autouse=True)
def fake_sentence_transformers(monkeypatch):
    FakeSentenceTransformer.instances = []
    module = ModuleType("sentence_transformers")
    module.SentenceTransformer = FakeSentenceTransformer
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)


def test_model_is_loaded_by_name():
    model = EmbeddingModel("my-model")

    assert model.model_name == "my-model"
    assert [m.model_name for m in FakeSentenceTransformer.instances] == ["my-model"]


def test_encode_returns_python_lists():
    vectors = EmbeddingModel("m").encode(["ab", "abcd"])
    assert vectors == [[2.0, 1.0], [4.0, 1.0]]


def test_encode_normalizes_and_hides_progress_bar():
    model = EmbeddingModel("m")
    model.encode(["a"])

    _, kwargs = FakeSentenceTransformer.instances[0].encode_calls[0]
    assert kwargs == {"normalize_embeddings": True, "show_progress_bar": False}


def test_encode_accepts_any_iterable():
    model = EmbeddingModel("m")
    model.encode(text for text in ["a", "b"])

    texts, _ = FakeSentenceTransformer.instances[0].encode_calls[0]
    assert texts == ["a", "b"]


def test_encode_empty_input():
    assert EmbeddingModel("m").encode([]) == []
