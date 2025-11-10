#!/bin/bash
# ==========================================================
# 🧱 BedLink Entrypoint (v0.6.3)
# ----------------------------------------------------------
# Inicializa los archivos persistentes si no existen y
# lanza el proxy + panel FastAPI. Compatible con Docker
# bind mounts y ejecución directa.
# ==========================================================

APP_DIR="/app"

echo "🚀 Iniciando BedLink Entrypoint..."
mkdir -p "$APP_DIR"

# Crear los archivos necesarios si no existen
[ ! -f "$APP_DIR/servers.json" ] && echo '[]' > "$APP_DIR/servers.json"
[ ! -f "$APP_DIR/targets.json" ] && echo '{}' > "$APP_DIR/targets.json"
[ ! -f "$APP_DIR/player_sessions.json" ] && echo '{}' > "$APP_DIR/player_sessions.json"

echo "✅ Archivos verificados:"
ls -lh "$APP_DIR" | grep '.json'

echo "--------------------------------------------------"
echo "🧱 Lanzando BedLink-Menu (FastAPI + UDP Proxy)..."
echo "--------------------------------------------------"

# Ejecutar aplicación principal
exec python3 /app/main.py
