from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Favorite, Restaurant

router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)


@router.get("/{user_id}")
def get_favorites(
    user_id: int,
    db: Session = Depends(get_db)
):
    favorites = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id)
        .all()
    )

    result = []

    for favorite in favorites:
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == favorite.restaurant_id
        ).first()

        if restaurant:
            result.append({
                "id": favorite.id,
                "restaurant_id": restaurant.id,
                "name": restaurant.name,
                "cuisine": restaurant.cuisine,
                "location": restaurant.location,
                "rating": restaurant.rating,
                "image_url": restaurant.image_url
            })

    return result


@router.post("/{user_id}/{restaurant_id}")
def add_favorite(
    user_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.restaurant_id == restaurant_id
    ).first()

    if existing:
        return {
            "message": "Already in favorites",
            "favorite": True
        }

    favorite = Favorite(
        user_id=user_id,
        restaurant_id=restaurant_id
    )

    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return {
        "message": "Restaurant added to favorites",
        "favorite": True,
        "restaurant_id": restaurant_id
    }


@router.delete("/{user_id}/{restaurant_id}")
def remove_favorite(
    user_id: int,
    restaurant_id: int,
    db: Session = Depends(get_db)
):
    favorite = db.query(Favorite).filter(
        Favorite.user_id == user_id,
        Favorite.restaurant_id == restaurant_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=404,
            detail="Favorite not found"
        )

    db.delete(favorite)
    db.commit()

    return {
        "message": "Restaurant removed from favorites",
        "favorite": False,
        "restaurant_id": restaurant_id
    }
