"""Shared test setup.

Tests run against SQLite by default (fast). To run them against PostgreSQL:

    TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/dinesmart_test pytest

The URL is forced into DATABASE_URL *before* the app is imported, and we refuse
to run unless the database is SQLite or has "test" in its name, so the suite
can never wipe your real development data.
"""

import os

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")

if not (_TEST_URL.startswith("sqlite") or "test" in _TEST_URL.rsplit("/", 1)[-1]):
    raise RuntimeError(
        "Refusing to run tests: TEST_DATABASE_URL must be SQLite or a database "
        "whose name contains 'test' (the suite drops and recreates all tables)."
    )

os.environ["DATABASE_URL"] = _TEST_URL
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-for-hs256-0123456789"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database.connection import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.migrations import run_migrations, seed_dietary_preferences  # noqa: E402
from app.models import models  # noqa: E402,F401
from app.security import login_limiter, register_limiter  # noqa: E402
from app.services import discovery  # noqa: E402


@pytest.fixture(autouse=True)
def clean_state():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    seed_dietary_preferences(engine)
    login_limiter.reset_all()
    register_limiter.reset_all()
    discovery.clear_cache()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


_counter = {"n": 0}


@pytest.fixture
def make_user(client):
    """Register a user; returns (auth headers, user json)."""

    def _make(email=None, prefs=None, name=("Test", "User")):
        _counter["n"] += 1
        email = email or f"user{_counter['n']}@example.com"
        response = client.post(
            "/auth/register",
            json={
                "first_name": name[0],
                "last_name": name[1],
                "email": email,
                "password": "password123",
                "dietary_preferences": prefs or [],
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]

    return _make


@pytest.fixture
def make_restaurant(db):
    from app.models.models import Restaurant

    def _make(name="Test Kitchen", cuisine="Indian", lat=13.0827, lon=80.2707, **kw):
        restaurant = Restaurant(
            name=name, cuisine=cuisine, latitude=lat, longitude=lon,
            osm_id=kw.pop("osm_id", f"node_{name.replace(' ', '_')}"),
            rating=0.0, image_url="", **kw,
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        return restaurant

    return _make


def osm_node(node_id, name, lat=13.0827, lon=80.2707, **tags):
    return {
        "type": "node", "id": node_id, "lat": lat, "lon": lon,
        "tags": {"amenity": "restaurant", "name": name, **tags},
    }


@pytest.fixture
def fake_overpass(monkeypatch):
    """Replace the network call. Set `.elements` or `.fail` on the fixture."""

    class Fake:
        elements: list = []
        fail = False
        calls = 0

    fake = Fake()

    async def _fetch(latitude, longitude, radius):
        fake.calls += 1
        if fake.fail:
            raise discovery.OverpassUnavailable("boom")
        return fake.elements

    monkeypatch.setattr(discovery, "fetch_overpass", _fetch)
    return fake
