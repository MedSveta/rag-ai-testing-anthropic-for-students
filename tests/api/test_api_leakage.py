import pytest
import re

INTERNALS = [
    "Traceback",
    "File",
    "site-packages",
    "sk-ant",
]

PYTHON_FILE = re.compile(r"[\w_]\.py\b")  #_.py   u.py

ERROR_REQUESTS = [
    pytest.param("POST", "/retrieve", {"question": "   "}, 400, id="blank-question-400"),
    pytest.param("POST", "/retrieve", {"question": ""}, 422, id="empty-question-422"),
    pytest.param("POST", "/retrieve", {"question": "x", "top_k": 0}, 422, id="bad-top-k-422"),
    pytest.param("POST", "/retrieve", {}, 422, id="no-question-422"),
    pytest.param("GET", "/ask", None, 405, id="wrong-method-405"),
    pytest.param("GET", "/no-such-page", None, 404, id="unknown-page-404"),
]

def assert_no_internals(text):
    for marker in INTERNALS:
        assert marker not in text, f"Answer has {marker}  in: {text}"
    assert not PYTHON_FILE.search(text), f"Answer has {PYTHON_FILE}  in: {text}"

def test_health_does_not_have_api_key(api_client):
    response = api_client.get("/health")
    assert_no_internals(response.text)

    assert response.json()["api_key_configured"] in (True, False)

@pytest.mark.parametrize(("method", "path", "body", "expected_status_code"), ERROR_REQUESTS)
def test_response_error_not_have_internals(api_client, method, path, body, expected_status_code):
    response = api_client.request(method, path, json=body)
    assert  response.status_code == expected_status_code
    assert_no_internals(response.text)

def test_broken_json_not_have_internals(api_client):
    response = api_client.post("/retrieve", content="it's not json"
                               , headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert_no_internals(response.text)

