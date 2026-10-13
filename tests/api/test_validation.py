import pytest

from sympy.parsing.sympy_parser import null

ENDPOINTS = ["/retrieve", "/ask"]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("payload", [
    pytest.param({}, id="no-request-json"),
    pytest.param({"question": ""}, id="empty-question"),
    pytest.param({"question": "a" * 4001}, id="question-4001-chars"),
    pytest.param({"question": 123}, id="question-is-number"),
    pytest.param({"question": "password", "top_k": 0}, id="top-k-0"),
    pytest.param({"question": "password", "top_k": 11}, id="top-k-11"),
    pytest.param({"question": "password", "top_k": -1}, id="top-k-negative"),
    pytest.param({"question": "password", "top_k": 1.1}, id="top-k-not-integer"),
    pytest.param({"question": "password", "top_k": "max"}, id="top-k-str"),
    pytest.param({"question": "password", "top_k": null}, id="top-k-null"),
],
                         )
def test_validation_invalid_422(api_client, endpoint, payload):
    response = api_client.post(endpoint, json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_request_without_body(api_client, endpoint):
    response = api_client.post(endpoint)
    assert response.status_code == 422


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_request_wrong_key_check(api_client, endpoint):
    response = api_client.post(endpoint, json={"question": "question", "top_k": 0})
    errors = response.json()["detail"]
    assert errors[0]["type"] == "greater_than_equal"
    assert errors[0]["loc"] == ["body", "top_k"]
    assert errors[0]["msg"] == "Input should be greater than or equal to 1"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"question": "q"}, id="question-1-char"),
        pytest.param({"question": "q" * 4000}, id="question-4000-chars"),
        pytest.param({"question": "password", "top_k": 1}, id="top-k-1"),
        pytest.param({"question": "password", "top_k": 10}, id="top-k-10"),
    ],
)
def test_boundary_values(api_client, payload):
    response = api_client.post("/retrieve", json=payload)
    assert response.status_code == 200

@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("question", ["   ", "\n\t"], ids=["spaces", "newline,tab"])
def test_spaces_validation_400(api_client, endpoint, question):
    response = api_client.post(endpoint, json={"question": question})
    assert response.status_code == 400
    assert response.json() ==  {'detail': 'Question must not be blank.'}

@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/retrieve"),
        ("GET", "/ask"),
        ("POST", "/health"),
        ("DELETE", "/health"),
    ]
)
def test_wrong_method_return_405(api_client, method, path):
    response = api_client.request(method, path)
    assert response.status_code == 405

def test_unknown_endpoint_404(api_client):
    response = api_client.get("/wrong-endpoint")
    assert response.status_code == 404

