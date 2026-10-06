from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class RetrieveRequest(AskRequest):
    pass


class ContextResponse(BaseModel):
    chunk_id: str
    source: str
    section: str
    requirement_ids: list[str]
    text: str
    distance: float | None = None
    score: float | None = None


class UsageResponse(BaseModel):
    input_tokens: int
    output_tokens: int
    approximate_cost_usd: float | None = None


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    contexts: list[ContextResponse]
    usage: UsageResponse


class RetrieveResponse(BaseModel):
    question: str
    contexts: list[ContextResponse]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    anthropic_model: str
    api_key_configured: bool
    knowledge_base_exists: bool
