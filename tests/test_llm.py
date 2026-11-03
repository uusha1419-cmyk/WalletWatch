from fastapi.testclient import TestClient

from app import llm, main


class Meta:
    prompt_token_count = 10
    candidates_token_count = 5


class R:
    text = '{"answer": "hi", "key_points": ["a"], "confidence": "high"}'
    parsed = None
    usage_metadata = Meta()


def fake_client(fail_models):
    calls = []

    class Models:
        def generate_content(self, model, contents, config=None):
            calls.append(model)
            if model in fail_models:
                raise RuntimeError("boom")
            return R()

    class C:
        models = Models()

    return C(), calls


def test_fallback_after_retry(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    c, calls = fake_client({llm.PRIMARY})
    monkeypatch.setattr(llm, "client", lambda: c)
    out = llm.ask_llm("test")
    assert out["model"] == llm.FALLBACK
    assert calls == [llm.PRIMARY, llm.PRIMARY, llm.FALLBACK]


def test_chat_returns_structured_json(monkeypatch):
    c, _ = fake_client(set())
    monkeypatch.setattr(llm, "client", lambda: c)
    out = llm.chat("How many breaches?")
    assert out["answer"] == "hi"
    assert out["confidence"] == "high"
    assert out["fallback_used"] is False
    assert out["input_tokens"] == 10


def test_chat_endpoint(monkeypatch):
    monkeypatch.setattr(
        main,
        "chat",
        lambda m: {
            "answer": "hi",
            "key_points": [],
            "confidence": "low",
            "model": "x",
            "fallback_used": False,
            "input_tokens": 1,
            "output_tokens": 1,
        },
    )
    r = TestClient(main.app).post("/chat", json={"message": "hello"})
    assert r.status_code == 200
    assert r.json()["confidence"] == "low"
    assert TestClient(main.app).post("/chat", json={"message": ""}).status_code == 422
