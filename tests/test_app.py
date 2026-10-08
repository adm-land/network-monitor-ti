from app import create_app, db
from app.models import User, Device, Alert, CheckResult


def make_app(tmp_path):
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}", "SECRET_KEY": "test", "WTF_CSRF_ENABLED": False, "MONITOR_MODE": "demo"})


def create_users(app):
    with app.app_context():
        admin = User(name="Admin", email="admin@test.local", role="admin"); admin.set_password("pass123")
        viewer = User(name="Viewer", email="viewer@test.local", role="viewer"); viewer.set_password("pass123")
        db.session.add_all([admin, viewer]); db.session.commit()


def login(client, email="admin@test.local"):
    return client.post("/login", data={"email": email, "password": "pass123"}, follow_redirects=True)


def create_device(client, profile="online"):
    return client.post("/devices/new", data={"name": "Switch laboratorio", "device_type": "Switch", "host": "192.168.1.2", "port": "22", "mac_address": "00:11:22:33:44:55", "vendor": "Cisco", "model": "2960", "location": "Laboratorio", "demo_profile": profile}, follow_redirects=True)


def test_health_login_and_permissions(tmp_path):
    app = make_app(tmp_path); create_users(app); client = app.test_client()
    assert client.get("/health").status_code == 200
    assert login(client).status_code == 200
    client.get("/logout"); login(client, "viewer@test.local")
    assert client.get("/devices/new").status_code == 403


def test_monitor_alert_api_and_export(tmp_path):
    app = make_app(tmp_path); create_users(app); client = app.test_client(); login(client); assert create_device(client, "offline").status_code == 200
    with app.app_context(): device_id = Device.query.first().id
    assert client.post(f"/devices/{device_id}/check", follow_redirects=True).status_code == 200
    with app.app_context():
        assert db.session.get(Device, device_id).status == "Fuera de línea"
        assert Alert.query.filter_by(device_id=device_id, is_open=True).count() == 1
        assert CheckResult.query.filter_by(device_id=device_id).count() == 1
    assert client.get("/api/devices").get_json()[0]["status"] == "Fuera de línea"
    assert b"Switch laboratorio" in client.get("/devices/export.csv").data
