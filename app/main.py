from functools import lru_cache

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.llm_client import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.rag_service import RAGService
from app.schemas import (
    AskRequest,
    AskResponse,
    ContextResponse,
    HealthResponse,
    RetrieveRequest,
    RetrieveResponse,
    UsageResponse,
)

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)


@lru_cache
def get_service() -> RAGService:
    return RAGService(settings)


def _context_response(context) -> ContextResponse:
    return ContextResponse(
        chunk_id=context.chunk_id,
        source=context.source,
        section=context.section,
        requirement_ids=list(context.requirement_ids),
        text=context.text,
        distance=context.distance,
        score=context.score,
    )


def _raise_http_for_llm_error(exc: Exception) -> None:
    if isinstance(exc, LLMAuthenticationError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if isinstance(exc, LLMRateLimitError):
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    if isinstance(exc, LLMTimeoutError):
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    if isinstance(exc, (LLMConnectionError, LLMProviderError)):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if isinstance(exc, LLMConfigurationError):
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    raise exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        anthropic_model=settings.anthropic_model,
        api_key_configured=bool(settings.anthropic_api_key),
        knowledge_base_exists=settings.resolved_knowledge_path.exists(),
    )


@app.post("/retrieve", response_model=RetrieveResponse)
def retrieve(request: RetrieveRequest) -> RetrieveResponse:
    try:
        contexts = get_service().retrieve(request.question, request.top_k)
        return RetrieveResponse(
            question=request.question,
            contexts=[_context_response(c) for c in contexts],
        )
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        result, contexts = get_service().ask(request.question, request.top_k)
        return AskResponse(
            question=request.question,
            answer=result.text,
            model=result.model,
            contexts=[_context_response(c) for c in contexts],
            usage=UsageResponse(
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                approximate_cost_usd=result.usage.approximate_cost_usd,
            ),
        )
    except (
        LLMConfigurationError,
        LLMAuthenticationError,
        LLMRateLimitError,
        LLMTimeoutError,
        LLMConnectionError,
        LLMProviderError,
    ) as exc:
        _raise_http_for_llm_error(exc)
        raise AssertionError("unreachable")
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
