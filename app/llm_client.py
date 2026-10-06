from __future__ import annotations

from dataclasses import dataclass


class LLMConfigurationError(RuntimeError):
    pass


class LLMAuthenticationError(RuntimeError):
    pass


class LLMRateLimitError(RuntimeError):
    pass


class LLMTimeoutError(RuntimeError):
    pass


class LLMConnectionError(RuntimeError):
    pass


class LLMProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMUsage:
    input_tokens: int
    output_tokens: int
    approximate_cost_usd: float | None = None


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    usage: LLMUsage


class AnthropicLLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        max_output_tokens: int = 700,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
    ):
        if not api_key:
            raise LLMConfigurationError(
                "ANTHROPIC_API_KEY is not configured. Add it to .env or the environment."
            )

        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResult:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_output_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except self._anthropic.AuthenticationError as exc:
            raise LLMAuthenticationError(
                "Anthropic authentication failed. Check ANTHROPIC_API_KEY."
            ) from exc
        except self._anthropic.RateLimitError as exc:
            raise LLMRateLimitError(
                "Anthropic rate limit reached. Retry later or review API limits/balance."
            ) from exc
        except self._anthropic.APITimeoutError as exc:
            raise LLMTimeoutError("Anthropic API request timed out.") from exc
        except self._anthropic.APIConnectionError as exc:
            raise LLMConnectionError("Could not connect to the Anthropic API.") from exc
        except self._anthropic.APIStatusError as exc:
            status = getattr(exc, "status_code", "unknown")
            raise LLMProviderError(f"Anthropic API returned HTTP {status}.") from exc
        except self._anthropic.APIError as exc:
            raise LLMProviderError("Anthropic API request failed.") from exc

        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        ).strip()
        input_tokens = int(getattr(message.usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(message.usage, "output_tokens", 0) or 0)
        cost = None
        if self.input_cost_per_million or self.output_cost_per_million:
            cost = (
                input_tokens / 1_000_000 * self.input_cost_per_million
                + output_tokens / 1_000_000 * self.output_cost_per_million
            )
        return LLMResult(
            text=text,
            model=getattr(message, "model", self.model),
            usage=LLMUsage(input_tokens, output_tokens, cost),
        )
