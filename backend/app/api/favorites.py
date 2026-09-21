from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Favorite, Restaurant, User
from app.security import get_current_user
from app.services.serializers import restaurant_cards

router = APIRouter(prefix="/favorites", tags=["Favorites"])


def _get_restaurant(db: Session, restaurant_id: int) -> Restaurant:
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("")
def get_favorites(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Restaurant)
        .join(Favorite, Favorite.restaurant_id == Restaurant.id)
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.id.desc())
        .all()
    )

    cards = restaurant_cards(db, [(r, None) for r in rows])
    for card in cards:
        card["restaurant_id"] = card["id"]

    return {"favorites": cards, "count": len(cards)}


@router.get("/check/{restaurant_id}")
def check_favorite(
    restaurant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exists = (
        db.query(Favorite.id)
        .filter(
            Favorite.user_id == user.id,
            Favorite.restaurant_id == restaurant_id,
        )
        .first()
        is not None
    )
    return {"restaurant_id": restaurant_id, "favorite": exists}


@router.post("/{restaurant_id}")
def add_favorite(
    restaurant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_restaurant(db, restaurant_id)

    existing = (
        db.query(Favorite)
        .filter(
            Favorite.user_id == user.id,
            Favorite.restaurant_id == restaurant_id,
        )
        .first()
    )
    if existing:
        return {
            "message": "Restaurant already in favorites",
            "favorite": True,
            "restaurant_id": restaurant_id,
        }

    try:
        db.add(Favorite(user_id=user.id, restaurant_id=restaurant_id))
        db.commit()
    except IntegrityError:
        # double-click race: the other request already saved it
        db.rollback()

    return {
        "message": "Restaurant added to favorites",
        "favorite": True,
        "restaurant_id": restaurant_id,
    }


@router.delete("/{restaurant_id}")
def remove_favorite(
    restaurant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_restaurant(db, restaurant_id)

    db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.restaurant_id == restaurant_id,
    ).delete()
    db.commit()

    return {
        "message": "Restaurant removed from favorites",
        "favorite": False,
        "restaurant_id": restaurant_id,
    }
