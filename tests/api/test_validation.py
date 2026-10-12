import pytest

ENDPOINTS = ["/retrieve", "/ask"]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("payload", [
    pytest.param({}, id="no-request-json"),
    pytest.param({"question": ""}, id="empty-question"),
    pytest.param({"question": "   "}, id="only-space-in-question"),
    pytest.param({"question": "a" * 4001}, id="question-4001-chars"),
    pytest.param({"question": 123}, id="question-is-number"),
    ],
)
def test_validation_invalid_422(api_client, endpoint, payload):
    response = api_client.post(endpoint, json=payload)
    assert response.status_code == 422
