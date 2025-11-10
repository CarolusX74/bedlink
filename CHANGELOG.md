# 🧱 Bedlink – Changelog

## v0.5.1 – Reactive FastUDP (Stable)

**Fecha:** 2025-11-10
**Autor:** Carlos Pensa (@CarolusX74)

### ✨ Mejoras principales

* Proxy UDP optimizado con relay asíncrono **sin lag perceptible**.
* Eliminado el error `Destination address required` al conectar nuevos clientes.
* Estabilidad mejorada con control de sesiones inactivas (`SESSION_TTL`).
* Panel `/panel` funcional y compatible con FastAPI 0.115+.
* Código base simplificado y ajustado para **rendimiento + claridad**.
* Entrypoint actualizado (`v0.5.1-stable`) con detección automática de archivos.
* Dockerfile más limpio y portable (Python 3.12-slim + pip actualizado).
* Compatibilidad con Docker Compose LAN o túnel Cloudflare.

### 🐛 Fixes

* Corregido error `NameError: set_global_target no definido` al seleccionar un servidor.
* Corregido `player_sessions.json: Is a directory` en el entrypoint.
* Eliminados locks innecesarios en envío UDP que generaban micro-lag.

### 🧹 Estructura final

```
Dockerfile  
docker-compose.yml  
entrypoint.sh  
CHANGELOG.md  
app/
 ├─ main.py  
 ├─ servers.json  
 ├─ targets.json  
 └─ player_sessions.json  
```

---

## v0.5.0 – Base Reactive UDP

* Implementación inicial del motor asincrónico con FastAPI.
* Proxy UDP funcional y panel básico.
* Persistencia de `targets.json` y `servers.json`.
* Reducción de overhead de sockets respecto a v0.4.x.


## v0.6.4 – Refinamiento Pre-Release

**Fecha:** 2025-11-10

### ✨ Mejoras

* Dockerfile actualizado con `entrypoint.sh` para inicialización automática.
* Validación robusta de archivos `targets.json` y `servers.json` (creación si faltan).
* Script `build-and-push.sh v3` con soporte de versión, tags git y logging histórico.
* MOTD dinámico más corto y limpio para visualización in-game.
* Eliminación de warnings `[Errno 21] Is a directory: '/app/targets.json'`.

### 🧩 Estructura final

```
Dockerfile  
docker-compose.yml  
entrypoint.sh  
app/  
 ├─ main.py  
 ├─ menu_manager.py  
 ├─ udp_selector.py  
 ├─ servers.json  
 ├─ targets.json  
 └─ player_sessions.json  
```

---

## v0.6.3 – Primer Release Público

**Fecha:** 2025-11-09

### ✨ Novedades

* Implementación base de servidor **BedrockConnect alternativo** compatible con Minecraft Bedrock.
* Soporte para **autenticación con contraseña** (panel `/` protegido).
* Panel de administración simple en `http://IP:8090` para gestionar servidores.
* Persistencia de configuración en `servers.json`.
* Respuestas `PONG` y manejo básico de **heartbeats UDP**.
* Dockerfile y `docker-compose.yml` para despliegue rápido.
* Imagen pública en Docker Hub:
  [`carolusx74/bedlink:latest`](https://hub.docker.com/r/carolusx74/bedlink)

### 🐛 Fixes

* Corrección de permisos y rutas en `/app`.
* Manejador robusto de `targets.json` para evitar errores cuando la ruta apunta a un directorio.
