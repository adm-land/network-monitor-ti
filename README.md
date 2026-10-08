# Network Monitor TI

Sistema web para registrar dispositivos de una red y dar seguimiento a su disponibilidad, latencia y alertas. Lo desarrollé como parte de mi portafolio para combinar programación con temas de redes que he trabajado en Cisco y en la carrera.

La idea es mantener el proyecto enfocado en monitoreo básico y entendible: se agregan los equipos que se quieren supervisar y el sistema guarda los resultados de cada comprobación. No hace descubrimiento masivo ni escaneo de rangos completos.

## Funciones principales

- Inicio de sesión con roles de administrador, técnico y consulta.
- Registro de routers, switches, servidores, PCs, impresoras, access points y firewalls.
- IP o hostname, puerto TCP, MAC, fabricante, modelo y ubicación.
- Comprobación individual o de todos los dispositivos registrados.
- Estado En línea / Fuera de línea.
- Medición de latencia en milisegundos.
- Porcentaje de disponibilidad con base en las comprobaciones recientes.
- Historial de resultados por dispositivo.
- Alertas automáticas cuando un dispositivo deja de responder.
- Cierre automático de la alerta cuando el equipo vuelve a estar disponible.
- Dashboard con indicadores de salud de la red.
- Identificación de dispositivos con latencia alta.
- Vista lógica de topología.
- Búsqueda y filtros.
- Exportación de dispositivos a CSV.
- API de consulta en `/api/devices`.
- Historial de actividad para trazabilidad.
- Pruebas automáticas con Pytest y GitHub Actions.

## Tecnologías

Python, Flask, SQLAlchemy, MySQL / PyMySQL, HTML, CSS, Flask-Login, Flask-WTF, TCP/IP, sockets de Python, Cisco Packet Tracer, Docker Compose, Pytest, GitHub Actions y Gunicorn.

## Cómo funciona el monitoreo

En modo local, cada dispositivo tiene un host y un puerto TCP configurado. El sistema intenta establecer una conexión únicamente con ese equipo y ese puerto, mide el tiempo de respuesta y guarda el resultado.

No se escanean rangos de red ni múltiples puertos. Para usarlo en una red real, los equipos deben ser propios o estar autorizados para monitoreo.

La demo pública usa `MONITOR_MODE=demo` porque un servicio alojado en Internet no puede comprobar una red LAN privada. Ese modo permite enseñar el flujo de estados, latencia, alertas y recuperación sin realizar conexiones externas desde la demo.

## Ejecutarlo en local

```bash
python -m venv .venv
pip install -r requirements.txt
python seed.py
python run.py
```

### Usuarios de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@network.local` | `Admin123!` |
| Técnico | `tecnico@network.local` | `Tecnico123!` |
| Consulta | `consulta@network.local` | `Consulta123!` |

## Laboratorio Cisco

En `docs/topologia.md` dejé una topología de referencia y en `docs/cisco` están los comandos base para un router y un switch. Esto permite relacionar la aplicación con un laboratorio de direccionamiento y administración por SSH en Packet Tracer.

## Seguridad y alcance

El proyecto está hecho para monitorear únicamente dispositivos que se registran manualmente. En la demo pública las comprobaciones son simuladas y no generan tráfico hacia direcciones ingresadas por el usuario.

## Mejoras futuras

Más adelante se podría agregar monitoreo programado en segundo plano, notificaciones por correo, métricas históricas por periodo, SNMP de solo lectura y una topología más dinámica.

## Autor

**Alan Daniel Martínez Martínez**  
Estudiante de Ingeniería en Sistemas Computacionales — UNITEC
