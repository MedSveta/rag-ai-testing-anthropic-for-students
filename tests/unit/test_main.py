"""FastAPI layer tests: RAGService is replaced with a fake, no index or LLM is used."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import app.main as main
from app.llm_client import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResult,
    LLMTimeoutError,
    LLMUsage,
)
from tests.conftest import make_context, make_llm_result


class FakeService:
    def __init__(self, contexts=None, result=None, error=None):
        self.contexts = contexts if contexts is not None else [make_context()]
        self.result = result or make_llm_result()
        self.error = error
        self.calls = []

    def retrieve(self, question, top_k=None):
        self.calls.append(("retrieve", question, top_k))
        if self.error:
            raise self.error
        return self.contexts

    def ask(self, question, top_k=None):
        self.calls.append(("ask", question, top_k))
        if self.error:
            raise self.error
        return self.result, self.contexts


@pytest.fixture
def use_service(monkeypatch):
    def _use(service):
        monkeypatch.setattr(main, "get_service", lambda: service)
        return service

    return _use


@pytest.fixture
def client(make_settings, monkeypatch):
    monkeypatch.setattr(main, "settings", make_settings(anthropic_api_key=None))
    return TestClient(main.app)


# ---------- app metadata and docs ----------

def test_app_title_and_version():
    assert main.app.title == main.settings.app_name
    assert main.app.version == main.settings.app_version


def test_openapi_lists_all_endpoints(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/health", "/retrieve", "/ask"}
    assert "get" in paths["/health"]
    assert "post" in paths["/retrieve"]
    assert "post" in paths["/ask"]


def test_swagger_ui_is_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


# ---------- /health ----------

def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == main.settings.app_name
    assert body["version"] == main.settings.app_version
    assert body["anthropic_model"] == main.settings.anthropic_model
    assert body["api_key_configured"] is False
    assert body["knowledge_base_exists"] is True


def test_health_reports_configured_key_without_exposing_it(make_settings, monkeypatch):
    monkeypatch.setattr(main, "settings", make_settings(anthropic_api_key="secret-key"))
    response = TestClient(main.app).get("/health")

    assert response.json()["api_key_configured"] is True
    assert "secret-key" not in response.text


def test_health_reports_missing_knowledge_base(make_settings, monkeypatch, tmp_path):
    monkeypatch.setattr(main, "settings", make_settings(knowledge_path=str(tmp_path / "none.md")))
    assert TestClient(main.app).get("/health").json()["knowledge_base_exists"] is False


def test_health_does_not_touch_rag_service(client, monkeypatch):
    monkeypatch.setattr(main, "get_service", lambda: pytest.fail("health must not build the service"))
    assert client.get("/health").status_code == 200


# ---------- /retrieve ----------

def test_retrieve_returns_contexts(client, use_service):
    service = use_service(FakeService(contexts=[make_context(distance=0.25)]))
    response = client.post("/retrieve", json={"question": "Max password?", "top_k": 2})

    assert response.status_code == 200
    assert response.json() == {
        "question": "Max password?",
        "contexts": [
            {
                "chunk_id": "t15-password",
                "source": "requirements.md",
                "section": "Password Requirements",
                "requirement_ids": ["T15"],
                "text": "Requirement T15: Password must have maximum 15 symbols",
                "distance": 0.25,
                "score": 0.75,
            }
        ],
    }
    assert service.calls == [("retrieve", "Max password?", 2)]


def test_retrieve_without_top_k_passes_none(client, use_service):
    service = use_service(FakeService())
    client.post("/retrieve", json={"question": "q"})
    assert service.calls == [("retrieve", "q", None)]


def test_retrieve_with_no_contexts(client, use_service):
    use_service(FakeService(contexts=[]))
    response = client.post("/retrieve", json={"question": "q"})
    assert response.status_code == 200
    assert response.json()["contexts"] == []


@pytest.mark.parametrize(
    "error",
    [ValueError("Question must not be blank."), RuntimeError("Vector store is empty."), FileNotFoundError("missing")],
)
def test_retrieve_errors_return_400(client, use_service, error):
    use_service(FakeService(error=error))
    response = client.post("/retrieve", json={"question": "q"})

    assert response.status_code == 400
    assert response.json() == {"detail": str(error)}


# ---------- /ask ----------

def test_ask_returns_answer_contexts_and_usage(client, use_service):
    result = LLMResult(
        text="Maximum is 15 [T15].",
        model="claude-test",
        usage=LLMUsage(input_tokens=120, output_tokens=12, approximate_cost_usd=0.001),
    )
    service = use_service(FakeService(result=result))
    response = client.post("/ask", json={"question": "Max password?", "top_k": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "Max password?"
    assert body["answer"] == "Maximum is 15 [T15]."
    assert body["model"] == "claude-test"
    assert body["usage"] == {"input_tokens": 120, "output_tokens": 12, "approximate_cost_usd": 0.001}
    assert [c["requirement_ids"] for c in body["contexts"]] == [["T15"]]
    assert service.calls == [("ask", "Max password?", 3)]


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (LLMConfigurationError("no key"), 503),
        (LLMAuthenticationError("auth"), 503),
        (LLMRateLimitError("limit"), 429),
        (LLMTimeoutError("timeout"), 504),
        (LLMConnectionError("connection"), 502),
        (LLMProviderError("provider"), 502),
        (ValueError("blank"), 400),
        (RuntimeError("stale index"), 400),
        (FileNotFoundError("missing kb"), 400),
    ],
)
def test_ask_errors_map_to_http_statuses(client, use_service, error, status):
    use_service(FakeService(error=error))
    response = client.post("/ask", json={"question": "q"})

    assert response.status_code == status
    assert response.json() == {"detail": str(error)}


def test_ask_unexpected_error_is_not_hidden(use_service, make_settings, monkeypatch):
    monkeypatch.setattr(main, "settings", make_settings())
    use_service(FakeService(error=KeyError("bug")))
    response = TestClient(main.app, raise_server_exceptions=False).post("/ask", json={"question": "q"})
    assert response.status_code == 500


# ---------- request validation (both POST endpoints) ----------

@pytest.mark.parametrize("path", ["/retrieve", "/ask"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": ""},
        {"question": "x" * 4001},
        {"question": "q", "top_k": 0},
        {"question": "q", "top_k": 11},
        {"question": "q", "top_k": "many"},
        {"question": 123},
    ],
)
def test_invalid_requests_return_422(client, use_service, path, payload):
    service = use_service(FakeService())
    response = client.post(path, json=payload)

    assert response.status_code == 422
    assert service.calls == []


@pytest.mark.parametrize("path", ["/retrieve", "/ask"])
def test_non_json_body_returns_422(client, use_service, path):
    use_service(FakeService())
    response = client.post(path, content="question=q", headers={"Content-Type": "text/plain"})
    assert response.status_code == 422


@pytest.mark.parametrize(("method", "path"), [("get", "/ask"), ("get", "/retrieve"), ("post", "/health")])
def test_wrong_http_method_returns_405(client, method, path):
    assert getattr(client, method)(path).status_code == 405


# ---------- _raise_http_for_llm_error ----------

@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (LLMAuthenticationError("auth"), 503),
        (LLMConfigurationError("config"), 503),
        (LLMRateLimitError("limit"), 429),
        (LLMTimeoutError("timeout"), 504),
        (LLMConnectionError("connection"), 502),
        (LLMProviderError("provider"), 502),
    ],
)
def test_llm_errors_map_to_specific_http_statuses(exc, status):
    with pytest.raises(HTTPException) as caught:
        main._raise_http_for_llm_error(exc)

    assert caught.value.status_code == status
    assert caught.value.detail == str(exc)
    assert caught.value.__cause__ is exc


def test_unknown_error_is_re_raised_unchanged():
    error = KeyError("other")
    with pytest.raises(KeyError) as caught:
        main._raise_http_for_llm_error(error)
    assert caught.value is error


# ---------- get_service ----------

def test_get_service_is_cached(monkeypatch):
    main.get_service.cache_clear()
    created = []

    class Recorder:
        def __init__(self, settings):
            created.append(settings)

    monkeypatch.setattr(main, "RAGService", Recorder)
    try:
        assert main.get_service() is main.get_service()
        assert created == [main.settings]
    finally:
        main.get_service.cache_clear()
