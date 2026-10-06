"""Command-line scripts: RAGService is replaced with a fake."""

import sys

import pytest

from scripts import index_knowledge_base, show_retrieval
from tests.conftest import make_context


class FakeService:
    def __init__(self, contexts=None):
        self.contexts = contexts if contexts is not None else []
        self.calls = []

    def index_knowledge_base(self, replace=True):
        self.calls.append(("index", replace))
        return 42

    def retrieve(self, question, top_k=None):
        self.calls.append(("retrieve", question, top_k))
        return self.contexts


@pytest.fixture
def fake_service(monkeypatch):
    service = FakeService()
    monkeypatch.setattr(index_knowledge_base, "RAGService", lambda: service)
    monkeypatch.setattr(show_retrieval, "RAGService", lambda: service)
    return service


def test_index_script_reindexes_and_prints_count(fake_service, capsys):
    index_knowledge_base.main()

    assert fake_service.calls == [("index", True)]
    assert capsys.readouterr().out == "Indexed 42 chunks into ChromaDB.\n"


def test_show_retrieval_default_top_k(fake_service, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["rag-retrieve", "password length"])
    show_retrieval.main()

    assert fake_service.calls == [("retrieve", "password length", 4)]
    assert "No contexts passed the relevance threshold." in capsys.readouterr().out


def test_show_retrieval_prints_contexts(fake_service, monkeypatch, capsys):
    fake_service.contexts = [
        make_context("T15 text", section="Password", requirement_ids=("T15",), distance=0.25),
        make_context("plain text", section="Overview", requirement_ids=(), distance=None),
    ]
    monkeypatch.setattr(sys, "argv", ["rag-retrieve", "q", "--top-k", "2"])
    show_retrieval.main()
    out = capsys.readouterr().out

    assert fake_service.calls == [("retrieve", "q", 2)]
    assert "#1 score=0.7500 section=Password" in out
    assert "IDs: T15" in out
    assert "#2 score=n/a section=Overview" in out
    assert "IDs: -" in out


def test_show_retrieval_truncates_long_text(fake_service, monkeypatch, capsys):
    fake_service.contexts = [make_context("x" * 1000 + "END")]
    monkeypatch.setattr(sys, "argv", ["rag-retrieve", "q"])
    show_retrieval.main()

    out = capsys.readouterr().out
    assert "x" * 800 in out
    assert "END" not in out


def test_show_retrieval_requires_question(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["rag-retrieve"])
    with pytest.raises(SystemExit):
        show_retrieval.main()
