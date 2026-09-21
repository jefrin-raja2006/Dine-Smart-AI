"""Lightweight, idempotent schema upgrades.

`Base.metadata.create_all()` only creates missing tables; it never alters a
table that already exists. Because DineSmart AI was already running with real
data, new columns/indexes are applied here so an existing database upgrades
in place without losing anything.

Every step checks before it acts, so running this on every startup is safe.

For a larger team/production system, replace this with Alembic.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.constants import DIETARY_PREFERENCES

logger = logging.getLogger("dinesmart.migrations")


# =========================================================
# COLUMN ADDITIONS
# =========================================================

COLUMN_ADDITIONS: dict[str, list[tuple[str, str]]] = {
    "users": [
        ("created_at", "TIMESTAMP"),

        # User role:
        # customer / owner / admin
        ("role", "VARCHAR(30) DEFAULT 'customer'"),
    ],

    "restaurants": [
        ("latitude", "DOUBLE PRECISION"),
        ("longitude", "DOUBLE PRECISION"),
        ("amenity", "VARCHAR(50)"),
        ("phone", "VARCHAR(100)"),
        ("website", "TEXT"),
        ("opening_hours", "TEXT"),
        ("diet_tags", "TEXT"),

        # Restaurant owner.
        # NULL is allowed for restaurants discovered from OSM.
        ("owner_id", "INTEGER"),
    ],

    "reviews": [
        ("analysis_json", "TEXT"),
    ],
}


# =========================================================
# NORMAL INDEXES
# =========================================================

# (index name, table, columns)
INDEXES: list[tuple[str, str, str]] = [
    ("ix_users_role", "users", "role"),

    ("ix_restaurants_latitude", "restaurants", "latitude"),
    ("ix_restaurants_longitude", "restaurants", "longitude"),
    ("ix_restaurants_owner_id", "restaurants", "owner_id"),

    ("ix_reviews_user_id", "reviews", "user_id"),
    ("ix_reviews_restaurant_id", "reviews", "restaurant_id"),

    ("ix_favorites_user_id", "favorites", "user_id"),
    ("ix_favorites_restaurant_id", "favorites", "restaurant_id"),
]


# =========================================================
# UNIQUE INDEXES
# =========================================================

# (unique index name, table, columns, which duplicate to keep)
UNIQUE_INDEXES: list[tuple[str, str, str, str]] = [
    (
        "uq_favorites_user_restaurant",
        "favorites",
        "user_id, restaurant_id",
        "MIN",
    ),
    (
        "uq_reviews_user_restaurant",
        "reviews",
        "user_id, restaurant_id",
        "MAX",
    ),
]


# =========================================================
# RUN MIGRATIONS
# =========================================================

def run_migrations(engine: Engine) -> None:
    """Apply safe, repeatable database schema upgrades."""

    with engine.begin() as conn:

        # Inspect using the SAME connection/transaction
        # that is performing the changes.
        inspector = inspect(conn)

        # =====================================================
        # 1. ADD MISSING COLUMNS
        # =====================================================

        for table, columns in COLUMN_ADDITIONS.items():

            if not inspector.has_table(table):
                continue

            existing = {
                column["name"]
                for column in inspector.get_columns(table)
            }

            for column, ddl in columns:

                if column not in existing:

                    conn.execute(
                        text(
                            f"ALTER TABLE {table} "
                            f"ADD COLUMN {column} {ddl}"
                        )
                    )

                    logger.info(
                        "Added column %s.%s",
                        table,
                        column,
                    )

        # =====================================================
        # 2. FIX EXISTING USER ROLES
        # =====================================================
        #
        # Existing users were created before role support.
        # They should become normal customers.
        #

        if inspector.has_table("users"):

            conn.execute(
                text(
                    """
                    UPDATE users
                    SET role = 'customer'
                    WHERE role IS NULL
                       OR role = ''
                    """
                )
            )

        # =====================================================
        # 3. CREATED_AT BACKFILL
        # =====================================================

        if inspector.has_table("users"):

            conn.execute(
                text(
                    """
                    UPDATE users
                    SET created_at = CURRENT_TIMESTAMP
                    WHERE created_at IS NULL
                    """
                )
            )

        # =====================================================
        # 4. NORMAL INDEXES
        # =====================================================

        for name, table, columns in INDEXES:

            if inspector.has_table(table):

                conn.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS "
                        f"{name} "
                        f"ON {table} ({columns})"
                    )
                )

        # =====================================================
        # 5. UNIQUE INDEXES
        # =====================================================
        #
        # Remove legacy duplicate records before creating the
        # unique indexes.
        #

        for name, table, columns, keep in UNIQUE_INDEXES:

            if not inspector.has_table(table):
                continue

            conn.execute(
                text(
                    f"DELETE FROM {table} "
                    f"WHERE id NOT IN ("
                    f"SELECT {keep}(id) "
                    f"FROM {table} "
                    f"GROUP BY {columns}"
                    f")"
                )
            )

            conn.execute(
                text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS "
                    f"{name} "
                    f"ON {table} ({columns})"
                )
            )


# =========================================================
# SEED DIETARY PREFERENCES
# =========================================================

def seed_dietary_preferences(engine: Engine) -> None:
    """Make sure canonical dietary preference rows exist."""

    from sqlalchemy.orm import Session

    from app.models.models import DietaryPreference

    with Session(engine) as session:

        existing = {
            name.lower()
            for (name,) in session.query(
                DietaryPreference.name
            ).all()
        }

        for name in DIETARY_PREFERENCES:

            if name.lower() not in existing:

                session.add(
                    DietaryPreference(name=name)
                )

        session.commit()