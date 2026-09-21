from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    ForeignKey,
    Boolean,
    DateTime,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base
from app.utils import utcnow


# =========================================================
# USER ↔ DIETARY PREFERENCE
# Many-to-Many relationship
# =========================================================

user_dietary_preferences = Table(
    "user_dietary_preferences",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "preference_id",
        Integer,
        ForeignKey("dietary_preferences.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# =========================================================
# USER
# =========================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    password = Column(
        String(255),
        nullable=False,
    )

    # ---------------------------------------------------------
    # USER ROLE
    # customer = normal application user
    # owner    = restaurant owner
    # admin    = system administrator
    #
    # Normal registration will use "customer".
    # ---------------------------------------------------------

    role = Column(
        String(30),
        nullable=False,
        default="customer",
        server_default="customer",
        index=True,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    favorites = relationship(
        "Favorite",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    dietary_preferences = relationship(
        "DietaryPreference",
        secondary=user_dietary_preferences,
        back_populates="users",
    )

    # Restaurants owned/managed by this user
    owned_restaurants = relationship(
        "Restaurant",
        back_populates="owner",
        foreign_keys="Restaurant.owner_id",
    )


# =========================================================
# RESTAURANT
# =========================================================

class Restaurant(Base):
    __tablename__ = "restaurants"

    # PostgreSQL database ID
    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ---------------------------------------------------------
    # OpenStreetMap ID
    # Example:
    # node_123456
    # way_987654
    # ---------------------------------------------------------

    osm_id = Column(
        String(100),
        unique=True,
        index=True,
        nullable=True,
    )

    # ---------------------------------------------------------
    # Restaurant owner
    #
    # NULL is allowed because restaurants discovered from
    # OpenStreetMap may not have a DineSmart owner yet.
    # ---------------------------------------------------------

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    name = Column(
        String(150),
        nullable=False,
    )

    cuisine = Column(
        String(100),
    )

    location = Column(
        String(150),
    )

    # Average of review ratings
    rating = Column(
        Float,
        default=0.0,
    )

    image_url = Column(
        Text,
    )

    # ---------------------------------------------------------
    # OpenStreetMap data
    # ---------------------------------------------------------

    latitude = Column(
        Float,
        index=True,
    )

    longitude = Column(
        Float,
        index=True,
    )

    # restaurant / cafe / fast_food / food_court
    amenity = Column(
        String(50),
    )

    phone = Column(
        String(100),
    )

    website = Column(
        Text,
    )

    opening_hours = Column(
        Text,
    )

    # JSON object of OSM diet:* tags
    # Example:
    # {"vegetarian": "yes"}
    diet_tags = Column(
        Text,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    owner = relationship(
        "User",
        back_populates="owned_restaurants",
        foreign_keys=[owner_id],
    )

    menu_items = relationship(
        "MenuItem",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    reviews = relationship(
        "Review",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    favorites = relationship(
        "Favorite",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )


# =========================================================
# MENU ITEM
# =========================================================

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
    )

    name = Column(
        String(150),
        nullable=False,
    )

    description = Column(
        Text,
    )

    price = Column(
        Float,
    )

    is_vegetarian = Column(
        Boolean,
        default=False,
    )

    is_vegan = Column(
        Boolean,
        default=False,
    )

    is_jain = Column(
        Boolean,
        default=False,
    )

    is_gluten_free = Column(
        Boolean,
        default=False,
    )

    restaurant = relationship(
        "Restaurant",
        back_populates="menu_items",
    )


# =========================================================
# REVIEW
# =========================================================

class Review(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        # One review per user per restaurant
        UniqueConstraint(
            "user_id",
            "restaurant_id",
            name="uq_reviews_user_restaurant",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True,
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        index=True,
    )

    rating = Column(
        Integer,
    )

    text = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=utcnow,
    )

    # ---------------------------------------------------------
    # AI / NLP fields
    # ---------------------------------------------------------

    # positive | negative | mixed | neutral
    sentiment = Column(
        String(30),
    )

    # -1.0 very negative → +1.0 very positive
    sentiment_score = Column(
        Float,
    )

    # 0.0 low trust → 1.0 high trust
    trust_score = Column(
        Float,
    )

    # JSON:
    # dish/aspect sentiments + trust reasons
    analysis_json = Column(
        Text,
    )

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    user = relationship(
        "User",
        back_populates="reviews",
    )

    restaurant = relationship(
        "Restaurant",
        back_populates="reviews",
    )


# =========================================================
# FAVORITE
# =========================================================

class Favorite(Base):
    __tablename__ = "favorites"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "restaurant_id",
            name="uq_favorites_user_restaurant",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        index=True,
    )

    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        index=True,
    )

    user = relationship(
        "User",
        back_populates="favorites",
    )

    restaurant = relationship(
        "Restaurant",
        back_populates="favorites",
    )


# =========================================================
# DIETARY PREFERENCE
# =========================================================

class DietaryPreference(Base):
    __tablename__ = "dietary_preferences"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    users = relationship(
        "User",
        secondary=user_dietary_preferences,
        back_populates="dietary_preferences",
    )