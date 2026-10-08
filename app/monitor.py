import socket
import time
from datetime import datetime


def _demo_check(device):
    profile = device.demo_profile or "online"
    base = 12 + ((device.id or 1) * 17) % 65
    if profile == "offline":
        return "Fuera de línea", None, "Sin respuesta en la comprobación de demostración"
    if profile == "slow":
        return "En línea", float(180 + base), "Respuesta recibida con latencia alta"
    return "En línea", float(base), "Conectividad disponible"


def _tcp_check(device, timeout):
    started = time.perf_counter()
    try:
        with socket.create_connection((device.host, int(device.port)), timeout=timeout):
            latency = round((time.perf_counter() - started) * 1000, 1)
            return "En línea", latency, f"TCP {device.host}:{device.port} respondió"
    except (OSError, ValueError) as exc:
        return "Fuera de línea", None, f"Sin respuesta TCP: {type(exc).__name__}"


def run_check(device, mode="live", timeout=1.5):
    if mode == "demo":
        status, latency, detail = _demo_check(device)
    else:
        status, latency, detail = _tcp_check(device, timeout)
    return {
        "status": status,
        "latency_ms": latency,
        "detail": detail,
        "checked_at": datetime.utcnow(),
    }
