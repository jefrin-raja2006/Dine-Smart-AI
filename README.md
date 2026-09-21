# 🍽️ DineSmart AI

> AI-powered restaurant discovery: find food that fits your diet, backed by dish-level review insights and review-trust indicators.

DineSmart AI finds real restaurants around you (OpenStreetMap), ranks them for **your** dietary preferences, and turns customer reviews into **dish-level sentiment** and **trust indicators** — with the reasoning shown, and honest "verified vs. likely" labels instead of false certainty.

## ✨ Features

| Area | What it does |
|---|---|
| **Accounts** | Register / login with JWT tokens, bcrypt passwords, login rate-limiting, profile, change name & password |
| **Nearby discovery** | GPS → OpenStreetMap (Overpass) → PostgreSQL sync; distance, phone, hours, website, dietary tags; caching and an offline fallback to saved restaurants |
| **Dietary awareness** | Vegetarian, Vegan, Jain, Gluten-Free, Dairy-Free. Each place is labelled **verified** (OSM tag / menu data), **likely** (inferred) or unknown — never presented as a guarantee |
| **AI recommendations** | Explainable 0–100 match score (dietary fit, quality, taste affinity from favourites/reviews, distance) with the reasons, a confidence level and a fallback note when data is thin |
| **Reviews + NLP** | Star rating + text; the backend runs sentiment analysis (overall + per dish + service/ambience/price), and produces an explainable **trust score** for each review |
| **Insights** | Trust-weighted overall sentiment, best-rated dish, dish list, confidence ("only 2 reviews so far…") |
| **Favourites** | Save places; they also teach the recommender your taste |

## 🧱 Tech stack

- **Frontend:** React 19, Vite, React Router, lucide-react, plain CSS · tests with Vitest + Testing Library
- **Backend:** FastAPI, SQLAlchemy 2, Pydantic 2, PyJWT, bcrypt, httpx · tests with pytest
- **Database:** PostgreSQL (SQLite is used only for the fast test run)
- **Data:** OpenStreetMap / Overpass API
- **AI:** in-house, explainable NLP + ranking (see [`docs/AI_METHODOLOGY.md`](docs/AI_METHODOLOGY.md)) — no external AI service or API key needed

## 🚀 Run it locally

**Prerequisites:** Python 3.12+, Node 20+, PostgreSQL.

```bash
# 1. Database
createdb dinesmart            # or create it in pgAdmin

# 2. Backend  (http://127.0.0.1:8000, docs at /docs)
cd backend
python -m venv venv
venv\Scripts\activate         # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # then edit DATABASE_URL (and set SECRET_KEY)
uvicorn app.main:app --reload

# 3. Frontend (http://localhost:5173)
cd frontend
npm install
npm run dev
```

Tables are created automatically on startup, and an **existing database is upgraded in place** (new columns are added, nothing is deleted).

## 🧪 Tests

```bash
# backend (SQLite, fast)
cd backend && pip install -r requirements-dev.txt && pytest

# backend against PostgreSQL (what CI does). The DB name must contain "test"
# because the suite drops and recreates its tables:
TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/dinesmart_test pytest

# frontend
cd frontend && npm run lint && npm test && npm run build
```

## 🐳 Deploy

`docker compose up --build` runs Postgres + API + website. See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
CI (GitHub Actions) runs the backend tests on PostgreSQL, the frontend lint/tests/build, and builds both Docker images.

## 📂 Project structure

```
DineSmart-AI/
├── backend/
│   ├── app/
│   │   ├── api/            auth, users, restaurants, reviews, favorites, recommendations
│   │   ├── services/       sentiment, trust, dietary, recommender, insights, discovery, …
│   │   ├── models/         SQLAlchemy tables
│   │   ├── schemas/        request validation
│   │   ├── config.py  security.py  migrations.py  main.py
│   ├── tests/              pytest suite
│   └── requirements.txt
├── frontend/
│   └── src/  pages/ components/ hooks/ services/ utils/
├── docs/                   API, AI methodology, deployment, DB design, diagrams
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## 📖 Documentation

- [Problem Statement](Problem_Statement.md)
- [API reference](docs/API.md)
- [AI methodology & limitations](docs/AI_METHODOLOGY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Database design](docs/Database_Design.md)
- Architecture / ER / module diagrams in `docs/diagrams/`

## ⚠️ Responsible AI

Dietary information comes from OpenStreetMap, menus and reviews and can be incomplete. DineSmart AI provides food-discovery insights, **not medical advice**, and never guarantees a dish is allergen-free. Review-trust scores are *indicators of low-information or promotional patterns*, not proof that a review is fake.

## 🗺️ Not built yet (future scope)

Restaurant-owner and admin roles (menu management, moderation), real restaurant photos, a learned (ML) sentiment model, and Redis-backed rate limiting for multi-server deployments.

## 📌 Status

🟢 Design, backend, frontend, AI features, tests, CI and deployment setup complete.
