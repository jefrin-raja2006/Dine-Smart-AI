import jwt

from app.config import settings

REG = {
    "first_name": "Asha", "last_name": "Rao", "email": "asha@example.com",
    "password": "password123", "dietary_preferences": ["vegetarian", "gluten free"],
}


def test_register_returns_token_and_normalised_prefs(client):
    r = client.post("/auth/register", json=REG)
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"] and body["token_type"] == "bearer"
    assert body["user"]["dietary_preferences"] == ["Vegetarian", "Gluten-Free"]
    assert "password" not in body["user"]


def test_duplicate_email_case_insensitive(client):
    client.post("/auth/register", json=REG)
    r = client.post("/auth/register", json={**REG, "email": "ASHA@Example.com"})
    assert r.status_code == 400


def test_short_and_overlong_passwords_rejected(client):
    assert client.post("/auth/register", json={**REG, "password": "short"}).status_code == 400
    r = client.post("/auth/register", json={**REG, "password": "a" * 80})
    assert r.status_code == 400  # would crash bcrypt if not guarded


def test_unknown_preference_rejected(client):
    r = client.post("/auth/register", json={**REG, "dietary_preferences": ["Carnivore"]})
    assert r.status_code == 400 and "Carnivore" in r.json()["detail"]


def test_invalid_email_rejected(client):
    assert client.post("/auth/register", json={**REG, "email": "nope"}).status_code == 422


def test_login_success_and_failure(client):
    client.post("/auth/register", json=REG)
    ok = client.post("/auth/login", json={"email": "ASHA@example.com", "password": "password123"})
    assert ok.status_code == 200 and ok.json()["access_token"]

    bad = client.post("/auth/login", json={"email": "asha@example.com", "password": "wrongpass1"})
    unknown = client.post("/auth/login", json={"email": "who@example.com", "password": "wrongpass1"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json()["detail"] == unknown.json()["detail"]   # no user enumeration


def test_login_is_rate_limited_after_repeated_failures(client):
    client.post("/auth/register", json=REG)
    for _ in range(settings.login_max_failures):
        assert client.post(
            "/auth/login", json={"email": "asha@example.com", "password": "wrongpass1"}
        ).status_code == 401
    blocked = client.post(
        "/auth/login", json={"email": "asha@example.com", "password": "password123"}
    )
    assert blocked.status_code == 429 and "Retry-After" in blocked.headers


def test_protected_endpoints_require_valid_token(client):
    assert client.get("/users/me").status_code == 401
    assert client.get("/favorites").status_code == 401
    assert client.get("/users/me", headers={"Authorization": "Bearer garbage"}).status_code == 401

    forged = jwt.encode({"sub": "1", "exp": 9999999999}, "wrong" * 10, "HS256")
    assert client.get("/users/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_token_for_deleted_user_rejected(client, make_user, db):
    from app.models.models import User

    headers, user = make_user()
    db.query(User).filter(User.id == user["id"]).delete()
    db.commit()
    assert client.get("/users/me", headers=headers).status_code == 401


def test_profile_and_stats(client, make_user):
    headers, _ = make_user(prefs=["Vegan"])
    body = client.get("/users/me", headers=headers).json()
    assert body["dietary_preferences"] == ["Vegan"]
    assert body["stats"] == {"favorites": 0, "reviews": 0, "average_rating_given": None}
    assert body["member_since"].endswith("Z")


def test_update_name_and_preferences(client, make_user):
    headers, _ = make_user(prefs=["Vegan"])
    assert client.put("/users/me", json={"name": "  New   Name "}, headers=headers).json()["name"] == "New Name"

    r = client.put("/users/me/preferences", json={"dietary_preferences": ["Jain", "jain", "Dairy-Free"]}, headers=headers)
    assert r.json()["dietary_preferences"] == ["Jain", "Dairy-Free"]
    assert client.put("/users/me/preferences", json={"dietary_preferences": []}, headers=headers).json()["dietary_preferences"] == []


def test_change_password(client, make_user):
    headers, user = make_user(email="pw@example.com")
    assert client.post("/users/me/password", json={"current_password": "nope", "new_password": "newpassword1"}, headers=headers).status_code == 400
    assert client.post("/users/me/password", json={"current_password": "password123", "new_password": "short"}, headers=headers).status_code == 400
    assert client.post("/users/me/password", json={"current_password": "password123", "new_password": "newpassword1"}, headers=headers).status_code == 200

    assert client.post("/auth/login", json={"email": "pw@example.com", "password": "password123"}).status_code == 401
    assert client.post("/auth/login", json={"email": "pw@example.com", "password": "newpassword1"}).status_code == 200


def test_security_headers_and_no_error_leak(client):
    r = client.get("/db-test")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.json()["status"] == "success"
    assert client.get("/health").json() == {"status": "ok"}
