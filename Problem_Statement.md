# Problem Statement

## 1. Title

**DineSmart AI – Restaurant Discovery & Review Platform**

---

## 2. Domain

Food Technology (FoodTech)

---

## 3. Who is the User?

### Customer
- Register and log in to the platform.
- Search restaurants based on cuisine, location, and ratings.
- View restaurant details and menus.
- Add ratings and reviews.
- Save favorite restaurants.
- Receive AI-powered restaurant recommendations.

### Restaurant Owner
- Register and manage restaurants.
- Add, edit, and delete menu items.
- View customer reviews and ratings.

### Admin
- Manage users.
- Verify and manage restaurants.
- Moderate reviews.
- Monitor overall platform activities.

---

## 4. What Problem Are We Solving?

Finding the right restaurant can be time-consuming because users often browse multiple websites and applications to compare ratings, cuisines, prices, and customer reviews. Many platforms also contain fake or misleading reviews, making it difficult for users to make informed decisions.

DineSmart AI provides a centralized platform where customers can discover restaurants, browse menus, read authentic reviews, submit ratings, and receive personalized AI-powered recommendations based on their preferences.

---

## 5. Proposed Solution

The application will provide the following features:

- User Registration & Login
- Restaurant Management
- Restaurant Search & Filtering
- Restaurant Categories
- Menu Management
- Ratings & Reviews
- Favorite Restaurants
- AI-Based Restaurant Recommendation System
- Review Sentiment Analysis
- Admin Dashboard

---

## 6. Core Entities / Database Tables

1. Users
2. Restaurants
3. Categories
4. RestaurantCategories
5. MenuItems
6. Reviews
7. Favorites
8. Recommendations

---

## 7. User Roles & Permissions

### Admin
- Manage users
- Manage restaurants
- Verify restaurant registrations
- Remove inappropriate reviews

### Restaurant Owner
- Register restaurants
- Manage restaurant details
- Manage menus
- View customer reviews

### Customer
- Register/Login
- Search restaurants
- View restaurant information
- Submit reviews and ratings
- Save favorite restaurants
- Receive personalized recommendations

---

## 8. Success Criteria

- Users can successfully register and log in.
- Restaurants can be searched using multiple filters.
- Restaurant owners can manage restaurant information and menus.
- Customers can post ratings and reviews.
- The system provides AI-based restaurant recommendations.
- Reviews can be analyzed using sentiment analysis in the enhancement phase.

---

## 9. Out of Scope

The following features are intentionally excluded from the current project scope:

- Online food ordering
- Payment gateway integration
- Live delivery tracking
- Restaurant table reservation
- Live chat between users and restaurant owners
- Video reviews

---

## 10. Chosen Track

**Python (FastAPI)**