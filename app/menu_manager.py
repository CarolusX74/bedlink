#- ==========================================================
#- 🧱 Bedlink - Menu Manager (Dynamic MOTD v0.6.2)
#- ----------------------------------------------------------
#- Genera el texto que Minecraft Bedrock muestra en la lista
#- de servidores, usando servers.json como base.
#- Muestra SIEMPRE el menú rotativo in-game, sin autoselección.
#- ==========================================================

import json
import os
import socket
import time
from typing import List



SERVERS_FILE = "/app/servers.json"

_last_index = 0
_last_time = 0
ROTATE_INTERVAL = 3  # segundos entre cada rotación visible


#- ==========================================================
#- Utilidades
#- ==========================================================
def load_servers() -> List[dict]:
    try:
        with open(SERVERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] No se pudo leer servers.json: {e}")
        return []


def get_local_ip() -> str:
    """Obtiene la IP LAN de la interfaz principal."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def build_menu_motd(client_ip: str) -> str:
    """
    Muestra en el MOTD la IP real o dominio del panel BedLink.
    """
    panel_port = os.getenv("WEB_PORT", "8090")
    publish_ip = os.getenv("BEDLINK_PUBLISH_IP", "auto")

    # Detectar IP de publicación
    if publish_ip == "auto":
        ip = get_local_ip()
    else:
        ip = publish_ip

    # Permitir dominio si se usa uno (por ejemplo minecraft.pensa.ar)
    host = os.getenv("BEDLINK_DOMAIN", ip)
    url = f"{host}:{panel_port}/panel"

    # Mensaje final visible en la lista del juego
    return f"See → {url}"
