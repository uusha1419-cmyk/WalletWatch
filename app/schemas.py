"""Request and response models. Empty for now; you add these from Session 4."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatAnswer(BaseModel):
    """What the LLM must return."""

    answer: str
    key_points: list[str] = Field(description="Up to 3 short bullet points")
    confidence: str = Field(description="One of: high, medium, low")


class ChatResponse(ChatAnswer):
    """What our API returns."""

    model: str
    fallback_used: bool
    input_tokens: int
    output_tokens: int
