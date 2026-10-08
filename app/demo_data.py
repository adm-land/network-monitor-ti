from datetime import datetime, timedelta
from . import db
from .models import User, Device, CheckResult, Alert, AuditEvent


def seed_demo_data(reset=False):
    if reset:
        db.drop_all()
        db.create_all()
    elif User.query.first():
        return False

    admin = User(name="Alan Martínez", email="admin@network.local", role="admin")
    admin.set_password("Admin123!")
    tech = User(name="Sofía Torres", email="tecnico@network.local", role="technician")
    tech.set_password("Tecnico123!")
    viewer = User(name="Carlos Mendoza", email="consulta@network.local", role="viewer")
    viewer.set_password("Consulta123!")
    db.session.add_all([admin, tech, viewer])
    db.session.flush()

    devices = [
        Device(name="Router principal", device_type="Router", host="192.168.10.1", port=443, mac_address="00:1A:2B:3C:4D:01", vendor="Cisco", model="ISR 4331", location="Site principal", status="En línea", last_latency_ms=18, availability_pct=99.8, demo_profile="online"),
        Device(name="Switch core", device_type="Switch", host="192.168.10.2", port=22, mac_address="00:1A:2B:3C:4D:02", vendor="Cisco", model="Catalyst 2960", location="Site principal", status="En línea", last_latency_ms=24, availability_pct=99.4, demo_profile="online"),
        Device(name="Servidor aplicaciones", device_type="Servidor", host="192.168.20.10", port=443, mac_address="00:1A:2B:3C:4D:03", vendor="Dell", model="PowerEdge", location="Rack 01", status="En línea", last_latency_ms=41, availability_pct=98.9, demo_profile="online"),
        Device(name="Access Point ventas", device_type="Access Point", host="192.168.30.15", port=80, mac_address="00:1A:2B:3C:4D:04", vendor="Cisco", model="Aironet", location="Piso 2", status="En línea", last_latency_ms=204, availability_pct=96.2, demo_profile="slow"),
        Device(name="Impresora administración", device_type="Impresora", host="192.168.40.25", port=9100, mac_address="00:1A:2B:3C:4D:05", vendor="HP", model="LaserJet Pro", location="Administración", status="Fuera de línea", availability_pct=87.5, demo_profile="offline"),
    ]
    db.session.add_all(devices)
    db.session.flush()

    now = datetime.utcnow()
    for device in devices:
        profile = device.demo_profile
        for i in range(8, 0, -1):
            checked_at = now - timedelta(hours=i * 2)
            if profile == "offline" and i <= 3:
                status, latency, detail = "Fuera de línea", None, "Sin respuesta TCP"
            elif profile == "slow":
                status, latency, detail = "En línea", 170 + i * 5, "Respuesta con latencia alta"
            else:
                status, latency, detail = "En línea", 15 + ((device.id + i) * 9) % 50, "Conectividad disponible"
            db.session.add(CheckResult(status=status, latency_ms=latency, detail=detail, checked_at=checked_at, device=device))

    alert = Alert(severity="Alta", message="Impresora administración no responde", device=devices[4], opened_at=now - timedelta(hours=5))
    db.session.add(alert)
    db.session.add_all([
        AuditEvent(action="Alta", detail="Router principal agregado al monitoreo", device=devices[0], actor=admin, created_at=now - timedelta(days=2)),
        AuditEvent(action="Comprobación", detail="Switch core respondió correctamente", device=devices[1], actor=tech, created_at=now - timedelta(hours=4)),
        AuditEvent(action="Alerta", detail="Se detectó pérdida de conectividad", device=devices[4], actor=admin, created_at=now - timedelta(hours=5)),
    ])
    db.session.commit()
    return True
