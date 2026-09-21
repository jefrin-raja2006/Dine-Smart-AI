from tests.conftest import osm_node

NEAR = {"latitude": 13.0827, "longitude": 80.2707, "radius": 5000}


def test_nearby_syncs_to_database_and_returns_ids(client, fake_overpass, db):
    from app.models.models import Restaurant

    fake_overpass.elements = [
        osm_node(1, "Udupi Bhavan", cuisine="south_indian;vegetarian", **{"diet:vegetarian": "only"}),
        osm_node(2, "Burger Barn", lat=13.09, lon=80.28, amenity="fast_food"),
        {"type": "way", "id": 3, "center": {"lat": 13.085, "lon": 80.275},
         "tags": {"amenity": "cafe", "name": "Cafe Way", "addr:street": "Main Rd", "addr:city": "Chennai"}},
        osm_node(4, ""),                      # unnamed -> ignored
        osm_node(1, "Udupi Bhavan"),          # duplicate -> ignored
    ]
    body = client.get("/restaurants/nearby", params=NEAR).json()

    assert body["count"] == 3
    first = body["restaurants"][0]
    assert first["name"] == "Udupi Bhavan"                 # nearest first
    assert first["id"] and first["osm_id"] == "node_1"
    assert first["cuisine"] == "South Indian, Vegetarian"
    assert first["distance_km"] == 0.0
    assert {"name": "Vegetarian", "level": "verified"}.items() <= first["diet_tags"][0].items()
    assert first["rating"] is None and first["review_count"] == 0

    way = next(r for r in body["restaurants"] if r["osm_id"] == "way_3")
    assert way["address"] == "Main Rd, Chennai" and way["cuisine"] == "Cafe"
    assert db.query(Restaurant).count() == 3


def test_nearby_is_idempotent_and_keeps_ids(client, fake_overpass):
    fake_overpass.elements = [osm_node(1, "A"), osm_node(2, "B")]
    first = {r["osm_id"]: r["id"] for r in client.get("/restaurants/nearby", params=NEAR).json()["restaurants"]}
    second = {r["osm_id"]: r["id"] for r in client.get("/restaurants/nearby", params=NEAR).json()["restaurants"]}
    assert first == second


def test_overlong_osm_values_do_not_break_sync(client, fake_overpass):
    fake_overpass.elements = [
        osm_node(1, "N" * 400, cuisine=";".join(f"cuisine_{i}" for i in range(40)),
                 **{"addr:street": "S" * 300}),
    ]
    body = client.get("/restaurants/nearby", params=NEAR).json()
    assert body["count"] == 1
    assert len(body["restaurants"][0]["cuisine"]) <= 100
    assert len(body["restaurants"][0]["name"]) <= 150


def test_sync_recovers_from_concurrent_insert_race(db, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session

    from app.services.discovery import Place, sync_places

    real_flush = Session.flush
    state = {"raised": False}

    def flaky_flush(self, *a, **kw):
        if not state["raised"]:
            state["raised"] = True
            raise IntegrityError("dup", None, Exception("unique violation"))
        return real_flush(self, *a, **kw)

    monkeypatch.setattr(Session, "flush", flaky_flush)
    place = Place("node_9", "Racey", "restaurant", "Cafe", 13.0, 80.0)
    rows = sync_places(db, [place])
    assert rows["node_9"].id is not None


def test_widens_radius_when_first_search_is_empty(client, fake_overpass):
    fake_overpass.elements = []
    body = client.get("/restaurants/nearby", params=NEAR).json()
    assert body["count"] == 0 and body["message"]
    assert fake_overpass.calls == 2          # 5 km then 10 km


def test_overpass_down_falls_back_to_saved_restaurants(client, fake_overpass):
    fake_overpass.elements = [osm_node(1, "Saved Place")]
    client.get("/restaurants/nearby", params=NEAR)

    fake_overpass.fail = True
    body = client.get("/restaurants/nearby", params=NEAR).json()
    assert body["count"] == 1 and body["source"] == "Saved data"
    assert "temporarily unavailable" in body["message"]


def test_overpass_down_and_nothing_saved_is_503(client, fake_overpass):
    fake_overpass.fail = True
    r = client.get("/restaurants/nearby", params=NEAR)
    assert r.status_code == 503


def test_nearby_validates_coordinates(client):
    assert client.get("/restaurants/nearby", params={"latitude": 200, "longitude": 0}).status_code == 422
    assert client.get("/restaurants/nearby", params={"latitude": 1, "longitude": 1, "radius": 99999}).status_code == 422


def test_restaurant_detail_and_404(client, make_restaurant):
    r = make_restaurant("Detail Cafe", cuisine="Cafe", phone="123", opening_hours="Mo-Su 09:00-22:00")
    body = client.get(f"/restaurants/{r.id}").json()
    assert body["name"] == "Detail Cafe" and body["menu_items"] == []
    assert len(body["diet_evidence"]) == 5
    assert "ai_match" not in body                       # anonymous: no personalisation
    assert client.get("/restaurants/99999").status_code == 404


def test_restaurant_detail_is_personalised_when_logged_in(client, make_user, make_restaurant):
    headers, _ = make_user(prefs=["Vegetarian"])
    r = make_restaurant("Green Bowl", cuisine="Vegetarian", diet_tags='{"vegetarian": "only"}')
    body = client.get(f"/restaurants/{r.id}", headers=headers, params={"latitude": 13.0827, "longitude": 80.2707}).json()
    assert body["ai_match"] > 50 and body["confidence"] == "high"
    assert body["match_reasons"] and body["is_favorite"] is False


def test_list_search_and_manual_create_requires_login(client, make_user, make_restaurant):
    make_restaurant("Alpha Grill", cuisine="Grill")
    make_restaurant("Beta Dosa", cuisine="South Indian")
    assert [r["name"] for r in client.get("/restaurants/", params={"q": "dosa"}).json()] == ["Beta Dosa"]

    assert client.post("/restaurants/", params={"name": "Sneaky"}).status_code == 401
    headers, _ = make_user()
    assert client.post("/restaurants/", params={"name": "Legit"}, headers=headers).status_code == 201
