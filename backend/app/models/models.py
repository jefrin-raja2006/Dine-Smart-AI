from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)

    reviews = relationship("Review", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    cuisine = Column(String(100))
    location = Column(String(150))
    rating = Column(Float, default=0.0)
    image_url = Column(Text)

    menu_items = relationship("MenuItem", back_populates="restaurant")
    reviews = relationship("Review", back_populates="restaurant")
    favorites = relationship("Favorite", back_populates="restaurant")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    name = Column(String(150), nullable=False)
    description = Column(Text)
    price = Column(Float)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    is_jain = Column(Boolean, default=False)
    is_gluten_free = Column(Boolean, default=False)

    restaurant = relationship("Restaurant", back_populates="menu_items")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    rating = Column(Integer)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sentiment = Column(String(30))
    sentiment_score = Column(Float)
    trust_score = Column(Float)

    user = relationship("User", back_populates="reviews")
    restaurant = relationship("Restaurant", back_populates="reviews")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))

    user = relationship("User", back_populates="favorites")
    restaurant = relationship("Restaurant", back_populates="favorites")


class DietaryPreference(Base):
    __tablename__ = "dietary_preferences"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
