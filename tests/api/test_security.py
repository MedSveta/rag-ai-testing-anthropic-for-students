import pytest
import re
from tests.golden import PROJECT_ROOT
import json

pytestmark = [pytest.mark.api, pytest.mark.llm, pytest.mark.security]

SECURITY_CASES = PROJECT_ROOT / "test_data" / "security_cases.json"
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

def load_security_cases():
    with open(SECURITY_CASES, encoding="utf-8") as file:
        return json.load(file)


def security_params(only_with_field=None, skip_category=None):
    params = []
    for case in load_security_cases():
        if only_with_field and not case.get(only_with_field):
            continue
        if skip_category and case["category"] == skip_category:
            continue
        params.append(pytest.param(case, id=case["id"]))
    return params

@pytest.mark.parametrize("case", security_params(skip_category="misuse"))
def test_security_check_claude_calling(case, api_client):
    body = ask(api_client, case["question"])

    assert body["model"] != "not-called", "Атака не дошла до Claude"

@pytest.mark.parametrize("case", security_params(only_with_field="forbidden"))
def test_security_check_has_not_forbidden_text(case, api_client):
    answer = ask(api_client, case["question"])["answer"]
    print(answer)
    text = without_requirement_ids(answer).lower()

    for word in case["forbidden"]:
        assert word.lower() not in text, f"The {word} is in {answer}"

@pytest.mark.parametrize("case", security_params(only_with_field="expected_contains"))
def test_security_check_answer_has_expected_contains(case, api_client):
    answer = ask(api_client, case["question"])["answer"]
    print(answer)
    text = without_requirement_ids(answer).lower()

    for word in case["expected_contains"]:
        assert word.lower() in text, f"The {word} not is in {answer}"

@pytest.mark.parametrize("case", security_params(only_with_field="max_words"))
def test_security_check_answer_is_not_too_long(case, api_client):
    answer = ask(api_client, case["question"])["answer"]
    print(answer)

    words = len(answer.split())
    assert  words <= case["max_words"], f" {words} words in the {answer}"