import pytest

from app.retriever import Retriever
from tests.conftest import make_context


class FakeStore:
    def __init__(self, result=None):
        self.calls = []
        self.result = result if result is not None else []

    def search(self, query, top_k, min_score):
        self.calls.append((query, top_k, min_score))
        return self.result


def test_default_parameters():
    retriever = Retriever(FakeStore())
    assert retriever.default_top_k == 4
    assert retriever.min_relevance_score == 0.35


def test_retriever_passes_relevance_threshold_to_store():
    store = FakeStore()
    retriever = Retriever(store, default_top_k=4, min_relevance_score=0.42)

    assert retriever.retrieve("password rules") == []
    assert store.calls == [("password rules", 4, 0.42)]


def test_explicit_top_k_overrides_default():
    store = FakeStore()
    Retriever(store, default_top_k=4).retrieve("q", top_k=2)
    assert store.calls[0][1] == 2


@pytest.mark.parametrize("top_k", [None, 0])
def test_missing_or_zero_top_k_falls_back_to_default(top_k):
    store = FakeStore()
    Retriever(store, default_top_k=5).retrieve("q", top_k=top_k)
    assert store.calls[0][1] == 5


def test_question_is_stripped_before_search():
    store = FakeStore()
    Retriever(store).retrieve("   password  \n")
    assert store.calls[0][0] == "password"


@pytest.mark.parametrize("question", ["", "   ", "\n\t"])
def test_blank_question_is_rejected_without_search(question):
    store = FakeStore()
    with pytest.raises(ValueError, match="must not be blank"):
        Retriever(store).retrieve(question)
    assert store.calls == []


def test_store_result_is_returned_unchanged():
    contexts = [make_context("a"), make_context("b")]
    assert Retriever(FakeStore(contexts)).retrieve("q") is contexts
