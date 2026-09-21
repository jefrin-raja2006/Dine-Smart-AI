from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.constants import normalize_preferences
from app.database.connection import get_db
from app.models.models import Favorite, Restaurant, User
from app.security import get_current_user
from app.services.discovery import (
    OverpassUnavailable,
    discover,
    saved_restaurants_near,
)
from app.services.recommendation_service import profile_for_user, rank_restaurants

router = APIRouter(prefix="/recommendations", tags=["AI Recommendations"])

ALLERGY_DISCLAIMER = (
    "Dietary information comes from OpenStreetMap, menus and reviews and may be "
    "incomplete. It is not medical advice and never a guarantee that food is "
    "allergen-free - always confirm with the restaurant."
)


@router.get("/me")
async def my_recommendations(
    latitude: float | None = Query(None, ge=-90, le=90),
    longitude: float | None = Query(None, ge=-180, le=180),
    radius: int = Query(10000, ge=1000, le=15000),
    limit: int = Query(20, ge=1, le=100),
    preferences: str | None = Query(
        None,
        max_length=200,
        description="Optional comma-separated override of saved dietary preferences",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Personalised, explainable restaurant ranking for the logged-in user."""
    override = None
    if preferences is not None:
        override, invalid = normalize_preferences(preferences.split(","))
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown dietary preference: {', '.join(invalid)}",
            )

    if (latitude is None) != (longitude is None):
        raise HTTPException(
            status_code=400, detail="Provide both latitude and longitude"
        )

    message = None

    # ---- candidate restaurants --------------------------------------
    if latitude is not None:
        try:
            result = await discover(db, latitude, longitude, radius)
            pairs = result.restaurants
            message = result.message
        except OverpassUnavailable:
            pairs = saved_restaurants_near(db, latitude, longitude, radius / 1000)
            message = (
                "Live restaurant data is unavailable; ranking saved restaurants."
                if pairs
                else "Restaurant data is temporarily unavailable."
            )
    else:
        rows = db.query(Restaurant).order_by(Restaurant.id.desc()).limit(300).all()
        pairs = [(r, None) for r in rows]

    profile = profile_for_user(db, user, override)
    favorite_ids = {
        rid
        for (rid,) in db.query(Favorite.restaurant_id).filter(
            Favorite.user_id == user.id
        )
    }

    ranked = rank_restaurants(db, pairs, profile, favorite_ids)[:limit]

    return {
        "count": len(ranked),
        "preferences": profile.preferences,
        "personalised": bool(profile.preferences or profile.has_history),
        "message": message,
        "disclaimer": ALLERGY_DISCLAIMER,
        "recommendations": ranked,
    }
