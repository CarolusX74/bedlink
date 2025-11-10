# 🧱 Bedlink – Changelog

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
