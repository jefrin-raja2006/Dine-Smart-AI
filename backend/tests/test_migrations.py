"""An existing (pre-v2) database must upgrade in place without losing data."""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.migrations import run_migrations, seed_dietary_preferences

LEGACY_DDL = [
    "CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(150) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL)",
    "CREATE TABLE restaurants (id INTEGER PRIMARY KEY, osm_id VARCHAR(100) UNIQUE, name VARCHAR(150) NOT NULL, cuisine VARCHAR(100), location VARCHAR(150), rating FLOAT, image_url TEXT)",
    "CREATE TABLE favorites (id INTEGER PRIMARY KEY, user_id INTEGER, restaurant_id INTEGER)",
    "CREATE TABLE reviews (id INTEGER PRIMARY KEY, user_id INTEGER, restaurant_id INTEGER, rating INTEGER, text TEXT NOT NULL, created_at DATETIME, sentiment VARCHAR(30), sentiment_score FLOAT, trust_score FLOAT)",
    "CREATE TABLE dietary_preferences (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL UNIQUE)",
]


def legacy_engine():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        for ddl in LEGACY_DDL:
            conn.execute(text(ddl))
        conn.execute(text("INSERT INTO users VALUES (1, 'Old User', 'old@example.com', 'hash')"))
        conn.execute(text("INSERT INTO restaurants (id, osm_id, name) VALUES (1, 'node_1', 'Old Place')"))
        # duplicate favorites that the old app could create through a race
        conn.execute(text("INSERT INTO favorites VALUES (1, 1, 1), (2, 1, 1), (3, 1, 1)"))
        conn.execute(text("INSERT INTO dietary_preferences VALUES (1, 'Vegetarian')"))
    return engine


def test_upgrade_adds_columns_keeps_rows_and_dedupes():
    engine = legacy_engine()
    run_migrations(engine)
    seed_dietary_preferences(engine)

    inspector = inspect(engine)
    assert {"latitude", "longitude", "amenity", "phone", "website", "opening_hours", "diet_tags"} <= {
        c["name"] for c in inspector.get_columns("restaurants")}
    assert "analysis_json" in {c["name"] for c in inspector.get_columns("reviews")}

    with engine.connect() as conn:
        assert conn.execute(text("SELECT name FROM restaurants")).scalar() == "Old Place"
        assert conn.execute(text("SELECT created_at FROM users")).scalar() is not None
        assert conn.execute(text("SELECT COUNT(*) FROM favorites")).scalar() == 1     # de-duplicated
        names = [r[0] for r in conn.execute(text("SELECT name FROM dietary_preferences ORDER BY id"))]
        assert names.count("Vegetarian") == 1 and len(names) == 5                    # no duplicate seeds


def test_migration_is_idempotent():
    engine = legacy_engine()
    for _ in range(3):
        run_migrations(engine)
        seed_dietary_preferences(engine)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM users")).scalar() == 1


def test_unique_index_now_blocks_duplicate_favorites():
    import pytest
    from sqlalchemy.exc import IntegrityError

    engine = legacy_engine()
    run_migrations(engine)
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO favorites (user_id, restaurant_id) VALUES (1, 1)"))
