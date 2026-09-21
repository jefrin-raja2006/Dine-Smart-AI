"""Nearby restaurant discovery: OpenStreetMap (Overpass) -> PostgreSQL.

Flow:  GPS point -> Overpass query -> named places -> upsert into the
`restaurants` table (keyed by osm_id) -> return rows with database IDs.

Improvements over the first version
  * one batched lookup/insert instead of one query per restaurant,
  * short-lived in-memory cache (Overpass is a free public service),
  * every value is clipped to its column size (a long OSM `cuisine` value used
    to make the whole insert fail),
  * if Overpass is down we fall back to previously saved restaurants.
"""

import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field

import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import Restaurant
from app.services.geo import bounding_box, haversine_km
from app.utils import clip

logger = logging.getLogger("dinesmart.discovery")

MAX_RESULTS = 300
_LOOKUP_CHUNK = 500

_AMENITY_LABELS = {
    "cafe": "Cafe",
    "fast_food": "Fast Food",
    "food_court": "Food Court",
    "restaurant": "Restaurant",
}


class OverpassUnavailable(Exception):
    """Every configured Overpass server failed."""


@dataclass
class Place:
    osm_id: str
    name: str
    amenity: str
    cuisine: str
    latitude: float
    longitude: float
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    opening_hours: str | None = None
    diet_tags: dict[str, str] = field(default_factory=dict)


@dataclass
class DiscoveryResult:
    restaurants: list[tuple[Restaurant, float]]     # (row, distance km)
    radius_used: int
    source: str                                     # openstreetmap | saved
    message: str | None = None


# =========================================================
# OVERPASS
# =========================================================

def build_query(latitude: float, longitude: float, radius: int) -> str:
    return f"""
    [out:json][timeout:25];
    (
      node["amenity"~"^(restaurant|fast_food|cafe|food_court)$"]["name"]
        (around:{radius},{latitude},{longitude});
      way["amenity"~"^(restaurant|fast_food|cafe|food_court)$"]["name"]
        (around:{radius},{latitude},{longitude});
    );
    out center tags;
    """


# (rounded lat, rounded lon, radius) -> (expires_at, elements)
_CACHE: "OrderedDict[tuple, tuple[float, list[dict]]]" = OrderedDict()
_CACHE_MAX_ENTRIES = 128


def clear_cache() -> None:
    _CACHE.clear()


def _cache_key(latitude: float, longitude: float, radius: int) -> tuple:
    # 3 decimals ~ 110 m: people standing in the same spot share results
    return (round(latitude, 3), round(longitude, 3), radius)


async def fetch_overpass(
    latitude: float, longitude: float, radius: int
) -> list[dict]:
    """Return raw Overpass elements (cached). Raises OverpassUnavailable."""
    key = _cache_key(latitude, longitude, radius)
    now = time.monotonic()

    cached = _CACHE.get(key)
    if cached and cached[0] > now:
        _CACHE.move_to_end(key)
        return cached[1]

    query = build_query(latitude, longitude, radius)
    headers = {
        "User-Agent": "DineSmartAI/1.0",
        "Accept": "application/json",
    }
    last_error = "no Overpass server configured"

    for server in settings.overpass_servers:
        try:
            async with httpx.AsyncClient(
                timeout=35, follow_redirects=True
            ) as client:
                response = await client.post(
                    server, data={"data": query}, headers=headers
                )
                response.raise_for_status()
                elements = response.json().get("elements", [])

        except httpx.HTTPStatusError as exc:
            last_error = f"{server} returned {exc.response.status_code}"
        except (httpx.RequestError, ValueError) as exc:
            last_error = f"{server}: {exc}"
        else:
            _CACHE[key] = (now + settings.nearby_cache_ttl_seconds, elements)
            _CACHE.move_to_end(key)
            while len(_CACHE) > _CACHE_MAX_ENTRIES:
                _CACHE.popitem(last=False)
            return elements

        logger.warning("Overpass failure: %s", last_error)

    raise OverpassUnavailable(last_error)


# =========================================================
# PARSING
# =========================================================

def prettify_cuisine(raw: str | None, amenity: str) -> str:
    """'south_indian;chinese' -> 'South Indian, Chinese'."""
    if raw:
        parts = [
            p.strip().replace("_", " ").title()
            for p in raw.replace(",", ";").split(";")
            if p.strip()
        ]
        if parts:
            return clip(", ".join(parts), 100)  # type: ignore[return-value]

    return _AMENITY_LABELS.get(amenity, "Restaurant")


def _address(tags: dict) -> str | None:
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb") or tags.get("addr:neighbourhood"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]
    joined = ", ".join(p.strip() for p in parts if p and p.strip())
    return clip(joined, 150) if joined else clip(tags.get("addr:full"), 150)


def parse_elements(elements: list[dict]) -> list[Place]:
    places: list[Place] = []
    seen: set[str] = set()

    for element in elements:
        tags = element.get("tags") or {}
        name = (tags.get("name") or "").strip()
        raw_id = element.get("id")

        if not name or raw_id is None:
            continue

        # type + id so a node and a way can never collide
        osm_id = f"{element.get('type', 'node')}_{raw_id}"
        if osm_id in seen:
            continue

        if element.get("type") == "node":
            lat, lon = element.get("lat"), element.get("lon")
        else:
            center = element.get("center") or {}
            lat, lon = center.get("lat"), center.get("lon")

        if lat is None or lon is None:
            continue

        seen.add(osm_id)
        amenity = tags.get("amenity", "restaurant")

        places.append(
            Place(
                osm_id=osm_id,
                name=clip(name, 150),  # type: ignore[arg-type]
                amenity=clip(amenity, 50) or "restaurant",  # type: ignore[arg-type]
                cuisine=prettify_cuisine(tags.get("cuisine"), amenity),
                latitude=float(lat),
                longitude=float(lon),
                address=_address(tags),
                phone=clip(tags.get("phone") or tags.get("contact:phone"), 100),
                website=tags.get("website") or tags.get("contact:website"),
                opening_hours=tags.get("opening_hours"),
                diet_tags={
                    key[5:]: str(value)
                    for key, value in tags.items()
                    if key.startswith("diet:")
                },
            )
        )

    return places


# =========================================================
# DATABASE SYNC
# =========================================================

def _sync_once(db: Session, places: list[Place]) -> dict[str, Restaurant]:
    ids = [p.osm_id for p in places]
    existing: dict[str, Restaurant] = {}

    for start in range(0, len(ids), _LOOKUP_CHUNK):
        chunk = ids[start:start + _LOOKUP_CHUNK]
        for row in db.query(Restaurant).filter(Restaurant.osm_id.in_(chunk)):
            existing[row.osm_id] = row

    for place in places:
        row = existing.get(place.osm_id)
        diet_json = json.dumps(place.diet_tags) if place.diet_tags else None

        if row is None:
            row = Restaurant(
                osm_id=place.osm_id,
                name=place.name,
                cuisine=place.cuisine,
                location=place.address,
                rating=0.0,
                image_url="",
                latitude=place.latitude,
                longitude=place.longitude,
                amenity=place.amenity,
                phone=place.phone,
                website=place.website,
                opening_hours=place.opening_hours,
                diet_tags=diet_json,
            )
            db.add(row)
            existing[place.osm_id] = row
        else:
            # keep our copy in sync; never touch rating / image_url
            row.name = place.name
            row.cuisine = place.cuisine
            row.latitude = place.latitude
            row.longitude = place.longitude
            row.amenity = place.amenity
            row.diet_tags = diet_json
            if place.address:
                row.location = place.address
            if place.phone:
                row.phone = place.phone
            if place.website:
                row.website = place.website
            if place.opening_hours:
                row.opening_hours = place.opening_hours

    db.flush()
    db.commit()
    return existing


def sync_places(db: Session, places: list[Place]) -> dict[str, Restaurant]:
    """Upsert places; returns {osm_id: Restaurant}.

    Two simultaneous requests may try to insert the same new restaurant
    (React StrictMode does exactly this in development). The loser hits the
    unique index on osm_id, so we roll back and retry once - by then the
    rows exist and are simply updated.
    """
    if not places:
        return {}

    try:
        return _sync_once(db, places)
    except IntegrityError:
        db.rollback()
        return _sync_once(db, places)


# =========================================================
# PUBLIC API
# =========================================================

def saved_restaurants_near(
    db: Session, latitude: float, longitude: float, radius_km: float
) -> list[tuple[Restaurant, float]]:
    """Previously synced restaurants around a point (used as a fallback)."""
    min_lat, max_lat, min_lon, max_lon = bounding_box(
        latitude, longitude, radius_km
    )

    rows = (
        db.query(Restaurant)
        .filter(
            Restaurant.latitude.isnot(None),
            Restaurant.longitude.isnot(None),
            Restaurant.latitude.between(min_lat, max_lat),
            Restaurant.longitude.between(min_lon, max_lon),
        )
        .all()
    )

    result = []
    for row in rows:
        distance = haversine_km(latitude, longitude, row.latitude, row.longitude)
        if distance <= radius_km:
            result.append((row, distance))

    result.sort(key=lambda pair: pair[1])
    return result[:MAX_RESULTS]


async def discover(
    db: Session, latitude: float, longitude: float, radius: int
) -> DiscoveryResult:
    """Find named food places around a GPS point and sync them to the DB."""
    radii = [radius]
    if radius < 10000:
        radii.append(10000)      # automatically widen an empty search

    for current_radius in radii:
        try:
            elements = await fetch_overpass(latitude, longitude, current_radius)
        except OverpassUnavailable as exc:
            logger.error("Overpass unavailable: %s", exc)

            saved = saved_restaurants_near(db, latitude, longitude, radius / 1000)
            if saved:
                return DiscoveryResult(
                    restaurants=saved,
                    radius_used=radius,
                    source="saved",
                    message=(
                        "Live OpenStreetMap data is temporarily unavailable. "
                        "Showing restaurants saved from earlier searches."
                    ),
                )
            raise

        places = parse_elements(elements)
        if not places:
            continue            # try the wider radius

        rows = sync_places(db, places)

        with_distance = [
            (
                rows[p.osm_id],
                haversine_km(latitude, longitude, p.latitude, p.longitude),
            )
            for p in places
        ]
        with_distance.sort(key=lambda pair: pair[1])

        return DiscoveryResult(
            restaurants=with_distance[:MAX_RESULTS],
            radius_used=current_radius,
            source="openstreetmap",
        )

    return DiscoveryResult(
        restaurants=[],
        radius_used=radii[-1],
        source="openstreetmap",
        message="No named food places were found near this location.",
    )
