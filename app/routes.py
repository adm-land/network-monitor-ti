import csv
import io
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response, jsonify, current_app
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from . import db
from .models import User, Device, CheckResult, Alert, AuditEvent
from .monitor import run_check

bp = Blueprint("main", __name__)
DEVICE_TYPES = {"Router", "Switch", "Servidor", "PC", "Impresora", "Access Point", "Firewall", "Otro"}


def manager_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.can_manage:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def filtered_devices(query):
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    device_type = request.args.get("type", "").strip()
    location = request.args.get("location", "").strip()
    if q:
        query = query.filter(or_(Device.name.ilike(f"%{q}%"), Device.host.ilike(f"%{q}%"), Device.mac_address.ilike(f"%{q}%"), Device.vendor.ilike(f"%{q}%"), Device.model.ilike(f"%{q}%")))
    if status in {"En línea", "Fuera de línea", "Desconocido"}:
        query = query.filter_by(status=status)
    if device_type in DEVICE_TYPES:
        query = query.filter_by(device_type=device_type)
    if location:
        query = query.filter(Device.location.ilike(f"%{location}%"))
    return query


def log_event(action, detail, device=None):
    db.session.add(AuditEvent(action=action, detail=detail, device=device, actor=current_user))


def update_availability(device):
    recent = CheckResult.query.filter_by(device_id=device.id).order_by(CheckResult.checked_at.desc()).limit(20).all()
    if recent:
        device.availability_pct = round((sum(1 for item in recent if item.status == "En línea") / len(recent)) * 100, 1)


def process_check(device):
    result = run_check(device, mode=current_app.config.get("MONITOR_MODE", "live"), timeout=current_app.config.get("MONITOR_TIMEOUT", 1.5))
    previous = device.status
    device.status = result["status"]
    device.last_latency_ms = result["latency_ms"]
    device.last_checked_at = result["checked_at"]
    device.updated_at = result["checked_at"]
    db.session.add(CheckResult(status=result["status"], latency_ms=result["latency_ms"], detail=result["detail"], checked_at=result["checked_at"], device=device))
    db.session.flush()
    update_availability(device)
    open_alert = device.open_alert
    if result["status"] == "Fuera de línea" and not open_alert:
        db.session.add(Alert(severity="Alta", message=f"{device.name} no responde", device=device))
        log_event("Alerta", "Se detectó pérdida de conectividad", device)
    elif result["status"] == "En línea" and open_alert:
        open_alert.is_open = False
        open_alert.closed_at = result["checked_at"]
        log_event("Recuperación", "El dispositivo volvió a responder", device)
    if previous != result["status"]:
        log_event("Estado", f"{previous} → {result['status']}", device)
    else:
        log_event("Comprobación", result["detail"], device)
    return result


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/dashboard")
@login_required
def dashboard():
    devices = Device.query.order_by(Device.name).all()
    open_alerts = Alert.query.filter_by(is_open=True).order_by(Alert.opened_at.desc()).all()
    metrics = {"total": len(devices), "online": sum(1 for d in devices if d.status == "En línea"), "offline": sum(1 for d in devices if d.status == "Fuera de línea"), "slow": sum(1 for d in devices if d.health_label == "Lento"), "alerts": len(open_alerts), "availability": round(sum(d.availability_pct for d in devices) / len(devices), 1) if devices else 0}
    type_counts = {}
    for device in devices:
        type_counts[device.device_type] = type_counts.get(device.device_type, 0) + 1
    max_count = max(type_counts.values(), default=1) or 1
    categories = [{"name": name, "count": count, "percent": round((count / max_count) * 100)} for name, count in sorted(type_counts.items(), key=lambda item: item[1], reverse=True)]
    recent_events = AuditEvent.query.order_by(AuditEvent.created_at.desc()).limit(7).all()
    return render_template("dashboard.html", metrics=metrics, devices=devices, alerts=open_alerts[:5], categories=categories, recent_events=recent_events)


@bp.route("/devices")
@login_required
def devices():
    items = filtered_devices(Device.query).order_by(Device.updated_at.desc()).all()
    return render_template("devices.html", devices=items, device_types=sorted(DEVICE_TYPES))


@bp.route("/devices/new", methods=["GET", "POST"])
@manager_required
def new_device():
    if request.method == "POST":
        name, device_type, host, location = (request.form.get(k, "").strip() for k in ["name", "device_type", "host", "location"])
        try:
            port = int(request.form.get("port", "80"))
        except ValueError:
            port = 0
        if not name or not host or not location or device_type not in DEVICE_TYPES or not 1 <= port <= 65535:
            flash("Revisa los campos obligatorios y el puerto.", "danger")
            return render_template("device_form.html", device_types=sorted(DEVICE_TYPES), device=None)
        device = Device(name=name, device_type=device_type, host=host, port=port, mac_address=request.form.get("mac_address", "").strip() or None, vendor=request.form.get("vendor", "").strip() or None, model=request.form.get("model", "").strip() or None, location=location, notes=request.form.get("notes", "").strip() or None, demo_profile=request.form.get("demo_profile", "online") if current_app.config.get("MONITOR_MODE") == "demo" else "online")
        db.session.add(device); db.session.flush(); log_event("Alta", f"{device.name} agregado al monitoreo", device); db.session.commit()
        flash("Dispositivo registrado.", "success")
        return redirect(url_for("main.device_detail", device_id=device.id))
    return render_template("device_form.html", device_types=sorted(DEVICE_TYPES), device=None)


@bp.route("/devices/<int:device_id>")
@login_required
def device_detail(device_id):
    device = db.get_or_404(Device, device_id)
    checks = CheckResult.query.filter_by(device_id=device.id).order_by(CheckResult.checked_at.desc()).limit(20).all()
    max_latency = max((item.latency_ms or 0 for item in checks), default=1) or 1
    history = [{"status": item.status, "latency": item.latency_ms, "percent": round(((item.latency_ms or 0) / max_latency) * 100) if item.latency_ms else 0, "checked_at": item.checked_at, "detail": item.detail} for item in reversed(checks)]
    return render_template("device_detail.html", device=device, history=history)


@bp.route("/devices/<int:device_id>/check", methods=["POST"])
@manager_required
def check_device(device_id):
    device = db.get_or_404(Device, device_id)
    result = process_check(device); db.session.commit()
    flash(f"{device.name} respondió correctamente." if result["status"] == "En línea" else f"{device.name} no respondió.", "success" if result["status"] == "En línea" else "danger")
    return redirect(url_for("main.device_detail", device_id=device.id))


@bp.route("/devices/check-all", methods=["POST"])
@manager_required
def check_all_devices():
    devices = Device.query.order_by(Device.id).all()
    for device in devices:
        process_check(device)
    db.session.commit(); flash(f"Se comprobaron {len(devices)} dispositivos.", "success")
    return redirect(url_for("main.dashboard"))


@bp.route("/alerts")
@login_required
def alerts():
    return render_template("alerts.html", alerts=Alert.query.order_by(Alert.is_open.desc(), Alert.opened_at.desc()).all())


@bp.route("/topology")
@login_required
def topology():
    devices = Device.query.order_by(Device.device_type, Device.name).all()
    groups = {"Core": [d for d in devices if d.device_type in {"Router", "Firewall", "Switch"}], "Servicios": [d for d in devices if d.device_type == "Servidor"], "Acceso": [d for d in devices if d.device_type in {"Access Point", "PC", "Impresora", "Otro"}]}
    return render_template("topology.html", groups=groups)


@bp.route("/devices/export.csv")
@login_required
def export_devices():
    items = filtered_devices(Device.query).order_by(Device.name).all(); output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["Nombre", "Tipo", "Host", "Puerto", "MAC", "Fabricante", "Modelo", "Ubicación", "Estado", "Latencia ms", "Disponibilidad %", "Último chequeo"])
    for d in items:
        writer.writerow([d.name, d.device_type, d.host, d.port, d.mac_address or "", d.vendor or "", d.model or "", d.location, d.status, d.last_latency_ms if d.last_latency_ms is not None else "", d.availability_pct, d.last_checked_at.isoformat() if d.last_checked_at else ""])
    return Response(output.getvalue(), mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=network_devices.csv"})


@bp.route("/api/devices")
@login_required
def api_devices():
    items = filtered_devices(Device.query).order_by(Device.name).all()
    return jsonify([{"id": d.id, "name": d.name, "type": d.device_type, "host": d.host, "port": d.port, "location": d.location, "status": d.status, "latency_ms": d.last_latency_ms, "availability_pct": d.availability_pct, "last_checked_at": d.last_checked_at.isoformat() if d.last_checked_at else None, "open_alert": bool(d.open_alert)} for d in items])


@bp.route("/admin/users")
@admin_required
def users():
    return render_template("users.html", users=User.query.order_by(User.name).all())
