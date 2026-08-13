from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Restaurant, MenuItem

router = APIRouter(
    prefix="/recommendations",
    tags=["AI Recommendations"]
)


@router.get("/{user_id}")
def get_recommendations(
    user_id: int,
    preferences: str = "",
    db: Session = Depends(get_db)
):
    restaurant_list = db.query(Restaurant).all()

    if not restaurant_list:
        return []

    selected = {
        item.strip().lower()
        for item in preferences.split(",")
        if item.strip()
    }

    recommendations = []

    for restaurant in restaurant_list:

        menu_items = db.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant.id
        ).all()

        if not menu_items:
            continue

        best_match = 0
        best_dish = None

        for dish in menu_items:

            score = 0
            total_preferences = len(selected)

            if "vegetarian" in selected and dish.is_vegetarian:
                score += 25

            if "vegan" in selected and dish.is_vegan:
                score += 25

            if "jain" in selected and dish.is_jain:
                score += 25

            if "gluten-free" in selected and dish.is_gluten_free:
                score += 25

            if total_preferences == 0:
                score = 70

            if score > best_match:
                best_match = score
                best_dish = dish.name

        rating_score = min((restaurant.rating or 0) / 5 * 10, 10)

        final_score = min(
            round(best_match + rating_score),
            100
        )

        recommendations.append({
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "cuisine": restaurant.cuisine,
            "location": restaurant.location,
            "rating": restaurant.rating,
            "image_url": restaurant.image_url,
            "ai_match": final_score,
            "recommended_dish": best_dish,
        })

    recommendations.sort(
        key=lambda x: x["ai_match"],
        reverse=True
    )

    return recommendations
