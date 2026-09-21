# API Reference

Base URL (local): `http://127.0.0.1:8000` · Interactive docs: `/docs` (disabled when `ENVIRONMENT=production`).

Protected endpoints need `Authorization: Bearer <access_token>` (returned by register/login).
Errors are `{"detail": "message"}`; validation errors return HTTP 422.

## Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | – | `{first_name, last_name, email, password (8–72 bytes), dietary_preferences[]}` → `201 {access_token, token_type, user}` |
| POST | `/auth/login` | – | `{email, password}` → `{access_token, token_type, user}`. 5 failed attempts per IP+email / 15 min → `429` |

## Users

| Method | Path | Description |
|---|---|---|
| GET | `/users/me` | Profile + stats (`favorites`, `reviews`, `average_rating_given`), `member_since` |
| PUT | `/users/me` | `{name}` |
| PUT | `/users/me/preferences` | `{dietary_preferences: ["Vegetarian", …]}` — allowed: Vegetarian, Vegan, Jain, Gluten-Free, Dairy-Free |
| POST | `/users/me/password` | `{current_password, new_password}` |

## Restaurants

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/restaurants/nearby?latitude&longitude&radius=5000` | – | Discovers places via OpenStreetMap, syncs to the DB, returns them nearest-first. `radius` 1000–15000 m; widened to 10 km if empty. Falls back to saved restaurants if OSM is down (`503` if nothing saved) |
| GET | `/restaurants/?q&limit&offset` | – | Saved restaurants, optional text search |
| GET | `/restaurants/{id}?latitude&longitude` | optional | Detail: contact, hours, menu, `diet_evidence[]`; when logged in also `ai_match`, `match_reasons`, `confidence`, `note`, `recommended_dish`, `is_favorite` |
| POST | `/restaurants/` | ✔ | Create a restaurant manually (query params) |

**Restaurant card fields:** `id, osm_id, name, cuisine, amenity, latitude, longitude, address, phone, website, opening_hours, rating (null until reviewed), review_count, image_url, distance_km, diet_tags[{name, level: verified|likely, note}]`

## Reviews & insights

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/restaurants/{id}/reviews?limit&offset` | optional | Reviews with `sentiment`, `sentiment_score`, `trust_score`, `trust_label`, `trust_reasons`, `trust_strengths`, `mentions[]`, `is_mine` |
| POST | `/restaurants/{id}/reviews` | ✔ | `{rating 1–5, text 5–2000 chars}`. One review per user per restaurant — posting again **replaces** it. Runs the NLP + trust analysis and updates the restaurant's average rating |
| DELETE | `/restaurants/{id}/reviews/mine` | ✔ | Delete your review |
| GET | `/restaurants/{id}/insights` | – | `review_count, average_rating, confidence (none/low/medium/high), message, sentiment{positive_pct,label,distribution}, trust{score,label,low_trust_reviews}, dishes[], aspects[], best_dish` |

## Favourites

| Method | Path | Description |
|---|---|---|
| GET | `/favorites` | `{favorites: [card…], count}` |
| GET | `/favorites/check/{restaurant_id}` | `{favorite: bool}` |
| POST | `/favorites/{restaurant_id}` | Idempotent add |
| DELETE | `/favorites/{restaurant_id}` | Idempotent remove |

## AI recommendations

`GET /recommendations/me?latitude&longitude&radius=10000&limit=20&preferences=Vegan,Jain` (✔)

Returns `{recommendations[], preferences, personalised, message, disclaimer}`. Each item is a restaurant card plus
`ai_match (0–100), match_reasons[], confidence (high|medium|low), note, recommended_dish, is_favorite`.
`preferences` optionally overrides the saved ones (used for previews). Without coordinates, saved restaurants are ranked.

## System

`GET /` · `GET /health` · `GET /db-test`

### Breaking changes from the first version

Favourites and recommendations no longer take a `user_id` in the URL — the user comes from the token
(`/favorites/{user_id}` → `/favorites`; `/recommendations/{user_id}` → `/recommendations/me`). Login/register additionally return `access_token`.
