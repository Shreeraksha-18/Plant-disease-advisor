import io
import uuid

from PIL import Image

PASSWORD = "test12345"


def make_user(client):
    """Register a fresh user, log in, and return (username, auth headers)."""
    username = "u_" + uuid.uuid4().hex[:8]
    r = client.post("/auth/register", json={"username": username, "password": PASSWORD})
    assert r.status_code == 201
    r = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert r.status_code == 200
    return username, {"Authorization": "Bearer " + r.json()["access_token"]}


def leaf_png():
    img = Image.new("RGB", (300, 300), (60, 140, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def upload(client, headers):
    return client.post("/predict", headers=headers, files={"file": ("leaf.png", leaf_png(), "image/png")})


# ---------- system ----------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_classes_lists_38(client):
    r = client.get("/classes")
    assert r.status_code == 200
    assert len(r.json()["classes"]) == 38


# ---------- authentication ----------

def test_register_and_duplicate(client):
    username = "u_" + uuid.uuid4().hex[:8]
    r = client.post("/auth/register", json={"username": username, "password": PASSWORD})
    assert r.status_code == 201
    assert r.json()["username"] == username
    assert "password" not in r.text          # the password or its hash is never returned
    r = client.post("/auth/register", json={"username": username, "password": PASSWORD})
    assert r.status_code == 409


def test_register_validation(client):
    r = client.post("/auth/register", json={"username": "abc", "password": "short"})
    assert r.status_code == 422


def test_login_wrong_password(client):
    username, _ = make_user(client)
    r = client.post("/auth/login", data={"username": username, "password": "wrong-password"})
    assert r.status_code == 401


def test_me_requires_valid_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    username, headers = make_user(client)
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == username


# ---------- predict ----------

def test_predict_requires_login(client):
    r = client.post("/predict", files={"file": ("leaf.png", leaf_png(), "image/png")})
    assert r.status_code == 401


def test_predict_rejects_bad_files(client):
    _, headers = make_user(client)
    r = client.post("/predict", headers=headers, files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400
    r = client.post("/predict", headers=headers, files={"file": ("a.jpg", b"not an image", "image/jpeg")})
    assert r.status_code == 400


def test_predict_returns_result_and_saves_record(client):
    _, headers = make_user(client)
    r = upload(client, headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "uncertain")
    assert body["record_id"] is not None
    assert 0.0 <= body["prediction"]["confidence"] <= 1.0
    if body["status"] == "ok":
        assert body["explanation"]["summary"]


# ---------- CRUD on saved predictions ----------

def test_full_crud_flow(client):
    _, headers = make_user(client)
    rid = upload(client, headers).json()["record_id"]

    # Read (list + one)
    r = client.get("/predictions", headers=headers)
    assert r.status_code == 200
    assert any(row["id"] == rid for row in r.json())
    r = client.get(f"/predictions/{rid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == rid

    # Update
    r = client.put(f"/predictions/{rid}", headers=headers, json={"note": "checked in test"})
    assert r.status_code == 200
    assert r.json()["note"] == "checked in test"
    assert client.put(f"/predictions/{rid}", headers=headers, json={"disease": "Not_A_Class"}).status_code == 400
    assert client.put(f"/predictions/{rid}", headers=headers, json={}).status_code == 400

    # Delete
    assert client.delete(f"/predictions/{rid}", headers=headers).status_code == 204
    assert client.get(f"/predictions/{rid}", headers=headers).status_code == 404


def test_users_cannot_see_each_others_records(client):
    _, headers_a = make_user(client)
    _, headers_b = make_user(client)
    rid = upload(client, headers_a).json()["record_id"]

    assert client.get(f"/predictions/{rid}", headers=headers_b).status_code == 404
    assert client.put(f"/predictions/{rid}", headers=headers_b, json={"note": "x"}).status_code == 404
    assert client.delete(f"/predictions/{rid}", headers=headers_b).status_code == 404
    assert all(row["id"] != rid for row in client.get("/predictions", headers=headers_b).json())
    # and the owner still has it
    assert client.get(f"/predictions/{rid}", headers=headers_a).status_code == 200


def test_support_endpoint(client):
    _, headers = make_user(client)
    res = upload(client, headers).json()
    rid = res["record_id"]

    r = client.get(f"/predictions/{rid}/support", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "disease" in data
    assert "disease_readable" in data
    assert "recommended_products" in data
    assert isinstance(data["recommended_products"], list)
    assert len(data["recommended_products"]) > 0
    assert "where_to_buy" in data
    assert len(data["where_to_buy"]) > 0
    assert "disclaimer" in data
    assert "officer" in data["disclaimer"].lower()


def test_chat_endpoints(client):
    _, headers = make_user(client)
    res = upload(client, headers).json()
    rid = res["record_id"]

    # Send a question
    r = client.post(
        f"/predictions/{rid}/chat",
        headers=headers,
        json={"message": "What preventive care is needed?"},
    )
    if res.get("status") == "ok":
        assert r.status_code == 200
        assert "reply" in r.json()
        assert r.json()["record_id"] == rid

        r_hist = client.get(f"/predictions/{rid}/chat", headers=headers)
        assert r_hist.status_code == 200
        messages = r_hist.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What preventive care is needed?"
        assert messages[1]["role"] == "assistant"
    else:
        assert r.status_code == 400
