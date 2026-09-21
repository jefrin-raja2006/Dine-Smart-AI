from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.models import Restaurant, Review, User
from app.schemas.reviews import ReviewCreate
from app.security import get_current_user, get_optional_user
from app.services.insights import build_insights
from app.services.review_service import refresh_restaurant_rating, save_review
from app.services.serializers import review_payload

router = APIRouter(prefix="/restaurants", tags=["Reviews & AI insights"])


def _restaurant_or_404(db: Session, restaurant_id: int) -> Restaurant:
    restaurant = db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.get("/{restaurant_id}/reviews")
def list_reviews(
    restaurant_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    _restaurant_or_404(db, restaurant_id)

    query = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.restaurant_id == restaurant_id)
    )
    total = query.count()
    rows = query.order_by(Review.created_at.desc(), Review.id.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "reviews": [
            review_payload(r, current_user_id=user.id if user else None) for r in rows
        ],
    }


@router.post("/{restaurant_id}/reviews", status_code=201)
def create_review(
    restaurant_id: int,
    data: ReviewCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create your review (posting again replaces it). Runs the AI analysis."""
    restaurant = _restaurant_or_404(db, restaurant_id)
    review = save_review(db, user, restaurant, data.rating, data.text)
    return review_payload(review, current_user_id=user.id)


@router.delete("/{restaurant_id}/reviews/mine")
def delete_my_review(
    restaurant_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    restaurant = _restaurant_or_404(db, restaurant_id)

    deleted = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id, Review.user_id == user.id)
        .delete()
    )
    db.flush()
    refresh_restaurant_rating(db, restaurant)
    db.commit()

    if not deleted:
        raise HTTPException(status_code=404, detail="You have not reviewed this restaurant")

    return {"message": "Review deleted"}


@router.get("/{restaurant_id}/insights")
def restaurant_insights(restaurant_id: int, db: Session = Depends(get_db)):
    _restaurant_or_404(db, restaurant_id)
    reviews = db.query(Review).filter(Review.restaurant_id == restaurant_id).all()
    return build_insights(reviews)
