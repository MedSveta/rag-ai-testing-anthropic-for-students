import os

from deepeval.metrics import FaithfulnessMetric

os.environ.setdefault("DEEPEVAL_TELEMETRY_OPT_OUT", "YES")

import pytest
from deepeval import *
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, SingleTurnParams

from tests.golden import load_golden_cases

pytestmark = [pytest.mark.deepeval, pytest.mark.api, pytest.mark.llm]

JUDGE_MODEL = "claude-sonnet-5"

_answers = {}

FAITHFULNESS_IDS = ["password-special-chars", "phone-characters", "customer-delete-all"]

def ask(api_client, question):
    if question not in _answers:
        response = api_client.post("/ask", json={"question": question})
        assert response.status_code == 200, response.text
        _answers[question] = response.json()
    return _answers[question]

def golden_case(case_id):
    """Найти случай в golden dataset по id."""
    for case in load_golden_cases():
        if case["id"] == case_id:
            return case
    raise ValueError(f"В golden dataset нет случая с id {case_id}")


def golden_params(case_ids):
    """Превратить список id в параметры для pytest. known_issue → xfail."""
    params = []
    for case_id in case_ids:
        case = golden_case(case_id)
        marks = []
        if "known_issue" in case:
            marks.append(pytest.mark.xfail(reason=case["known_issue"], strict=False))
        params.append(pytest.param(case, id=case_id, marks=marks))
    return params

def make_test_case(api_client, case):
    body = ask(api_client, case["question"])
    retrieval_context = []
    for context in body["contexts"]:
        retrieval_context.append(context["text"])

    return LLMTestCase(
        input=case["question"],
        actual_output=body["answer"],
        expected_output=case["expected_answer"],
        retrieval_context=retrieval_context,
    )

def check_metric(metric, test_case):
    metric.measure(test_case)

    print(f"{metric.__name__}: score: {metric.score:.2f} (threshold {metric.threshold})")
    print(f"Answer from system : {test_case.actual_output}")
    print(f"Reason for: {metric.reason}")

    assert metric.is_successful(), (f"{metric.__name__}: score: {metric.score:.2f} (threshold {metric.threshold}). Reason for: {metric.reason}")

@pytest.fixture(scope="module", autouse=True)
def judge(api_client):
    if not api_client.get("/health").json()["api_key_configured"]:
        pytest.skip("API key not configured in .env")
    return AnthropicModel(model=JUDGE_MODEL, temperature=0)

@pytest.mark.parametrize("case",golden_params(FAITHFULNESS_IDS))
def test_deepeval_faithful(api_client, judge, case):
    metric = FaithfulnessMetric(threshold=0.8, model=judge, async_mode=False)
    check_metric(metric, make_test_case(api_client, case))


