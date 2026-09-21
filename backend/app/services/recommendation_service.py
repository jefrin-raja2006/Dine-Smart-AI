"""Glue between the database and the pure recommender functions."""

from sqlalchemy.orm import Session

from app.models.models import Favorite, Restaurant, Review, User
from app.services import dietary
from app.services.insights import build_insights
from app.services.recommender import (
    Candidate,
    UserProfile,
    build_profile,
    score_candidate,
)
from app.services.serializers import (
    menu_items_by_restaurant,
    restaurant_card,
    review_stats,
)


def profile_for_user(
    db: Session, user: User, preferences: list[str] | None = None
) -> UserProfile:
    favorites = [
        cuisine
        for (cuisine,) in db.query(Restaurant.cuisine)
        .join(Favorite, Favorite.restaurant_id == Restaurant.id)
        .filter(Favorite.user_id == user.id)
    ]
    rated = (
        db.query(Restaurant.cuisine, Review.rating)
        .join(Review, Review.restaurant_id == Restaurant.id)
        .filter(Review.user_id == user.id)
        .all()
    )

    return build_profile(
        preferences=(
            preferences
            if preferences is not None
            else [p.name for p in user.dietary_preferences]
        ),
        favorite_cuisines=favorites,
        liked_cuisines=[c for c, r in rated if r >= 4],
        disliked_cuisines=[c for c, r in rated if r <= 2],
    )


def rank_restaurants(
    db: Session,
    pairs: list[tuple[Restaurant, float | None]],
    profile: UserProfile,
    favorite_ids: set[int],
) -> list[dict]:
    """Score restaurants and return cards enriched with AI fields, best first."""
    ids = [r.id for r, _ in pairs]
    stats = review_stats(db, ids)
    menus = menu_items_by_restaurant(db, ids)

    # dish insights only for the (few) restaurants that have reviews
    reviewed_ids = [i for i in ids if stats.get(i, {}).get("count")]
    reviews_by_restaurant: dict[int, list[Review]] = {}
    if reviewed_ids:
        for review in db.query(Review).filter(Review.restaurant_id.in_(reviewed_ids)):
            reviews_by_restaurant.setdefault(review.restaurant_id, []).append(review)

    results = []

    for restaurant, distance in pairs:
        rstats = stats.get(restaurant.id) or {}
        items = menus.get(restaurant.id, [])

        evidence = dietary.evaluate_all(
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            diet_tags=dietary.parse_diet_tags(restaurant.diet_tags),
            menu_items=items,
        )

        best_dish = None
        insight = build_insights(reviews_by_restaurant.get(restaurant.id, []))
        if insight["best_dish"]:
            best_dish = insight["best_dish"]["name"]
        else:
            for preference in profile.preferences:
                flag = {
                    "Vegetarian": "is_vegetarian", "Vegan": "is_vegan",
                    "Jain": "is_jain", "Gluten-Free": "is_gluten_free",
                }.get(preference)
                match = next((i for i in items if flag and getattr(i, flag, False)), None)
                if match:
                    best_dish = match.name
                    break

        candidate = Candidate(
            id=restaurant.id,
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            distance_km=distance,
            rating=rstats.get("rating"),
            review_count=rstats.get("count", 0),
            avg_trust=rstats.get("trust"),
            has_address=bool(restaurant.location),
            has_contact=bool(restaurant.phone or restaurant.website),
            has_hours=bool(restaurant.opening_hours),
            evidence=evidence,
            best_dish=best_dish,
        )
        rec = score_candidate(candidate, profile)

        card = restaurant_card(
            restaurant, distance_km=distance, stats=rstats, menu_items=items
        )
        card.update(
            {
                "ai_match": rec.match,
                "match_reasons": rec.reasons,
                "confidence": rec.confidence,
                "note": rec.note,
                "recommended_dish": best_dish,
                "is_favorite": restaurant.id in favorite_ids,
            }
        )
        results.append(card)

    results.sort(
        key=lambda c: (-c["ai_match"], c["distance_km"] if c["distance_km"] is not None else 1e9)
    )
    return results
