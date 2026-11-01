from app.llm import ask_llm, USAGE
from typing import Annotated

from fastapi import Depends, FastAPI

from app.config import Settings, get_settings

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
