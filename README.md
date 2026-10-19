# Network Monitor TI

Sistema web para **registrar y monitorear dispositivos de red**, dando seguimiento a disponibilidad, latencia, historial de comprobaciones y alertas.

Lo desarrollé como proyecto de portafolio para combinar programación con fundamentos de redes y laboratorios Cisco. El enfoque es mantener un monitoreo básico, claro y controlado: los dispositivos se registran manualmente y el sistema guarda los resultados de cada comprobación.

## Demo pública

**Probar aplicación:** https://network-monitor-ti-alan.onrender.com

> La demo pública utiliza `MONITOR_MODE=demo`, por lo que simula las comprobaciones de red para mostrar estados, latencia, alertas y recuperación sin generar tráfico hacia redes externas.

## Funcionalidades principales

### Gestión de dispositivos
- Registro de routers, switches, servidores, PCs, impresoras, access points y firewalls.
- Configuración de IP o hostname, puerto TCP, MAC, fabricante, modelo y ubicación.
- Búsqueda y filtros.
- Exportación de dispositivos a CSV.

### Monitoreo
- Comprobación individual o de todos los dispositivos registrados.
- Estado **En línea / Fuera de línea**.
- Medición de latencia en milisegundos.
- Porcentaje de disponibilidad basado en comprobaciones recientes.
- Historial de resultados por dispositivo.
- Identificación de dispositivos con latencia alta.

### Alertas y trazabilidad
- Alertas automáticas cuando un dispositivo deja de responder.
- Cierre automático de la alerta cuando el equipo vuelve a estar disponible.
- Historial de actividad.
- Dashboard con indicadores de salud de la red.
- Vista lógica de topología.

### API y calidad
- API de consulta en `/api/devices`.
- Inicio de sesión con roles de administrador, técnico y consulta.
- Pruebas automáticas con Pytest.
- GitHub Actions para validación automática.

## Tecnologías

- **Backend:** Python, Flask, SQLAlchemy
- **Base de datos:** MySQL / PyMySQL
- **Frontend:** HTML, CSS
- **Redes:** TCP/IP, sockets de Python, Cisco Packet Tracer
- **Autenticación y formularios:** Flask-Login, Flask-WTF
- **Infraestructura:** Docker Compose, Gunicorn, Render
- **Calidad:** Pytest, GitHub Actions

## Cómo funciona el monitoreo

En modo local, cada dispositivo tiene un host y un puerto TCP configurado. El sistema intenta establecer una conexión únicamente con ese equipo y ese puerto, mide el tiempo de respuesta y almacena el resultado.

No se escanean rangos completos ni múltiples puertos. Para utilizarlo en una red real, los equipos deben ser propios o estar autorizados para monitoreo.

La demo pública utiliza `MONITOR_MODE=demo`, ya que un servicio alojado en Internet no puede comprobar directamente una red LAN privada. Este modo permite mostrar estados, latencia, alertas y recuperación sin realizar conexiones externas desde la demo.

## Ejecución local

```bash
python -m venv .venv
pip install -r requirements.txt
python seed.py
python run.py
```

## Usuarios de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@network.local` | `Admin123!` |
| Técnico | `tecnico@network.local` | `Tecnico123!` |
| Consulta | `consulta@network.local` | `Consulta123!` |

## Laboratorio Cisco

En `docs/topologia.md` se incluye una topología de referencia y en `docs/cisco` están los comandos base para un router y un switch. Esto relaciona la aplicación con un laboratorio de direccionamiento y administración por SSH en Cisco Packet Tracer.

## Seguridad y alcance

El proyecto está diseñado para monitorear únicamente dispositivos que se registran manualmente. En la demo pública, las comprobaciones son simuladas y no generan tráfico hacia direcciones ingresadas por el usuario.

## Mejoras futuras

- Monitoreo programado en segundo plano.
- Notificaciones por correo.
- Métricas históricas por periodo.
- SNMP de solo lectura.
- Topología más dinámica.

## Autor

**Alan Daniel Martínez Martínez**  
Estudiante de Ingeniería en Sistemas Computacionales — UNITEC  
[GitHub](https://github.com/adm-land) · [LinkedIn](https://www.linkedin.com/in/alan-daniel-martinez-mart%C3%ADnez-5215a8218)
