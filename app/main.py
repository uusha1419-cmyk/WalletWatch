from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

from app.config import Settings, get_settings
from app.llm import USAGE, ask_llm, chat
from app.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Examate RAG starter", version="0.1.0")

SettingsDep = Annotated[Settings, Depends(get_settings)]


@app.get("/health")
def health(settings: SettingsDep) -> dict:
    """Liveness: the process is up. Must be fast and must not call the LLM or the DB."""
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.post("/llm/test")
def llm_test(body: dict):
    return ask_llm(body.get("prompt", "Say hello"))


@app.get("/usage")
def usage():
    return USAGE


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        return chat(req.message)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="LLM unavailable, try again") from e
