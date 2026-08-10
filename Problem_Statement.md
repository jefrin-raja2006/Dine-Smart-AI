# Problem Statement

## 1. Title

**DineSmart AI – AI-Powered Dietary-Aware Restaurant & Dish Discovery Platform**

---

## 2. Domain

Food Technology (FoodTech) / Artificial Intelligence

---

## 3. Who is the User?

### Customer

- Register and log in.
- Search restaurants and dishes.
- Select dietary preferences.
- Filter restaurants based on cuisine, location, rating, and budget.
- View menus and restaurant details.
- Read customer reviews.
- View AI-generated dish-level sentiment insights.
- View suspicious-review indicators.
- Save favorite restaurants.
- Receive personalized recommendations.

### Restaurant Owner

- Register and manage restaurants.
- Manage restaurant information.
- Add, update, and remove menu items.
- View customer ratings and reviews.

### Admin

- Manage users.
- Manage restaurants.
- Moderate reviews.
- Monitor suspicious-review indicators.
- Manage platform activities.

---

## 4. What Problem Are We Solving?

Users with specific dietary preferences often struggle to identify suitable
restaurants and individual dishes because dietary information can be
incomplete or difficult to compare. Customer reviews are also unstructured,
making it difficult to determine which individual dishes are well received.

In addition, potentially suspicious or manipulated reviews can reduce trust
in restaurant information.

Users therefore need a platform that can combine restaurant discovery,
dietary preferences, menu information, and intelligent analysis of customer
reviews.

---

## 5. Proposed Solution

DineSmart AI is an AI-powered restaurant and dish discovery platform that
helps users discover restaurants and dishes according to their preferences.

The platform analyzes restaurant information and customer reviews using
AI/NLP techniques to provide:

- Dietary-aware restaurant and dish recommendations.
- Personalized restaurant recommendations.
- Dish-level sentiment analysis.
- Suspicious-review indicators.
- Explainable recommendation reasons.
- Confidence-aware fallback messages when sufficient evidence is unavailable.

The system also provides normal restaurant discovery, ratings, reviews,
favorites, menu browsing, and role-based management.

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
9. DietaryPreferences
10. RestaurantDietaryTags
11. ReviewAnalysis
12. DishSentiments

---

## 7. User Roles & Permissions

### Admin

- Manage users.
- Manage restaurants.
- Moderate reviews.
- Monitor suspicious-review indicators.
- Manage platform activities.

### Restaurant Owner

- Register restaurants.
- Manage restaurant details.
- Manage menu items.
- View customer reviews and ratings.

### Customer

- Register/Login.
- Manage dietary preferences.
- Search restaurants and dishes.
- View menus.
- Submit ratings and reviews.
- Save favorite restaurants.
- View AI insights.
- Receive personalized recommendations.

---

## 8. Success Criteria

- Users can register and log in successfully.
- Users can define dietary preferences.
- Users can search and filter restaurants and dishes.
- Users can view restaurant menus and reviews.
- The system provides personalized recommendations.
- The system provides dish-level sentiment insights.
- The system identifies potentially suspicious reviews.
- Recommendations provide understandable reasons.
- The system provides a fallback when AI confidence is low.

---

## 9. Out of Scope

- Online food ordering.
- Payment gateway.
- Live delivery tracking.
- Restaurant table reservation.
- Medical diagnosis.
- Medical or nutritional treatment recommendations.
- Guaranteeing that a dish is completely allergen-free.

Users with serious allergies or medical dietary restrictions should verify
ingredients directly with the restaurant before consuming food.

---

## 10. Chosen Track

**Python (FastAPI)**