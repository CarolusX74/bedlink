#!/bin/bash
# ==========================================================
# 🧱 BedLink Entrypoint (v0.5.1-stable)
# ----------------------------------------------------------
# Inicializa los archivos persistentes si no existen y
# lanza el proxy + panel FastAPI.
# Compatible con Docker bind mounts y ejecución directa.
# ==========================================================

APP_DIR="/app"
cd "$APP_DIR" || exit 1

echo "🚀 Iniciando BedLink Entrypoint..."
echo "--------------------------------------------------"

# Crear archivos persistentes si no existen
[ ! -f "servers.json" ] && echo '[]' > servers.json && echo "🆕 Creado servers.json"
[ ! -f "targets.json" ] && echo '{}' > targets.json && echo "🆕 Creado targets.json"

# Nota: player_sessions.json no es requerido por main.py v0.5.1
# pero se mantiene por compatibilidad futura
[ ! -f "player_sessions.json" ] && echo '{}' > player_sessions.json && echo "🆕 Creado player_sessions.json"

echo "✅ Archivos verificados:"
ls -lh *.json 2>/dev/null || echo "⚠️ No se encontraron archivos JSON"

echo "--------------------------------------------------"
echo "🧱 Lanzando BedLink-Menu (FastAPI + UDP Proxy)..."
echo "--------------------------------------------------"

exec python3 /app/main.py
