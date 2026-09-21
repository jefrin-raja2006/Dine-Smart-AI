# Deployment

## Option A — Docker Compose (simplest)

```bash
cp .env.example .env          # set POSTGRES_PASSWORD and SECRET_KEY
docker compose up --build
```

Website → http://localhost:8080 · API → http://localhost:8000 (`/health`).

For a real server put both behind HTTPS (Caddy, nginx or your host's proxy) and set in `.env`:

```
API_PUBLIC_URL=https://api.yourdomain.com
WEB_PUBLIC_URL=https://yourdomain.com
```

`API_PUBLIC_URL` is baked into the website at build time; `WEB_PUBLIC_URL` becomes the API's CORS allow-list.
Generate a secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.

> The Docker setup was written and its steps verified manually (dependency install, production boot, frontend build),
> but the images themselves were not built in the environment where this was authored — run `docker compose build` once and check the CI "Docker" job.

## Option B — Managed hosting (e.g. Render, Railway, Fly.io + a hosted Postgres)

**Backend (web service, root `backend/`)**
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips "*"`
- Env: `ENVIRONMENT=production`, `SECRET_KEY`, `DATABASE_URL` (the `postgres://` form many hosts give is accepted), `CORS_ORIGINS=https://your-frontend`

**Frontend (static site, root `frontend/`)**
- Build: `npm ci && npm run build` (env `VITE_API_URL=https://your-api`) · Publish dir: `dist`
- Add an SPA rewrite: all paths → `/index.html` (otherwise refreshing `/restaurant/5` gives a 404).

## Production checklist

- [ ] `ENVIRONMENT=production` and a strong `SECRET_KEY` (the API refuses to start otherwise)
- [ ] HTTPS on both sites; `CORS_ORIGINS` lists only your real frontend origin
- [ ] Database backups enabled; database not exposed publicly
- [ ] Geolocation only works on HTTPS (or localhost) — browsers block it otherwise
- [ ] If you run more than one API instance, replace the in-memory login rate limiter/Overpass cache with Redis
- [ ] Be mindful of the public Overpass servers' fair-use policy (results are cached 5 min); consider your own instance at scale

## Upgrading an existing database

Nothing to run: on startup the API creates missing tables, adds new columns/indexes, removes duplicate favourites/reviews (needed for the new unique constraints) and seeds the dietary preferences. Existing users, favourites and bcrypt passwords keep working. **Back up before upgrading anyway.**
