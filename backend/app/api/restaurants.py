from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx

from app.database.connection import get_db
from app.models.models import Restaurant

router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"]
)

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


# =========================================================
# GET RESTAURANTS FROM DATABASE
# =========================================================

@router.get("/")
def get_restaurants(
    db: Session = Depends(get_db)
):
    return db.query(Restaurant).all()


# =========================================================
# GET NEARBY RESTAURANTS FROM OPENSTREETMAP
# =========================================================

@router.get("/nearby")
async def get_nearby_restaurants(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: int = Query(
        5000,
        ge=1000,
        le=15000
    )
):

    # -----------------------------------------------------
    # First search radius
    # -----------------------------------------------------

    search_radii = [radius]

    # Automatically expand if too few named places
    if radius < 10000:
        search_radii.append(10000)

    last_error = None

    for current_radius in search_radii:

        query = f"""
        [out:json][timeout:25];

        (
          node["amenity"~"restaurant|fast_food|cafe|food_court"]
            ["name"]
            (around:{current_radius},{latitude},{longitude});

          way["amenity"~"restaurant|fast_food|cafe|food_court"]
            ["name"]
            (around:{current_radius},{latitude},{longitude});
        );

        out center tags;
        """

        headers = {
            "User-Agent": "DineSmartAI/1.0",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        for server in OVERPASS_SERVERS:

            try:

                async with httpx.AsyncClient(
                    timeout=35,
                    follow_redirects=True
                ) as client:

                    response = await client.post(
                        server,
                        data={"data": query},
                        headers=headers
                    )

                    response.raise_for_status()

                    data = response.json()

                    restaurants = []
                    seen = set()

                    # -------------------------------------------------
                    # Convert OSM results
                    # -------------------------------------------------

                    for element in data.get(
                        "elements",
                        []
                    ):

                        tags = element.get(
                            "tags",
                            {}
                        )

                        name = tags.get(
                            "name"
                        )

                        # Ignore unnamed restaurants
                        if not name:
                            continue

                        # ---------------------------------------------
                        # Remove duplicates
                        # ---------------------------------------------

                        osm_id = element.get(
                            "id"
                        )

                        if osm_id in seen:
                            continue

                        seen.add(osm_id)

                        # ---------------------------------------------
                        # Coordinates
                        # ---------------------------------------------

                        if element.get(
                            "type"
                        ) == "node":

                            lat = element.get(
                                "lat"
                            )

                            lon = element.get(
                                "lon"
                            )

                        else:

                            center = element.get(
                                "center",
                                {}
                            )

                            lat = center.get(
                                "lat"
                            )

                            lon = center.get(
                                "lon"
                            )

                        # ---------------------------------------------
                        # Amenity
                        # ---------------------------------------------

                        amenity = tags.get(
                            "amenity",
                            "restaurant"
                        )

                        # ---------------------------------------------
                        # Cuisine
                        # ---------------------------------------------

                        cuisine = tags.get(
                            "cuisine"
                        )

                        if not cuisine:

                            if amenity == "cafe":
                                cuisine = "Cafe"

                            elif amenity == "fast_food":
                                cuisine = "Fast Food"

                            elif amenity == "food_court":
                                cuisine = "Food Court"

                            else:
                                cuisine = "Restaurant"

                        # ---------------------------------------------
                        # Address
                        # ---------------------------------------------

                        street = tags.get(
                            "addr:street"
                        )

                        city = tags.get(
                            "addr:city"
                        )

                        postcode = tags.get(
                            "addr:postcode"
                        )

                        address_parts = []

                        if street:
                            address_parts.append(
                                street
                            )

                        if city:
                            address_parts.append(
                                city
                            )

                        if postcode:
                            address_parts.append(
                                postcode
                            )

                        address = (
                            ", ".join(
                                address_parts
                            )
                            if address_parts
                            else None
                        )

                        # ---------------------------------------------
                        # Restaurant object
                        # ---------------------------------------------

                        restaurants.append({

                            "osm_id":
                                osm_id,

                            "name":
                                name,

                            "cuisine":
                                cuisine,

                            "amenity":
                                amenity,

                            "latitude":
                                lat,

                            "longitude":
                                lon,

                            "address":
                                address,

                            "street":
                                street,

                            "city":
                                city,

                            "postcode":
                                postcode,

                            "phone":
                                tags.get(
                                    "phone"
                                ),

                            "website":
                                tags.get(
                                    "website"
                                ),

                            "opening_hours":
                                tags.get(
                                    "opening_hours"
                                ),

                            "diet":
                                tags.get(
                                    "diet"
                                )
                        })

                    # -------------------------------------------------
                    # If we have useful results, return them
                    # -------------------------------------------------

                    if restaurants:

                        return {
                            "status": "success",
                            "source": "OpenStreetMap",
                            "count": len(
                                restaurants
                            ),
                            "search_location": {
                                "latitude":
                                    latitude,
                                "longitude":
                                    longitude,
                                "radius":
                                    current_radius
                            },
                            "restaurants":
                                restaurants
                        }

                    # No restaurants at this radius.
                    # Try the next radius.
                    break

            except httpx.HTTPStatusError as e:

                last_error = (
                    f"{server} returned "
                    f"{e.response.status_code}"
                )

                print(
                    "Overpass error:",
                    last_error
                )

                continue

            except httpx.RequestError as e:

                last_error = (
                    f"{server} connection error: "
                    f"{str(e)}"
                )

                print(
                    "Overpass connection error:",
                    last_error
                )

                continue

            except Exception as e:

                last_error = str(e)

                print(
                    "Unexpected Overpass error:",
                    last_error
                )

                continue

    # =========================================================
    # NOTHING FOUND
    # =========================================================

    return {
        "status": "success",
        "source": "OpenStreetMap",
        "count": 0,
        "search_location": {
            "latitude": latitude,
            "longitude": longitude,
            "radius": search_radii[-1]
        },
        "restaurants": [],
        "message": (
            "No named food places were found "
            "near this location."
        )
    }


# =========================================================
# GET RESTAURANT BY DATABASE ID
# =========================================================

@router.get("/{restaurant_id}")
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db)
):

    restaurant = (
        db.query(Restaurant)
        .filter(
            Restaurant.id == restaurant_id
        )
        .first()
    )

    if not restaurant:

        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    return restaurant


# =========================================================
# CREATE RESTAURANT
# =========================================================

@router.post("/")
def create_restaurant(
    name: str,
    cuisine: str,
    location: str,
    rating: float = 0.0,
    image_url: str = "",
    db: Session = Depends(get_db)
):

    restaurant = Restaurant(
        name=name,
        cuisine=cuisine,
        location=location,
        rating=rating,
        image_url=image_url
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant