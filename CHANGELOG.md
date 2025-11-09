# 🧱 Bedlink – Changelog

## v1.0.0 – Primer Release Público
**Fecha:** 2025-11-09

### ✨ Novedades
- Implementación base de servidor **BedrockConnect alternativo** compatible con Minecraft Bedrock.
- Soporte para **autenticación con contraseña** (panel `/` protegido).
- Panel de administración simple en `http://IP:8090` para gestionar servidores.
- Persistencia de configuración en `servers.json`.
- Respuestas `PONG` y manejo básico de **heartbeats UDP**.
- Dockerfile y `docker-compose.yml` para despliegue rápido.
- Imagen pública en Docker Hub:  
  [`carolusx74/bedlink:latest`](https://hub.docker.com/r/carolusx74/bedlink)

### 🐛 Fixes
- Corrección de permisos y rutas en `/app`.
- Manejador robusto de `targets.json` para evitar errores cuando la ruta apunta a un directorio.
