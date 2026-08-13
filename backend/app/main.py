from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.recommendations import router as recommendation_router
from app.database.connection import engine, Base
from app.models.models import *
from app.api.restaurants import router as restaurant_router
from app.api.auth import router as auth_router
from app.api.favorites import router as favorites_router
Base.metadata.create_all(bind=engine)

app = FastAPI(title="DineSmart AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(recommendation_router)
app.include_router(restaurant_router)
app.include_router(auth_router)
app.include_router(favorites_router)

@app.get("/")
def root():
    return {
        "message": "DineSmart AI API is running"
    }


@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "success",
            "message": "PostgreSQL connected successfully"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
