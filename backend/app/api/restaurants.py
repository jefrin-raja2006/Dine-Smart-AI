from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Favorite, Restaurant, User
from app.security import get_current_user, get_optional_user
from app.services import dietary
from app.services.discovery import OverpassUnavailable, discover
from app.services.geo import haversine_km
from app.services.recommendation_service import profile_for_user, rank_restaurants
from app.services.recommender import build_profile
from app.services.serializers import (
    menu_items_by_restaurant,
    restaurant_card,
    restaurant_cards,
    review_stats,
)

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# =========================================================
# LIST RESTAURANTS SAVED IN THE DATABASE
# =========================================================

@router.get("/")
def get_restaurants(
    q: str | None = Query(None, max_length=100),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)

    if q:
        pattern = f"%{q.strip()}%"
        query = query.filter(
            Restaurant.name.ilike(pattern) | Restaurant.cuisine.ilike(pattern)
        )

    rows = query.order_by(Restaurant.id).offset(offset).limit(limit).all()
    return restaurant_cards(db, [(r, None) for r in rows])


# =========================================================
# NEARBY RESTAURANTS (OpenStreetMap -> PostgreSQL sync)
# =========================================================

@router.get("/nearby")
async def get_nearby_restaurants(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: int = Query(5000, ge=1000, le=15000),
    db: Session = Depends(get_db),
):
    try:
        result = await discover(db, latitude, longitude, radius)
    except OverpassUnavailable:
        raise HTTPException(
            status_code=503,
            detail=(
                "The restaurant data service (OpenStreetMap) is temporarily "
                "unavailable. Please try again in a moment."
            ),
        )

    cards = restaurant_cards(db, result.restaurants)

    return {
        "status": "success",
        "source": "OpenStreetMap" if result.source == "openstreetmap" else "Saved data",
        "database": "PostgreSQL",
        "count": len(cards),
        "search_location": {
            "latitude": latitude,
            "longitude": longitude,
            "radius": result.radius_used,
        },
        "restaurants": cards,
        "message": result.message,
    }


# =========================================================
# ONE RESTAURANT (with menu, dietary evidence and - if logged in - AI match)
# =========================================================

@router.get("/{restaurant_id}")
def get_restaurant(
    restaurant_id: int,
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    distance = None
    if (
        latitude is not None
        and longitude is not None
        and restaurant.latitude is not None
        and restaurant.longitude is not None
    ):
        distance = haversine_km(
            latitude, longitude, restaurant.latitude, restaurant.longitude
        )

    stats = review_stats(db, [restaurant.id]).get(restaurant.id)
    menus = menu_items_by_restaurant(db, [restaurant.id]).get(restaurant.id, [])

    payload = restaurant_card(
        restaurant, distance_km=distance, stats=stats, menu_items=menus
    )

    evidence = dietary.evaluate_all(
        name=restaurant.name,
        cuisine=restaurant.cuisine,
        diet_tags=dietary.parse_diet_tags(restaurant.diet_tags),
        menu_items=menus,
    )
    payload["diet_evidence"] = [
        {"name": e.preference, "level": e.level, "note": e.note}
        for e in evidence.values()
    ]
    payload["menu_items"] = [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "price": m.price,
            "is_vegetarian": bool(m.is_vegetarian),
            "is_vegan": bool(m.is_vegan),
            "is_jain": bool(m.is_jain),
            "is_gluten_free": bool(m.is_gluten_free),
        }
        for m in menus
    ]

    # ---- personalised block (only for logged-in users) ---------------
    if user is not None:
        profile = profile_for_user(db, user)
        favorite_ids = {
            rid
            for (rid,) in db.query(Favorite.restaurant_id).filter(
                Favorite.user_id == user.id
            )
        }
        ranked = rank_restaurants(db, [(restaurant, distance)], profile, favorite_ids)[0]
        payload.update(
            {
                "ai_match": ranked["ai_match"],
                "match_reasons": ranked["match_reasons"],
                "confidence": ranked["confidence"],
                "note": ranked["note"],
                "recommended_dish": ranked["recommended_dish"],
                "is_favorite": ranked["is_favorite"],
            }
        )

    return payload


# =========================================================
# CREATE RESTAURANT MANUALLY (login required)
# =========================================================

@router.post("/", status_code=201)
def create_restaurant(
    name: str = Query(..., min_length=1, max_length=150),
    cuisine: str = Query("", max_length=100),
    location: str = Query("", max_length=150),
    rating: float = Query(0.0, ge=0, le=5),
    image_url: str = Query("", max_length=1000),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = Restaurant(
        name=name.strip(),
        cuisine=cuisine.strip(),
        location=location.strip(),
        rating=rating,
        image_url=image_url,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant_card(restaurant)
