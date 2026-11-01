from app import llm


class Meta:
    prompt_token_count = 10
    candidates_token_count = 5


class R:
    text = "hi"
    usage_metadata = Meta()


def test_fallback(monkeypatch):
    calls = []

    class Models:
        def generate_content(self, model, contents):
            calls.append(model)
            if model == llm.PRIMARY:
                raise RuntimeError("boom")
            return R()

    class C:
        models = Models()

    monkeypatch.setattr(llm, "client", lambda: C())
    out = llm.ask_llm("test")
    assert out["model"] == llm.FALLBACK
    assert calls == [llm.PRIMARY, llm.FALLBACK]