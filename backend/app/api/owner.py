from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import MenuItem, Restaurant, Review, User
from app.security import require_owner_or_admin
from app.services.serializers import restaurant_card


router = APIRouter(prefix="/owner", tags=["Restaurant Owner"])


# =========================================================
# SCHEMAS
# =========================================================

class RestaurantUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    cuisine: str = Field(default="", max_length=100)
    location: str = Field(default="", max_length=150)
    phone: str = Field(default="", max_length=100)
    website: str = Field(default="", max_length=1000)
    opening_hours: str = Field(default="", max_length=1000)
    image_url: str = Field(default="", max_length=1000)


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=2000)
    price: float | None = Field(default=None, ge=0)
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_jain: bool = False
    is_gluten_free: bool = False


class MenuItemUpdate(MenuItemCreate):
    pass


# =========================================================
# OWNERSHIP HELPER
# =========================================================

def get_owned_restaurant(
    restaurant_id: int,
    user: User,
    db: Session,
) -> Restaurant:
    restaurant = db.get(Restaurant, restaurant_id)

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found",
        )

    # Admin can manage any restaurant.
    if (user.role or "customer").lower() == "admin":
        return restaurant

    # Owner can manage only their own restaurant.
    if restaurant.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage this restaurant",
        )

    return restaurant


# =========================================================
# OWNER RESTAURANTS
# =========================================================

@router.get("/restaurants")
def get_my_restaurants(
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)

    if (user.role or "customer").lower() != "admin":
        query = query.filter(Restaurant.owner_id == user.id)

    restaurants = query.order_by(Restaurant.id).all()

    return {
        "count": len(restaurants),
        "restaurants": [
            restaurant_card(restaurant)
            for restaurant in restaurants
        ],
    }


@router.get("/restaurants/{restaurant_id}")
def get_my_restaurant(
    restaurant_id: int,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    restaurant = get_owned_restaurant(
        restaurant_id,
        user,
        db,
    )

    return restaurant_card(restaurant)


@router.put("/restaurants/{restaurant_id}")
def update_my_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    restaurant = get_owned_restaurant(
        restaurant_id,
        user,
        db,
    )

    restaurant.name = data.name.strip()
    restaurant.cuisine = data.cuisine.strip()
    restaurant.location = data.location.strip()
    restaurant.phone = data.phone.strip()
    restaurant.website = data.website.strip()
    restaurant.opening_hours = data.opening_hours.strip()
    restaurant.image_url = data.image_url.strip()

    db.commit()
    db.refresh(restaurant)

    return {
        "message": "Restaurant updated successfully",
        "restaurant": restaurant_card(restaurant),
    }


# =========================================================
# MENU
# =========================================================

@router.get("/restaurants/{restaurant_id}/menu")
def get_my_menu(
    restaurant_id: int,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    restaurant = get_owned_restaurant(
        restaurant_id,
        user,
        db,
    )

    return {
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "count": len(restaurant.menu_items),
        "menu_items": [
            {
                "id": item.id,
                "restaurant_id": item.restaurant_id,
                "name": item.name,
                "description": item.description,
                "price": item.price,
                "is_vegetarian": bool(item.is_vegetarian),
                "is_vegan": bool(item.is_vegan),
                "is_jain": bool(item.is_jain),
                "is_gluten_free": bool(item.is_gluten_free),
            }
            for item in restaurant.menu_items
        ],
    }


@router.post(
    "/restaurants/{restaurant_id}/menu",
    status_code=201,
)
def add_menu_item(
    restaurant_id: int,
    data: MenuItemCreate,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    restaurant = get_owned_restaurant(
        restaurant_id,
        user,
        db,
    )

    item = MenuItem(
        restaurant_id=restaurant.id,
        name=data.name.strip(),
        description=data.description.strip(),
        price=data.price,
        is_vegetarian=data.is_vegetarian,
        is_vegan=data.is_vegan,
        is_jain=data.is_jain,
        is_gluten_free=data.is_gluten_free,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "message": "Menu item added successfully",
        "menu_item": {
            "id": item.id,
            "restaurant_id": item.restaurant_id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "is_vegetarian": bool(item.is_vegetarian),
            "is_vegan": bool(item.is_vegan),
            "is_jain": bool(item.is_jain),
            "is_gluten_free": bool(item.is_gluten_free),
        },
    }


@router.put("/menu/{menu_id}")
def update_menu_item(
    menu_id: int,
    data: MenuItemUpdate,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, menu_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Menu item not found",
        )

    get_owned_restaurant(
        item.restaurant_id,
        user,
        db,
    )

    item.name = data.name.strip()
    item.description = data.description.strip()
    item.price = data.price
    item.is_vegetarian = data.is_vegetarian
    item.is_vegan = data.is_vegan
    item.is_jain = data.is_jain
    item.is_gluten_free = data.is_gluten_free

    db.commit()
    db.refresh(item)

    return {
        "message": "Menu item updated successfully",
        "menu_item": {
            "id": item.id,
            "restaurant_id": item.restaurant_id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "is_vegetarian": bool(item.is_vegetarian),
            "is_vegan": bool(item.is_vegan),
            "is_jain": bool(item.is_jain),
            "is_gluten_free": bool(item.is_gluten_free),
        },
    }


@router.delete("/menu/{menu_id}")
def delete_menu_item(
    menu_id: int,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    item = db.get(MenuItem, menu_id)

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Menu item not found",
        )

    get_owned_restaurant(
        item.restaurant_id,
        user,
        db,
    )

    db.delete(item)
    db.commit()

    return {
        "message": "Menu item deleted successfully",
    }


# =========================================================
# REVIEWS
# =========================================================

@router.get("/restaurants/{restaurant_id}/reviews")
def get_my_reviews(
    restaurant_id: int,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    restaurant = get_owned_restaurant(
        restaurant_id,
        user,
        db,
    )

    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    return {
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "count": len(reviews),
        "reviews": [
            {
                "id": review.id,
                "user_id": review.user_id,
                "user_name": (
                    review.user.name
                    if review.user
                    else "Anonymous"
                ),
                "rating": review.rating,
                "text": review.text,
                "created_at": (
                    review.created_at.isoformat()
                    if review.created_at
                    else None
                ),
                "sentiment": review.sentiment,
                "sentiment_score": review.sentiment_score,
                "trust_score": review.trust_score,
            }
            for review in reviews
        ],
    }


# =========================================================
# RESTAURANT STATISTICS
# =========================================================

@router.get("/restaurants/{restaurant_id}/stats")
def get_my_stats(
    restaurant_id: int,
    user: User = Depends(require_owner_or_admin),
    db: Session = Depends(get_db),
):
    restaurant = get_owned_restaurant(
        restaurant_id,
        user,
        db,
    )

    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant.id)
        .all()
    )

    review_count = len(reviews)

    average_rating = None
    if reviews:
        average_rating = round(
            sum(review.rating for review in reviews) / review_count,
            1,
        )

    sentiment_counts = {
        "positive": 0,
        "negative": 0,
        "mixed": 0,
        "neutral": 0,
    }

    for review in reviews:
        sentiment = (review.sentiment or "neutral").lower()

        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
        else:
            sentiment_counts["neutral"] += 1

    return {
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.name,
        "menu_items": len(restaurant.menu_items),
        "review_count": review_count,
        "average_rating": average_rating,
        "sentiment": sentiment_counts,
    }