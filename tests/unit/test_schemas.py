import pytest
from pydantic import ValidationError

from app.schemas import (
    AskRequest,
    AskResponse,
    ContextResponse,
    HealthResponse,
    RetrieveRequest,
    UsageResponse,
)


# ---------- AskRequest / RetrieveRequest ----------

@pytest.mark.parametrize("model", [AskRequest, RetrieveRequest])
def test_question_only_is_valid_and_top_k_defaults_to_none(model):
    request = model(question="What is T15?")
    assert request.question == "What is T15?"
    assert request.top_k is None


@pytest.mark.parametrize("model", [AskRequest, RetrieveRequest])
@pytest.mark.parametrize("question", ["a", "x" * 4000])
def test_question_length_boundaries_are_accepted(model, question):
    assert model(question=question).question == question


@pytest.mark.parametrize("model", [AskRequest, RetrieveRequest])
@pytest.mark.parametrize("question", ["", "x" * 4001])
def test_question_length_out_of_range_is_rejected(model, question):
    with pytest.raises(ValidationError):
        model(question=question)


@pytest.mark.parametrize("model", [AskRequest, RetrieveRequest])
def test_question_is_required(model):
    with pytest.raises(ValidationError):
        model()


@pytest.mark.parametrize("top_k", [1, 10])
def test_top_k_boundaries_are_accepted(top_k):
    assert AskRequest(question="q", top_k=top_k).top_k == top_k


@pytest.mark.parametrize("top_k", [0, -1, 11])
def test_top_k_out_of_range_is_rejected(top_k):
    with pytest.raises(ValidationError):
        AskRequest(question="q", top_k=top_k)


def test_top_k_numeric_string_is_coerced():
    assert AskRequest(question="q", top_k="3").top_k == 3


def test_top_k_non_numeric_is_rejected():
    with pytest.raises(ValidationError):
        AskRequest(question="q", top_k="many")


def test_whitespace_only_question_passes_schema():
    # The schema only checks length; blank questions are rejected later by Retriever.
    assert AskRequest(question="   ").question == "   "


# ---------- response models ----------

def test_context_response_optional_fields_default_to_none():
    context = ContextResponse(
        chunk_id="c", source="s", section="sec", requirement_ids=[], text="t"
    )
    assert context.distance is None
    assert context.score is None


def test_usage_response_cost_is_optional():
    assert UsageResponse(input_tokens=1, output_tokens=2).approximate_cost_usd is None


def test_ask_response_serializes_nested_models():
    response = AskResponse(
        question="q",
        answer="a",
        model="m",
        contexts=[
            ContextResponse(
                chunk_id="c", source="s", section="sec", requirement_ids=["T1"], text="t"
            )
        ],
        usage=UsageResponse(input_tokens=1, output_tokens=2),
    )
    data = response.model_dump()
    assert data["contexts"][0]["requirement_ids"] == ["T1"]
    assert data["usage"] == {"input_tokens": 1, "output_tokens": 2, "approximate_cost_usd": None}


def test_health_response_requires_all_fields():
    with pytest.raises(ValidationError):
        HealthResponse(status="ok")
