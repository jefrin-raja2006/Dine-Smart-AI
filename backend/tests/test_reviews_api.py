GOOD = "The biryani was excellent and the service was really good. Loved the raita too."


def post(client, headers, rid, rating=5, text=GOOD):
    return client.post(f"/restaurants/{rid}/reviews", json={"rating": rating, "text": text}, headers=headers)


def test_review_requires_login(client, make_restaurant):
    r = make_restaurant()
    assert client.post(f"/restaurants/{r.id}/reviews", json={"rating": 5, "text": GOOD}).status_code == 401


def test_review_is_analysed_and_rating_updated(client, make_user, make_restaurant, db):
    headers, _ = make_user(name=("Priya", "K"))
    r = make_restaurant()
    resp = post(client, headers, r.id, 5)
    assert resp.status_code == 201
    body = resp.json()

    assert body["sentiment"] == "positive" and body["sentiment_score"] > 0.3
    assert body["trust_label"] in ("high", "medium") and 0 <= body["trust_score"] <= 1
    assert {m["name"] for m in body["mentions"]} >= {"biryani", "service"}
    assert body["is_mine"] and body["user_name"] == "Priya K"

    detail = client.get(f"/restaurants/{r.id}").json()
    assert detail["rating"] == 5.0 and detail["review_count"] == 1
    db.refresh(r)
    assert r.rating == 5.0                         # denormalised column kept in sync


def test_posting_again_replaces_review(client, make_user, make_restaurant):
    headers, _ = make_user()
    r = make_restaurant()
    post(client, headers, r.id, 5)
    post(client, headers, r.id, 2, "The dosa was cold and the staff were rude to us.")

    reviews = client.get(f"/restaurants/{r.id}/reviews").json()
    assert reviews["total"] == 1
    assert reviews["reviews"][0]["rating"] == 2
    assert reviews["reviews"][0]["sentiment"] == "negative"
    assert client.get(f"/restaurants/{r.id}").json()["rating"] == 2.0


def test_average_rating_over_users(client, make_user, make_restaurant):
    r = make_restaurant()
    for stars in (5, 4, 3):
        headers, _ = make_user()
        post(client, headers, r.id, stars, f"Decent food overall, ordered dosa number {stars}, staff polite.")
    assert client.get(f"/restaurants/{r.id}").json()["rating"] == 4.0


def test_validation(client, make_user, make_restaurant):
    headers, _ = make_user()
    r = make_restaurant()
    assert post(client, headers, r.id, 0).status_code == 422
    assert post(client, headers, r.id, 6).status_code == 422
    assert post(client, headers, r.id, 5, "ok").status_code == 422
    assert post(client, headers, r.id, 5, "x" * 2001).status_code == 422
    assert post(client, headers, 9999).status_code == 404


def test_duplicate_text_from_other_user_lowers_trust(client, make_user, make_restaurant):
    r = make_restaurant()
    a, _ = make_user()
    b, _ = make_user()
    first = post(client, a, r.id).json()
    second = post(client, b, r.id).json()
    assert second["trust_score"] < first["trust_score"]
    assert any("Identical" in reason for reason in second["trust_reasons"])


def test_delete_my_review(client, make_user, make_restaurant):
    headers, _ = make_user()
    r = make_restaurant()
    post(client, headers, r.id)
    assert client.delete(f"/restaurants/{r.id}/reviews/mine", headers=headers).status_code == 200
    assert client.get(f"/restaurants/{r.id}").json()["rating"] is None
    assert client.delete(f"/restaurants/{r.id}/reviews/mine", headers=headers).status_code == 404


def test_cannot_delete_someone_elses_review(client, make_user, make_restaurant):
    a, _ = make_user()
    b, _ = make_user()
    r = make_restaurant()
    post(client, a, r.id)
    assert client.delete(f"/restaurants/{r.id}/reviews/mine", headers=b).status_code == 404
    assert client.get(f"/restaurants/{r.id}/reviews").json()["total"] == 1


def test_is_mine_flag_only_for_author(client, make_user, make_restaurant):
    a, _ = make_user()
    b, _ = make_user()
    r = make_restaurant()
    post(client, a, r.id)
    assert client.get(f"/restaurants/{r.id}/reviews", headers=a).json()["reviews"][0]["is_mine"] is True
    assert client.get(f"/restaurants/{r.id}/reviews", headers=b).json()["reviews"][0]["is_mine"] is False
    assert client.get(f"/restaurants/{r.id}/reviews").json()["reviews"][0]["is_mine"] is False


def test_html_in_review_is_stored_as_plain_text(client, make_user, make_restaurant):
    headers, _ = make_user()
    r = make_restaurant()
    body = post(client, headers, r.id, 4, "<script>alert(1)</script> nice dosa and friendly staff").json()
    assert "<script>" in body["text"]            # returned verbatim; React escapes it on render


def test_insights_empty_state(client, make_restaurant):
    r = make_restaurant()
    body = client.get(f"/restaurants/{r.id}/insights").json()
    assert body["review_count"] == 0 and body["confidence"] == "none" and body["message"]


def test_insights_dish_level_and_confidence(client, make_user, make_restaurant):
    r = make_restaurant()
    texts = [
        (5, "The biryani was excellent and the service was really good, loved it."),
        (5, "Amazing biryani, best I have had. The dosa was okay but the staff were friendly."),
        (2, "The dosa was awful and cold. Staff were rude and the wait was very slow."),
    ]
    for stars, text in texts:
        headers, _ = make_user()
        post(client, headers, r.id, stars, text)

    body = client.get(f"/restaurants/{r.id}/insights").json()
    assert body["review_count"] == 3 and body["confidence"] == "medium"
    dishes = {d["name"]: d for d in body["dishes"]}
    assert dishes["biryani"]["label"] == "positive" and dishes["biryani"]["mentions"] == 2
    assert dishes["dosa"]["positive_pct"] < dishes["biryani"]["positive_pct"]
    assert body["best_dish"]["name"] == "biryani"
    assert body["trust"]["label"] in ("high", "medium")
    assert body["sentiment"]["distribution"]["negative"] >= 1


def test_low_trust_reviews_count_less(client, make_user, make_restaurant):
    from app.models.models import Review
    from app.services.insights import _weight

    r = make_restaurant()
    a, _ = make_user()
    post(client, a, r.id)
    review = client.get(f"/restaurants/{r.id}/reviews").json()["reviews"][0]
    assert 0.25 < review["trust_score"] <= 1.0
    assert _weight(Review(trust_score=0.0)) == 0.25 and _weight(Review(trust_score=1.0)) == 1.0


def test_single_review_gives_low_confidence_message(client, make_user, make_restaurant):
    r = make_restaurant()
    headers, _ = make_user()
    post(client, headers, r.id)
    body = client.get(f"/restaurants/{r.id}/insights").json()
    assert body["confidence"] == "low" and "indicative" in body["message"]
