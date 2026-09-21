# Changelog

All notable changes to this project will be documented in this file.

---

## Phase 1 – Design & Planning

### Day 1
- Finalized project title
- Completed Problem Statement
- Created repository structure

### Day 2
- Designed System Architecture Diagram
- Designed ER Diagram
- Designed Module Diagram
- Completed Database Schema
- Configured VS Code environment

### Current Status
- Phase 1 completed successfully
---

## v2.0 – Full-stack completion

### Backend
- JWT authentication; user identity now comes from the token (removed `user_id` from URLs)
- Login/register rate limiting; bcrypt 72-byte guard; case-insensitive emails; `/db-test` no longer leaks errors
- Startup migrations that upgrade existing databases in place; unique constraints on favourites/reviews
- Reviews API with sentiment analysis, dish/aspect extraction and explainable trust scoring
- Restaurant insights endpoint (trust-weighted, confidence-aware)
- Recommender rewritten: works for OpenStreetMap restaurants (previously required menu items), explainable scores
- Discovery: batched sync, caching, saved-data fallback, all values clipped to column sizes (long OSM `cuisine` values used to fail the insert)
- User profile, preferences and password endpoints
- Config from environment (`SECRET_KEY`, `CORS_ORIGINS`, …); production mode refuses to start with a weak key
- `requirements.txt`; 107 automated tests (SQLite + PostgreSQL)

### Frontend
- Restaurant Details, Profile and Home now use real data (were hard-coded)
- Cards link to details; working dietary filter, AI-picks mode, favourites, distance
- Review form with live AI analysis; trust explanations; dish sentiment; dietary evidence
- Session handling with automatic logout on expired tokens; shared Navbar/Footer/RestaurantCard
- Fixed two files saved in a non-UTF-8 encoding that broke `npm run build`; lockfile now points at the official npm registry
- 34 automated tests (Vitest)

### DevOps
- Dockerfiles, docker-compose, nginx config, `.env.example` files
- GitHub Actions CI (backend on PostgreSQL, frontend lint/test/build, Docker build)
- README, API, AI methodology and deployment documentation
