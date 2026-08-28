import pytest

import app.webapp.server as server_module
from app.webapp.server import create_app


@pytest.fixture(autouse=True)
def reset_login_attempts():
    server_module._login_attempts.clear()
    yield
    server_module._login_attempts.clear()


@pytest.fixture
def config(make_config):
    return make_config(web_password="test-pw")


@pytest.fixture
def client(config):
    app = create_app(config)
    app.testing = True
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    response = client.post("/api/login", json={"password": "test-pw"})
    assert response.status_code == 200
    return client


def test_session_reports_unauthenticated_by_default(client):
    response = client.get("/api/session")

    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}


def test_login_with_correct_password_authenticates(client):
    response = client.post("/api/login", json={"password": "test-pw"})

    assert response.status_code == 200
    assert response.get_json() == {"ok": True}
    assert client.get("/api/session").get_json() == {"authenticated": True}


def test_login_with_wrong_password_fails(client):
    response = client.post("/api/login", json={"password": "nope"})

    assert response.status_code == 401
    assert "error" in response.get_json()
    assert client.get("/api/session").get_json() == {"authenticated": False}


def test_logout_clears_session(logged_in_client):
    response = logged_in_client.post("/api/logout")

    assert response.status_code == 200
    assert logged_in_client.get("/api/session").get_json() == {"authenticated": False}


def test_lockout_after_max_failed_attempts(client):
    for _ in range(5):
        client.post("/api/login", json={"password": "wrong"})

    response = client.post("/api/login", json={"password": "test-pw"})

    assert response.status_code == 429


def test_lockout_expires_after_window(client, monkeypatch):
    fake_time = [1000.0]
    monkeypatch.setattr(server_module.time, "time", lambda: fake_time[0])

    for _ in range(5):
        client.post("/api/login", json={"password": "wrong"})
    assert client.post("/api/login", json={"password": "test-pw"}).status_code == 429

    fake_time[0] += server_module._LOCKOUT_SECONDS + 1

    response = client.post("/api/login", json={"password": "test-pw"})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/captures"),
        ("get", "/api/logs"),
        ("get", "/api/stream"),
        ("delete", "/api/captures/whatever"),
    ],
)
def test_protected_endpoints_require_login(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 401


def test_captures_lists_only_dirs_with_trigger_frame(logged_in_client, config):
    with_trigger = config.captures_dir / "event-with-trigger"
    with_trigger.mkdir(parents=True)
    (with_trigger / "trigger.jpeg").write_bytes(b"fake-jpeg")
    (with_trigger / "video.mp4").write_bytes(b"fake-video")

    without_trigger = config.captures_dir / "event-without-trigger"
    without_trigger.mkdir(parents=True)

    response = logged_in_client.get("/api/captures")

    assert response.status_code == 200
    items = response.get_json()
    assert [item["name"] for item in items] == ["event-with-trigger"]
    assert items[0]["has_video"] is True


def test_captures_reports_has_video_false_without_video_file(logged_in_client, config):
    event_dir = config.captures_dir / "event-no-video"
    event_dir.mkdir(parents=True)
    (event_dir / "trigger.jpeg").write_bytes(b"fake-jpeg")

    response = logged_in_client.get("/api/captures")

    items = response.get_json()
    assert items[0]["has_video"] is False


def test_delete_capture_removes_existing_dir(logged_in_client, config):
    event_dir = config.captures_dir / "event-to-delete"
    event_dir.mkdir(parents=True)
    (event_dir / "trigger.jpeg").write_bytes(b"fake-jpeg")

    response = logged_in_client.delete("/api/captures/event-to-delete")

    assert response.status_code == 200
    assert not event_dir.exists()


def test_get_capture_serves_allowed_filenames(logged_in_client, config):
    event_dir = config.captures_dir / "event-1"
    event_dir.mkdir(parents=True)
    (event_dir / "trigger.jpeg").write_bytes(b"fake-jpeg-bytes")

    response = logged_in_client.get("/captures/event-1/trigger.jpeg")

    assert response.status_code == 200
    assert response.data == b"fake-jpeg-bytes"


def test_get_capture_rejects_unknown_filenames(logged_in_client):
    response = logged_in_client.get("/captures/some-event/not-allowed.txt")

    assert response.status_code == 404


def test_delete_capture_cannot_escape_captures_dir(logged_in_client, config):
    # Whether Werkzeug's own routing normalizes ".." before it reaches our
    # guard, or the guard in delete_capture() catches it, nothing outside
    # captures_dir must ever be touched.
    secret_dir = config.data_dir / "secret"
    secret_dir.mkdir(parents=True)
    (secret_dir / "keepme.txt").write_text("do not delete", encoding="utf-8")

    response = logged_in_client.delete("/api/captures/..%2Fsecret")

    assert response.status_code in (404, 405)
    assert (secret_dir / "keepme.txt").exists()


def test_delete_capture_missing_dir_returns_404(logged_in_client):
    response = logged_in_client.delete("/api/captures/does-not-exist")

    assert response.status_code == 404
