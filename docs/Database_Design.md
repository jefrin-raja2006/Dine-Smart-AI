# Database Design

## Project
**DineSmart AI – Restaurant Discovery & Review Platform**

---

# Database Overview

The application uses MySQL as the relational database management system. The database stores user information, restaurant details, menus, reviews, categories, favorites, and AI recommendation data.

---

# Tables

## 1. Users

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(100) | UNIQUE |
| password | VARCHAR(255) | NOT NULL |
| role | ENUM('Admin','Owner','Customer') | NOT NULL |
| created_at | DATETIME | Default Current Timestamp |

---

## 2. Restaurants

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| owner_id | INT | Foreign Key |
| name | VARCHAR(150) | NOT NULL |
| description | TEXT | |
| location | VARCHAR(200) | |
| city | VARCHAR(100) | |
| average_rating | DECIMAL(2,1) | |

---

## 3. Categories

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| name | VARCHAR(100) | UNIQUE |

---

## 4. RestaurantCategories

| Column | Type | Constraint |
|---------|------|------------|
| restaurant_id | INT | Foreign Key |
| category_id | INT | Foreign Key |

---

## 5. MenuItems

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| restaurant_id | INT | Foreign Key |
| name | VARCHAR(150) | |
| price | DECIMAL(10,2) | |
| description | TEXT | |
| availability | BOOLEAN | |

---

## 6. Reviews

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| restaurant_id | INT | Foreign Key |
| user_id | INT | Foreign Key |
| rating | INT | |
| review | TEXT | |
| sentiment | VARCHAR(20) | |
| created_at | DATETIME | |

---

## 7. Favorites

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| user_id | INT | Foreign Key |
| restaurant_id | INT | Foreign Key |

---

## 8. Recommendations

| Column | Type | Constraint |
|---------|------|------------|
| id | INT | Primary Key |
| user_id | INT | Foreign Key |
| restaurant_id | INT | Foreign Key |
| score | DECIMAL(5,2) | |

---

# Relationships

- One User can own many Restaurants.
- One Restaurant can have many Menu Items.
- One Restaurant can have many Reviews.
- One User can write many Reviews.
- One User can save many Favorite Restaurants.
- One Restaurant can belong to multiple Categories.
- Categories and Restaurants have a many-to-many relationship.
- AI Recommendations are generated for each User based on restaurant preferences.

---

# Future AI Features

- Restaurant Recommendation System
- Review Sentiment Analysis
- Personalized Restaurant Suggestions
---

# Implemented schema (v2)

The tables above describe the original design. The running system uses PostgreSQL tables
`users`, `restaurants`, `menu_items`, `reviews`, `favorites`, `dietary_preferences`, `user_dietary_preferences`
(created from `backend/app/models/models.py`). Changes made in v2 (all additive, applied automatically by `app/migrations.py`):

| Table | Added |
|---|---|
| `users` | `created_at` |
| `restaurants` | `latitude`, `longitude` (indexed), `amenity`, `phone`, `website`, `opening_hours`, `diet_tags` (JSON of OSM `diet:*` tags) |
| `reviews` | `analysis_json` (dish/aspect mentions + trust reasons); `sentiment`, `sentiment_score`, `trust_score` are now populated by the NLP pipeline; **unique** (`user_id`, `restaurant_id`) |
| `favorites` | **unique** (`user_id`, `restaurant_id`); indexes on both FKs |

Conventions: `restaurants.rating` = average of review ratings (0.0 if none; the API returns `null` until reviewed) ·
`sentiment_score` −1…+1 · `trust_score` 0…1 · `osm_id` = `node_<id>` / `way_<id>`.
The original `Categories`, `RestaurantCategories` and `Recommendations` tables were not needed: cuisine is a text column and recommendations are computed on demand.
