from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.constants import DIETARY_PREFERENCES, normalize_preferences
from app.database.connection import get_db
from app.models.models import DietaryPreference, User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.security import (
    burn_password_check,
    create_access_token,
    hash_password,
    login_limiter,
    password_problem,
    register_limiter,
    verify_password,
)
from app.services.serializers import user_payload

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def resolve_preferences(db: Session, names: list[str]) -> list[DietaryPreference]:
    """Validate names and return the matching DietaryPreference rows."""
    valid, invalid = normalize_preferences(names)

    if invalid:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown dietary preference: {', '.join(invalid)}. "
                f"Allowed: {', '.join(DIETARY_PREFERENCES)}"
            ),
        )

    rows = []
    for name in valid:
        row = (
            db.query(DietaryPreference)
            .filter(func.lower(DietaryPreference.name) == name.lower())
            .first()
        )
        if row is None:
            row = DietaryPreference(name=name)
            db.add(row)
            db.flush()
        rows.append(row)

    return rows


def _auth_response(message: str, user: User) -> dict:
    return {
        "message": message,
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": user_payload(user),
    }


@router.post("/register", status_code=201)
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip_key = f"register:{_client_ip(request)}"
    wait = register_limiter.retry_after(ip_key)
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many sign-up attempts. Please try again later.",
            headers={"Retry-After": str(wait)},
        )
    register_limiter.hit(ip_key)

    problem = password_problem(data.password)
    if problem:
        raise HTTPException(status_code=400, detail=problem)

    email = data.email.strip().lower()

    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    preferences = resolve_preferences(db, data.dietary_preferences)

    user = User(
        name=f"{data.first_name} {data.last_name}",
        email=email,
        password=hash_password(data.password),
    )
    user.dietary_preferences = preferences

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

    return _auth_response("Account created successfully", user)


@router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()
    key = f"login:{_client_ip(request)}:{email}"

    wait = login_limiter.retry_after(key)
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Too many failed attempts. Please try again later.",
            headers={"Retry-After": str(wait)},
        )

    user = db.query(User).filter(func.lower(User.email) == email).first()

    if user is None:
        burn_password_check(data.password)
        valid = False
    else:
        valid = verify_password(data.password, user.password)

    if not valid:
        login_limiter.hit(key)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    login_limiter.clear(key)
    return _auth_response("Login successful", user)
