"""Turn ORM rows into the JSON the frontend consumes."""

from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import MenuItem, Restaurant, Review, User
from app.services import dietary
from app.utils import iso_utc


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role or "customer",
        "dietary_preferences": [p.name for p in user.dietary_preferences],
    }


def review_stats(db: Session, restaurant_ids: list[int]) -> dict[int, dict]:
    """{restaurant_id: {"count": n, "rating": avg, "trust": avg_trust}}"""
    if not restaurant_ids:
        return {}

    rows = (
        db.query(
            Review.restaurant_id,
            func.count(Review.id),
            func.avg(Review.rating),
            func.avg(Review.trust_score),
        )
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .group_by(Review.restaurant_id)
        .all()
    )

    return {
        rid: {
            "count": count,
            "rating": round(float(avg_rating), 1) if avg_rating is not None else None,
            "trust": float(avg_trust) if avg_trust is not None else None,
        }
        for rid, count, avg_rating, avg_trust in rows
    }


def menu_items_by_restaurant(
    db: Session, restaurant_ids: list[int]
) -> dict[int, list[MenuItem]]:
    if not restaurant_ids:
        return {}

    grouped: dict[int, list[MenuItem]] = defaultdict(list)
    for item in db.query(MenuItem).filter(MenuItem.restaurant_id.in_(restaurant_ids)):
        grouped[item.restaurant_id].append(item)

    return grouped


def restaurant_card(
    restaurant: Restaurant,
    *,
    distance_km: float | None = None,
    stats: dict | None = None,
    menu_items: list[MenuItem] | None = None,
) -> dict:
    """The compact shape used by every restaurant list/card in the UI."""
    stats = stats or {}
    count = stats.get("count", 0)

    evidence = dietary.evaluate_all(
        name=restaurant.name,
        cuisine=restaurant.cuisine,
        diet_tags=dietary.parse_diet_tags(restaurant.diet_tags),
        menu_items=menu_items,
    )

    return {
        "id": restaurant.id,
        "osm_id": restaurant.osm_id,
        "name": restaurant.name,
        "cuisine": restaurant.cuisine or "Restaurant",
        "amenity": restaurant.amenity or "restaurant",
        "latitude": restaurant.latitude,
        "longitude": restaurant.longitude,
        "address": restaurant.location,
        "phone": restaurant.phone,
        "website": restaurant.website,
        "opening_hours": restaurant.opening_hours,
        # null until at least one review exists
        "rating": stats.get("rating") if count else None,
        "review_count": count,
        "image_url": restaurant.image_url or "",
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
        "diet_tags": dietary.diet_labels(evidence),
    }


def restaurant_cards(
    db: Session,
    pairs: list[tuple[Restaurant, float | None]],
) -> list[dict]:
    """Serialize many restaurants with just two extra queries."""
    ids = [r.id for r, _ in pairs]
    stats = review_stats(db, ids)
    menus = menu_items_by_restaurant(db, ids)

    return [
        restaurant_card(
            r,
            distance_km=d,
            stats=stats.get(r.id),
            menu_items=menus.get(r.id),
        )
        for r, d in pairs
    ]


def review_payload(review: Review, *, current_user_id: int | None = None) -> dict:
    import json

    analysis = {}
    if review.analysis_json:
        try:
            analysis = json.loads(review.analysis_json)
        except ValueError:
            analysis = {}

    trust = review.trust_score if review.trust_score is not None else 0.0
    from app.services.trust import label_for_trust

    return {
        "id": review.id,
        "restaurant_id": review.restaurant_id,
        "user_name": review.user.name if review.user else "Anonymous",
        "rating": review.rating,
        "text": review.text,
        "created_at": iso_utc(review.created_at),
        "sentiment": review.sentiment,
        "sentiment_score": review.sentiment_score,
        "trust_score": review.trust_score,
        "trust_label": label_for_trust(trust),
        "trust_reasons": analysis.get("trust_reasons", []),
        "trust_strengths": analysis.get("trust_strengths", []),
        "mentions": analysis.get("mentions", []),
        "is_mine": current_user_id is not None and review.user_id == current_user_id,
    }
