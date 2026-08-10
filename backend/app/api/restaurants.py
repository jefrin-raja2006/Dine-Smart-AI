from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Restaurant

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.get("/")
def get_restaurants(db: Session = Depends(get_db)):
    return db.query(Restaurant).all()


@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(
        Restaurant.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return restaurant


@router.post("/")
def create_restaurant(
    name: str,
    cuisine: str,
    location: str,
    rating: float = 0.0,
    image_url: str = "",
    db: Session = Depends(get_db)
):
    restaurant = Restaurant(
        name=name,
        cuisine=cuisine,
        location=location,
        rating=rating,
        image_url=image_url
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant
