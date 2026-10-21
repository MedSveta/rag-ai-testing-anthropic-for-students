import pytest
import re
from tests.golden import golden_params

pytestmark = [pytest.mark.api, pytest.mark.llm]

MISSING_ANSWER = "The information is not specified in the knowledge base."

MAX_WORDS_ANSWER = 80

_answers = {}

def ask(api_client, question):
    if question not in _answers:
        response = api_client.post("/ask", json={"question": question})
        assert response.status_code == 200, response.text
        _answers[question] = response.json()
    return _answers[question]

def without_requirement_ids(answer):
    return re.sub(r"\b[TF]\d+\b", "", answer)

@pytest.fixture(scope="module", autouse=True)
def require_api_key(api_client):
    if not api_client.get("/health").json()["api_key_configured"]:
        pytest.skip("API key not configured in .env")

def test_ask_quality_returns_answer(api_client):
    body = ask(api_client, "What is the maximum password length?")
    assert body["answer"] != "", "Answer is empty"
    assert body["contexts"]
    assert body["usage"]["input_tokens"] > 0
    assert body["usage"]["output_tokens"] > 0

@pytest.mark.parametrize("case", golden_params("known"))
def test_ask_quality_found_expected_facts(api_client, case):
    answer = ask(api_client, case["question"])["answer"]
    text = without_requirement_ids(answer).lower()
    for word in case["expected_contains"]:
        assert word.lower() in text, f"{word} not in {text}"


@pytest.mark.parametrize("case", golden_params("known"))
def test_ask_known_answer_dont_include_not_specified(api_client, case):
    answer = ask(api_client, case["question"])["answer"]
    assert "not specified" not in answer.lower()

@pytest.mark.parametrize("case", golden_params("missing"))
def test_ask_missing_answer_not_specified(api_client, case):
    answer = ask(api_client, case["question"])["answer"]
    assert "not specified" in answer.lower(), f"Model is not missing a question {answer}"







