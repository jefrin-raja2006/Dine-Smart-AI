from fastapi import APIRouter, HTTPException, Query
import httpx

router = APIRouter(
    prefix="/restaurants",
    tags=["Nearby Restaurants"]
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


@router.get("/nearby")
async def get_nearby_restaurants(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: int = Query(5000, ge=500, le=20000)
):
    query = f"""
    [out:json][timeout:25];

    (
      node["amenity"="restaurant"]
        (around:{radius},{latitude},{longitude});

      way["amenity"="restaurant"]
        (around:{radius},{latitude},{longitude});

      relation["amenity"="restaurant"]
        (around:{radius},{latitude},{longitude});
    );

    out center tags;
    """

    try:
        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.post(
                OVERPASS_URL,
                data={"data": query}
            )

            response.raise_for_status()

            data = response.json()

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Overpass API error: {str(e)}"
        )

    restaurants = []

    for element in data.get("elements", []):

        tags = element.get("tags", {})

        if element["type"] == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        else:
            center = element.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")

        restaurants.append({
            "osm_id": element.get("id"),
            "name": tags.get("name", "Unnamed Restaurant"),
            "cuisine": tags.get("cuisine", "Restaurant"),
            "latitude": lat,
            "longitude": lon,
            "address": tags.get("addr:full"),
            "street": tags.get("addr:street"),
            "city": tags.get("addr:city"),
            "postcode": tags.get("addr:postcode"),
            "phone": tags.get("phone"),
            "website": tags.get("website"),
            "opening_hours": tags.get("opening_hours")
        })

    return {
        "count": len(restaurants),
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "restaurants": restaurants
    }
