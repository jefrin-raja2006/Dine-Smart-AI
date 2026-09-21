def test_favorite_lifecycle(client, make_user, make_restaurant):
    headers, _ = make_user()
    r = make_restaurant("Spice Hut")

    assert client.get(f"/favorites/check/{r.id}", headers=headers).json()["favorite"] is False
    assert client.post(f"/favorites/{r.id}", headers=headers).json()["favorite"] is True
    # idempotent
    assert client.post(f"/favorites/{r.id}", headers=headers).json()["message"].startswith("Restaurant already")
    assert client.get(f"/favorites/check/{r.id}", headers=headers).json()["favorite"] is True

    listing = client.get("/favorites", headers=headers).json()
    assert listing["count"] == 1
    assert listing["favorites"][0]["name"] == "Spice Hut"
    assert listing["favorites"][0]["restaurant_id"] == r.id

    assert client.delete(f"/favorites/{r.id}", headers=headers).json()["favorite"] is False
    assert client.delete(f"/favorites/{r.id}", headers=headers).status_code == 200  # idempotent
    assert client.get("/favorites", headers=headers).json()["count"] == 0


def test_favorites_are_private_per_user(client, make_user, make_restaurant):
    a, _ = make_user()
    b, _ = make_user()
    r = make_restaurant()
    client.post(f"/favorites/{r.id}", headers=a)

    assert client.get("/favorites", headers=b).json()["count"] == 0
    assert client.get(f"/favorites/check/{r.id}", headers=b).json()["favorite"] is False


def test_unknown_restaurant_404(client, make_user):
    headers, _ = make_user()
    assert client.post("/favorites/9999", headers=headers).status_code == 404
