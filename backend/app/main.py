import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database.connection import Base, engine
from app.migrations import run_migrations, seed_dietary_preferences
from app.models import models  # noqa: F401  (registers the tables)
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
# STARTUP: create tables, upgrade older databases, seed data
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations(engine)
    seed_dietary_preferences(engine)
    logger.info("DineSmart AI API started (%s)", settings.environment)
    yield


app = FastAPI(
    title="DineSmart AI API",
    description="AI-powered personalized restaurant discovery platform",
    version="2.0.0",
    lifespan=lifespan,
    # hide the interactive docs in production
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,          # we use bearer tokens, not cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


# =========================================================
# ROUTES
# =========================================================

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(restaurant_router)
app.include_router(reviews_router)
app.include_router(favorites_router)
app.include_router(recommendation_router)
app.include_router(recommendation_router)
app.include_router(owner_router)
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
        return {"status": "success", "message": "PostgreSQL connected successfully"}
    except Exception:
        logger.exception("Database health check failed")
        # never echo the raw error: it can contain the connection string
        return {"status": "error", "message": "Database connection failed"}
