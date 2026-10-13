
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database.connection import Base, engine
from app.migrations import run_migrations, seed_dietary_preferences
from app.models import models  # noqa: F401

from app.api.owner import router as owner_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.restaurants import router as restaurant_router
from app.api.reviews import router as reviews_router
from app.api.favorites import router as favorites_router
from app.api.recommendations import router as recommendation_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dinesmart")


# =========================================================
# STARTUP
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    seed_dietary_preferences(engine)

    logger.info(
        "DineSmart AI API started (%s)",
        settings.environment,
    )

    yield


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="DineSmart AI API",
    description="AI-powered personalized restaurant discovery platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)


# =========================================================
# CORS
# =========================================================

# Keep the configured origins and add common local Vite origins.
configured_origins = getattr(settings, "cors_origins", [])

if isinstance(configured_origins, str):
    configured_origins = [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]

local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

allowed_origins = list(
    dict.fromkeys(list(configured_origins) + local_origins)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# SECURITY HEADERS
# =========================================================

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers.setdefault(
        "X-Content-Type-Options", "nosniff"
    )
    response.headers.setdefault(
        "X-Frame-Options", "DENY"
    )
    response.headers.setdefault(
        "Referrer-Policy", "no-referrer"
    )

    return response


# =========================================================
# ROUTERS
# =========================================================

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(restaurant_router)
app.include_router(reviews_router)
app.include_router(favorites_router)
app.include_router(recommendation_router)
app.include_router(owner_router)


# =========================================================
# SYSTEM ENDPOINTS
# =========================================================

@app.get("/", tags=["System"])
def root():
    return {
        "message": "DineSmart AI API is running",
        "status": "online",
        "version": app.version,
    }


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok"}


@app.get("/db-test", tags=["System"])
def db_test():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "message": "PostgreSQL connected successfully",
        }

    except Exception:
        logger.exception("Database health check failed")

        return {
            "status": "error",
            "message": "Database connection failed",
        }
