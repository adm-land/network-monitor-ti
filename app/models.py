from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="viewer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    events = db.relationship("AuditEvent", back_populates="actor")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def can_manage(self):
        return self.role in {"technician", "admin"}


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(40), nullable=False)
    host = db.Column(db.String(255), nullable=False, index=True)
    port = db.Column(db.Integer, nullable=False, default=80)
    mac_address = db.Column(db.String(30), nullable=True)
    vendor = db.Column(db.String(80), nullable=True)
    model = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(100), nullable=False, default="Oficina principal")
    status = db.Column(db.String(20), nullable=False, default="Desconocido")
    last_latency_ms = db.Column(db.Float, nullable=True)
    availability_pct = db.Column(db.Float, nullable=False, default=0)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    demo_profile = db.Column(db.String(20), nullable=False, default="online")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    checks = db.relationship("CheckResult", back_populates="device", cascade="all, delete-orphan", order_by="CheckResult.checked_at.desc()")
    alerts = db.relationship("Alert", back_populates="device", cascade="all, delete-orphan", order_by="Alert.opened_at.desc()")
    events = db.relationship("AuditEvent", back_populates="device", cascade="all, delete-orphan", order_by="AuditEvent.created_at.desc()")

    @property
    def open_alert(self):
        return next((alert for alert in self.alerts if alert.is_open), None)

    @property
    def health_label(self):
        if self.status == "Fuera de línea":
            return "Crítico"
        if self.status == "En línea" and self.last_latency_ms is not None and self.last_latency_ms > 150:
            return "Lento"
        if self.status == "En línea":
            return "Saludable"
        return "Sin datos"


class CheckResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)
    latency_ms = db.Column(db.Float, nullable=True)
    detail = db.Column(db.String(255), nullable=False)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"), nullable=False)

    device = db.relationship("Device", back_populates="checks")


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    severity = db.Column(db.String(20), nullable=False, default="Alta")
    message = db.Column(db.String(255), nullable=False)
    is_open = db.Column(db.Boolean, nullable=False, default=True)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"), nullable=False)

    device = db.relationship("Device", back_populates="alerts")


class AuditEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("device.id"), nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    device = db.relationship("Device", back_populates="events")
    actor = db.relationship("User", back_populates="events")
