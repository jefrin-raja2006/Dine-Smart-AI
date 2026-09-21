import time
from datetime import timedelta

import jwt
import pytest

from app import security


def test_password_hash_roundtrip():
    hashed = security.hash_password("s3cretpass")
    assert security.verify_password("s3cretpass", hashed)
    assert not security.verify_password("wrong", hashed)


def test_verify_handles_garbage_hash():
    assert security.verify_password("x", "not-a-bcrypt-hash") is False


def test_password_rules():
    assert security.password_problem("short")
    assert security.password_problem("a" * 73)
    assert security.password_problem("é" * 40)  # 80 bytes
    assert security.password_problem("longenough1") is None


def test_token_roundtrip_and_expiry():
    assert security.decode_access_token(security.create_access_token(42)) == 42

    expired = security.create_access_token(42, timedelta(seconds=-5))
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_access_token(expired)


def test_token_with_wrong_key_rejected():
    forged = jwt.encode({"sub": "1", "exp": time.time() + 60}, "other-key" * 5, "HS256")
    with pytest.raises(jwt.PyJWTError):
        security.decode_access_token(forged)


def test_alg_none_rejected():
    forged = jwt.encode({"sub": "1", "exp": time.time() + 60}, None, algorithm="none")
    with pytest.raises(jwt.PyJWTError):
        security.decode_access_token(forged)


def test_rate_limiter_window():
    limiter = security.RateLimiter(max_events=2, window_seconds=60)
    assert limiter.retry_after("k") == 0
    limiter.hit("k")
    limiter.hit("k")
    assert limiter.retry_after("k") > 0
    assert limiter.retry_after("other") == 0
    limiter.clear("k")
    assert limiter.retry_after("k") == 0


def test_rate_limiter_expires():
    limiter = security.RateLimiter(max_events=1, window_seconds=1)
    limiter.hit("k")
    assert limiter.retry_after("k") > 0
    time.sleep(1.1)
    assert limiter.retry_after("k") == 0


def test_production_requires_strong_secret(monkeypatch):
    from app import config

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "short")
    with pytest.raises(RuntimeError):
        config.load_settings()

    monkeypatch.setenv("SECRET_KEY", "x" * 40)
    assert config.load_settings().is_production


def test_postgres_url_is_normalised(monkeypatch):
    from app import config

    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert config.load_settings().database_url.startswith("postgresql://")
