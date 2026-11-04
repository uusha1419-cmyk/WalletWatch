from app import db


def test_log_usage_without_database_is_a_noop(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db.log_usage("m", 1, 2, 0.0)
    assert db.totals() is None
