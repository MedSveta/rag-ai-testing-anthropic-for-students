import pytest

QUESTION = "What is the maximum password length?"

MIN_RELEVANCE_SCORE = 0.35


def test_retrieve_return_200(api_client):
    response = api_client.post("/retrieve", json={"question": QUESTION})
    assert response.status_code == 200


def test_retrieve_have_question(api_client):
    body = api_client.post("/retrieve", json={"question": QUESTION}).json()
    assert body["question"] == QUESTION


def test_retrieve_have_list_contexts(api_client):
    body = api_client.post("/retrieve", json={"question": QUESTION}).json()
    assert isinstance(body["contexts"], list)
    assert len(body["contexts"]) > 0


def test_retrieve_have_all_fields_in_context(api_client):
    body = api_client.post("/retrieve", json={"question": QUESTION}).json()
    expected_fields = {
        "chunk_id",
        "source",
        "section",
        "requirement_ids",
        "text",
        "distance",
        "score",
    }
    for context in body["contexts"]:
        assert set(context.keys()) == expected_fields
        assert isinstance(context["requirement_ids"], list)
        assert isinstance(context["text"], str)
        assert context["text"]


@pytest.mark.parametrize("top_k", [1, 2, 4, 10])
def test_retrieve_top_k(api_client, top_k):
    body = api_client.post("/retrieve", json={"question": QUESTION, "top_k": top_k}).json()

    assert len(body["contexts"]) == top_k

def test_retrieve_distance_between_0_and_1(api_client):
    body = api_client.post("/retrieve", json={"question": QUESTION}).json()
    for context in body["contexts"]:
        assert 0 <= context["distance"] <= 1

def test_retrieve_score_between_min_and_1(api_client):
    body = api_client.post("/retrieve", json={"question": QUESTION}).json()
    for context in body["contexts"]:
        assert MIN_RELEVANCE_SCORE <= context["score"] <= 1

def test_retrieve_sorted_by_score(api_client):
    body = api_client.post("/retrieve", json={"question": QUESTION, "top_k":10}).json()
    scores = [context["score"] for context in body["contexts"]]
    assert scores == sorted(scores, reverse=True)