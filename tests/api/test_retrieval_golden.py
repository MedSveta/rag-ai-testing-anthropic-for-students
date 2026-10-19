import pytest
from tests.golden import golden_params

def retrieve(api_client, question, top_k=4):
    response = api_client.post("/retrieve", json={"question": question, "top_k": top_k})
    assert response.status_code == 200, response.text
    return response.json()["contexts"]


def found_requirement_ids(contexts):
    res = set()
    for context in contexts:
        for rid in context["requirement_ids"]:
            res.add(rid)
    return res

@pytest.mark.parametrize("case", golden_params("known"))
def test_retrieve_golden_known(api_client, case):
    contexts = retrieve(api_client, case["question"])
    expected = set(case["expected_requirement_ids"])
    found = found_requirement_ids(contexts)
    missing = expected - found
    assert not missing, f"Not found: {missing}, all ids are: {sorted(found_requirement_ids(contexts))}"

@pytest.mark.parametrize("case", golden_params("off_topic"))
def test_retrieve_golden_off_topic(api_client, case):
    contexts = retrieve(api_client, case["question"])
    assert contexts == [], f"Found {sorted(found_requirement_ids(contexts))}"