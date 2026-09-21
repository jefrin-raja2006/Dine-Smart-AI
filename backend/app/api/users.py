from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.auth import resolve_preferences
from app.database.connection import get_db
from app.models.models import Favorite, Review, User
from app.schemas.auth import PasswordChange, PreferencesUpdate, ProfileUpdate
from app.security import (
    get_current_user,
    hash_password,
    password_problem,
    verify_password,
)
from app.services.serializers import user_payload
from app.utils import iso_utc

router = APIRouter(prefix="/users", tags=["Users"])


def _profile(db: Session, user: User) -> dict:
    favorites = (
        db.query(func.count(Favorite.id)).filter(Favorite.user_id == user.id).scalar()
    )
    reviews = (
        db.query(func.count(Review.id)).filter(Review.user_id == user.id).scalar()
    )
    average_given = (
        db.query(func.avg(Review.rating)).filter(Review.user_id == user.id).scalar()
    )

    return {
        **user_payload(user),
        "member_since": iso_utc(user.created_at),
        "stats": {
            "favorites": favorites or 0,
            "reviews": reviews or 0,
            "average_rating_given": (
                round(float(average_given), 1) if average_given is not None else None
            ),
        },
    }


@router.get("/me")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _profile(db, user)


@router.put("/me")
def update_me(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.name = data.name
    db.commit()
    db.refresh(user)
    return _profile(db, user)


@router.put("/me/preferences")
def update_preferences(
    data: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.dietary_preferences = resolve_preferences(db, data.dietary_preferences)
    db.commit()
    db.refresh(user)
    return _profile(db, user)


@router.post("/me/password")
def change_password(
    data: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, user.password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    problem = password_problem(data.new_password)
    if problem:
        raise HTTPException(status_code=400, detail=problem)

    user.password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password updated"}
