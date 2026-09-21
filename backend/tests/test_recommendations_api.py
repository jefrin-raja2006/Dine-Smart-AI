from tests.conftest import osm_node

LOC = {"latitude": 13.0827, "longitude": 80.2707}


def test_requires_login(client):
    assert client.get("/recommendations/me").status_code == 401


def test_ranks_dietary_matches_first_with_reasons(client, fake_overpass, make_user):
    fake_overpass.elements = [
        osm_node(1, "Steak Palace", cuisine="steak_house", lat=13.0830, lon=80.2710),
        osm_node(2, "Green Bowl", cuisine="vegetarian", **{"diet:vegetarian": "only"}, lat=13.0900, lon=80.2800),
        osm_node(3, "Mystery Diner"),
    ]
    headers, _ = make_user(prefs=["Vegetarian"])
    body = client.get("/recommendations/me", params=LOC, headers=headers).json()

    names = [r["name"] for r in body["recommendations"]]
    assert names[0] == "Green Bowl" and names[-1] == "Steak Palace"
    top, bottom = body["recommendations"][0], body["recommendations"][-1]
    assert top["confidence"] == "high" and top["match_reasons"]
    assert bottom["confidence"] == "low" and "May not suit Vegetarian" in bottom["note"]
    assert body["personalised"] is True and body["preferences"] == ["Vegetarian"]
    assert "not medical advice" in body["disclaimer"]
    assert all(0 <= r["ai_match"] <= 100 for r in body["recommendations"])


def test_preferences_query_overrides_saved(client, fake_overpass, make_user):
    fake_overpass.elements = [osm_node(1, "Vegan Hub", cuisine="vegan")]
    headers, _ = make_user(prefs=[])
    body = client.get("/recommendations/me", params={**LOC, "preferences": "Vegan"}, headers=headers).json()
    assert body["preferences"] == ["Vegan"]
    assert client.get("/recommendations/me", params={**LOC, "preferences": "Bogus"}, headers=headers).status_code == 400


def test_favorites_shape_future_recommendations(client, fake_overpass, make_user):
    fake_overpass.elements = [
        osm_node(1, "Dragon Wok", cuisine="chinese", lat=13.09, lon=80.28),
        osm_node(2, "Pasta Corner", cuisine="italian", lat=13.09, lon=80.28),
    ]
    headers, _ = make_user()
    ids = {r["name"]: r["id"] for r in client.get("/restaurants/nearby", params=LOC).json()["restaurants"]}
    client.post(f"/favorites/{ids['Dragon Wok']}", headers=headers)

    # a *different* chinese place should now be boosted over an italian one
    fake_overpass.elements += [
        osm_node(3, "Noodle Town", cuisine="chinese", lat=13.095, lon=80.285),
        osm_node(4, "Pizza Town", cuisine="italian", lat=13.095, lon=80.285),
    ]
    recs = client.get("/recommendations/me", params=LOC, headers=headers).json()["recommendations"]
    score = {r["name"]: r["ai_match"] for r in recs}
    assert score["Noodle Town"] > score["Pizza Town"]
    assert next(r for r in recs if r["name"] == "Dragon Wok")["is_favorite"] is True


def test_reviews_feed_quality_and_best_dish(client, fake_overpass, make_user):
    fake_overpass.elements = [osm_node(1, "Fresh Spot"), osm_node(2, "Meh Spot")]
    headers, _ = make_user()
    ids = {r["name"]: r["id"] for r in client.get("/restaurants/nearby", params=LOC).json()["restaurants"]}
    client.post(f"/restaurants/{ids['Fresh Spot']}/reviews", headers=headers,
                json={"rating": 5, "text": "The dosa was excellent and the staff were friendly, loved it."})
    client.post(f"/restaurants/{ids['Meh Spot']}/reviews", headers=headers,
                json={"rating": 1, "text": "The dosa was terrible and the service was rude and slow."})

    recs = client.get("/recommendations/me", params=LOC, headers=headers).json()["recommendations"]
    assert recs[0]["name"] == "Fresh Spot" and recs[0]["recommended_dish"] == "dosa"


def test_works_without_location_using_saved_restaurants(client, make_user, make_restaurant):
    make_restaurant("Saved One")
    headers, _ = make_user()
    body = client.get("/recommendations/me", headers=headers).json()
    assert body["count"] == 1 and body["recommendations"][0]["distance_km"] is None


def test_partial_coordinates_rejected(client, make_user):
    headers, _ = make_user()
    assert client.get("/recommendations/me", params={"latitude": 13.0}, headers=headers).status_code == 400


def test_overpass_outage_uses_saved(client, fake_overpass, make_user):
    fake_overpass.elements = [osm_node(1, "Cached Cafe")]
    headers, _ = make_user()
    client.get("/recommendations/me", params=LOC, headers=headers)
    fake_overpass.fail = True
    body = client.get("/recommendations/me", params=LOC, headers=headers).json()
    assert body["count"] == 1 and "unavailable" in body["message"]
