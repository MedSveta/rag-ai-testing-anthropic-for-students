from types import SimpleNamespace

import anthropic
import httpx2  # HTTP library used internally by the anthropic SDK
import pytest

from app.llm_client import (
    AnthropicLLMClient,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResult,
    LLMTimeoutError,
    LLMUsage,
)

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _response(status: int) -> httpx2.Response:
    return httpx2.Response(status, request=REQUEST)


def _message(blocks, input_tokens=10, output_tokens=5, model="claude-real-model-id"):
    return SimpleNamespace(
        content=blocks,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        model=model,
    )


def _text(text):
    return SimpleNamespace(type="text", text=text)


class FakeMessages:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def make_client():
    def _make(result=None, error=None, **kwargs):
        client = AnthropicLLMClient(api_key="test-key", model="claude-test", **kwargs)
        client.client.messages = FakeMessages(result if result is not None else _message([_text("ok")]), error)
        return client

    return _make


# ---------- constructor ----------

@pytest.mark.parametrize("api_key", ["", None])
def test_missing_api_key_raises_configuration_error(api_key):
    with pytest.raises(LLMConfigurationError, match="ANTHROPIC_API_KEY"):
        AnthropicLLMClient(api_key=api_key, model="claude-test")


def test_constructor_stores_parameters():
    client = AnthropicLLMClient(
        api_key="k",
        model="m",
        max_output_tokens=50,
        input_cost_per_million=1.0,
        output_cost_per_million=2.0,
    )
    assert client.model == "m"
    assert client.max_output_tokens == 50
    assert client.input_cost_per_million == 1.0
    assert client.output_cost_per_million == 2.0


def test_constructor_does_not_call_api():
    # Creating the client must work offline: no request is sent until generate().
    AnthropicLLMClient(api_key="k", model="m")


# ---------- request ----------

def test_generate_sends_expected_request(make_client):
    client = make_client(max_output_tokens=123)
    client.generate("system text", "user text")

    assert client.client.messages.calls == [
        {
            "model": "claude-test",
            "max_tokens": 123,
            "system": "system text",
            "messages": [{"role": "user", "content": "user text"}],
        }
    ]


# ---------- response parsing ----------

def test_generate_returns_text_model_and_usage(make_client):
    client = make_client(_message([_text("Answer [T15]")], input_tokens=100, output_tokens=7))
    result = client.generate("s", "u")

    assert result == LLMResult(
        text="Answer [T15]",
        model="claude-real-model-id",
        usage=LLMUsage(input_tokens=100, output_tokens=7, approximate_cost_usd=None),
    )


def test_text_blocks_are_joined_and_other_blocks_skipped(make_client):
    blocks = [
        _text("  Part one. "),
        SimpleNamespace(type="thinking", thinking="hidden"),
        _text("Part two.  "),
    ]
    result = make_client(_message(blocks)).generate("s", "u")
    assert result.text == "Part one. Part two."


def test_empty_content_gives_empty_text(make_client):
    assert make_client(_message([])).generate("s", "u").text == ""


def test_model_falls_back_to_configured_model(make_client):
    message = SimpleNamespace(content=[_text("x")], usage=SimpleNamespace(input_tokens=1, output_tokens=1))
    assert make_client(message).generate("s", "u").model == "claude-test"


def test_missing_usage_values_become_zero(make_client):
    message = SimpleNamespace(content=[_text("x")], usage=SimpleNamespace(input_tokens=None), model="m")
    usage = make_client(message).generate("s", "u").usage
    assert (usage.input_tokens, usage.output_tokens) == (0, 0)


# ---------- cost ----------

def test_cost_is_none_when_prices_are_zero(make_client):
    assert make_client().generate("s", "u").usage.approximate_cost_usd is None


def test_cost_is_calculated_from_prices(make_client):
    client = make_client(
        _message([_text("x")], input_tokens=1_000_000, output_tokens=500_000),
        input_cost_per_million=3.0,
        output_cost_per_million=15.0,
    )
    assert client.generate("s", "u").usage.approximate_cost_usd == pytest.approx(10.5)


def test_cost_with_only_input_price(make_client):
    client = make_client(
        _message([_text("x")], input_tokens=2_000, output_tokens=1_000),
        input_cost_per_million=1.0,
    )
    assert client.generate("s", "u").usage.approximate_cost_usd == pytest.approx(0.002)


# ---------- error mapping ----------

@pytest.mark.parametrize(
    ("sdk_error", "expected", "message"),
    [
        (anthropic.AuthenticationError("bad key", response=_response(401), body=None),
         LLMAuthenticationError, "authentication failed"),
        (anthropic.RateLimitError("slow down", response=_response(429), body=None),
         LLMRateLimitError, "rate limit"),
        (anthropic.APITimeoutError(request=REQUEST),
         LLMTimeoutError, "timed out"),
        (anthropic.APIConnectionError(request=REQUEST),
         LLMConnectionError, "Could not connect"),
        (anthropic.InternalServerError("boom", response=_response(500), body=None),
         LLMProviderError, "HTTP 500"),
        (anthropic.BadRequestError("bad", response=_response(400), body=None),
         LLMProviderError, "HTTP 400"),
        (anthropic.APIError("generic", REQUEST, body=None),
         LLMProviderError, "request failed"),
    ],
)
def test_sdk_errors_are_mapped(make_client, sdk_error, expected, message):
    client = make_client(error=sdk_error)
    with pytest.raises(expected, match=message) as caught:
        client.generate("s", "u")
    assert caught.value.__cause__ is sdk_error


def test_error_messages_do_not_leak_api_key(make_client):
    client = make_client(error=anthropic.AuthenticationError("bad", response=_response(401), body=None))
    with pytest.raises(LLMAuthenticationError) as caught:
        client.generate("s", "u")
    assert "test-key" not in str(caught.value)


def test_non_anthropic_errors_are_not_wrapped(make_client):
    with pytest.raises(KeyError):
        make_client(error=KeyError("unexpected")).generate("s", "u")


@pytest.mark.parametrize(
    "error_class",
    [
        LLMConfigurationError,
        LLMAuthenticationError,
        LLMRateLimitError,
        LLMTimeoutError,
        LLMConnectionError,
        LLMProviderError,
    ],
)
def test_all_llm_errors_are_runtime_errors(error_class):
    assert issubclass(error_class, RuntimeError)
