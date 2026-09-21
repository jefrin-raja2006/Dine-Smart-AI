"""Create/update a review, run the AI analysis and refresh restaurant rating."""

import json
from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import MenuItem, Restaurant, Review, User
from app.services import sentiment as nlp
from app.services.trust import TrustContext, score_review
from app.utils import utcnow


def _normalise(text: str) -> str:
    return " ".join(text.lower().split())


def refresh_restaurant_rating(db: Session, restaurant: Restaurant) -> None:
    average = (
        db.query(func.avg(Review.rating))
        .filter(Review.restaurant_id == restaurant.id)
        .scalar()
    )
    restaurant.rating = round(float(average), 1) if average is not None else 0.0


def save_review(
    db: Session,
    user: User,
    restaurant: Restaurant,
    rating: int,
    text: str,
) -> Review:
    menu_names = [
        name
        for (name,) in db.query(MenuItem.name).filter(
            MenuItem.restaurant_id == restaurant.id
        )
    ]

    result = nlp.analyze_text(text, menu_names)

    blended = nlp.blend_with_rating(result.score, rating)
    label = nlp.label_for_score(blended, result.positive_sum, result.negative_sum)

    existing = (
        db.query(Review)
        .filter(Review.user_id == user.id, Review.restaurant_id == restaurant.id)
        .first()
    )

    # ---- context for the trust scorer -------------------------------
    normalised = _normalise(text)
    duplicate_query = db.query(Review.id).filter(
        func.lower(Review.text) == normalised
    )
    if existing:
        duplicate_query = duplicate_query.filter(Review.id != existing.id)
    duplicate = duplicate_query.first() is not None

    recent_query = db.query(func.count(Review.id)).filter(
        Review.user_id == user.id,
        Review.created_at >= utcnow() - timedelta(hours=1),
    )
    if existing:
        recent_query = recent_query.filter(Review.id != existing.id)

    trust = score_review(
        text,
        rating,
        result,
        TrustContext(
            duplicate_elsewhere=duplicate,
            recent_reviews_by_user=recent_query.scalar() or 0,
        ),
    )

    analysis = json.dumps(
        {
            "mentions": [
                {"name": m.name, "kind": m.kind, "score": m.score, "label": m.label}
                for m in result.mentions
            ],
            "trust_reasons": trust.reasons,
            "trust_strengths": trust.strengths,
        }
    )

    if existing is None:
        review = Review(user_id=user.id, restaurant_id=restaurant.id)
        db.add(review)
    else:
        review = existing
        review.created_at = utcnow()

    review.rating = rating
    review.text = text
    review.sentiment = label
    review.sentiment_score = blended
    review.trust_score = trust.score
    review.analysis_json = analysis

    db.flush()
    refresh_restaurant_rating(db, restaurant)
    db.commit()
    db.refresh(review)

    return review
