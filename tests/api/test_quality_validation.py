import pytest

MIN_RELEVANCE_SCORE = 0.35

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

@pytest.mark.parametrize(
    ("question", "expected_id"),
    [pytest.param("What is the minimum customer password length?","T14",id="min-length-password"),
    pytest.param("What is the maximum customer password length?","T15",id="max-length-password"),
    pytest.param("Is the number required in password length?","T13",id="numbers-in-password"),
    pytest.param("What is the language in the customer password?","T10",id="password-language"),
    pytest.param("Is a special character required in the customer password?","T9",id="password-special-characters"),
    pytest.param("Is customer email required?","T1",id="email-required"),
    pytest.param("How many @ may be in customer email?","T3",id="email-at"),
    pytest.param("How many characters i need before @ in the customer email?","T4",id="email-form-before-at"),
     ],
)
def test_retrieve_question(api_client, question, expected_id):
    contexts = retrieve(api_client, question)
    assert expected_id in found_requirement_ids(contexts)
