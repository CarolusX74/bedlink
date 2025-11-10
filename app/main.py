# ==========================================================
# 🧱 BedLink - Main (v0.5.1 Reactive FastUDP)
# ----------------------------------------------------------
# - Basado en v0.5.0 con fix de selección global
# - Relay asíncrono eficiente sin lag perceptible
# - Panel /panel funcional y robusto
# ==========================================================

import asyncio, json, os, socket, time
from contextlib import closing
from typing import Dict, Tuple
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

# =========================
# Config
# =========================
MOTD = os.getenv("BEDLINK_MOTD", "BedLink 🌍 PensaRealms")
BEDROCK_VERSION = os.getenv("BEDROCK_VERSION", "1.21.50")
BEDROCK_PROTOCOL = os.getenv("BEDROCK_PROTOCOL", "475")
PUBLISH_IP = os.getenv("BEDLINK_PUBLISH_IP", "auto")
PUBLISH_PORT = int(os.getenv("BEDLINK_PUBLISH_PORT", "19132"))
WEB_PORT = int(os.getenv("WEB_PORT", "8090"))
LOG_LEVEL = os.getenv("BEDLINK_LOG_LEVEL", "INFO").upper()
SESSION_TTL = int(os.getenv("BEDLINK_SESSION_TTL", "240"))
DEFAULT_TARGET = os.getenv("BEDLINK_DEFAULT_TARGET", "minecraft.pensa.ar:19232")
SERVERS_FILE = "/app/servers.json"
TARGETS_FILE = "/app/targets.json"

UDP_PORT = 19132
RAKNET_MAGIC = bytes.fromhex("00ffff00fefefefefdfdfdfd12345678")
RAKNET_UNCONNECTED_PING = 0x01
RAKNET_UNCONNECTED_PONG = 0x1C

app = FastAPI(title="BedLink-Menu v0.5.1")

# =========================
# Estado global
# =========================
_global_target: str = DEFAULT_TARGET
_client_target: Dict[str, str] = {}
_sessions: Dict[Tuple[str, int], "UpstreamSession"] = {}
_last_check = 0

# =========================
# Logging
# =========================
def log(msg: str, level: str = "INFO"):
    levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    if levels.index(level) >= levels.index(LOG_LEVEL):
        print(f"[{level}] {msg}", flush=True)

# =========================
# Utilidades
# =========================
def load_servers():
    try:
        with open(SERVERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"No se pudo leer servers.json: {e}", "WARN")
        return []

def load_targets():
    global _global_target, _client_target
    if not os.path.exists(TARGETS_FILE):
        return
    try:
        with open(TARGETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _global_target = data.get("global_target", _global_target)
            _client_target = data.get("client_target", {})
            log(f"[LOAD] Targets restaurados desde {TARGETS_FILE}", "INFO")
    except Exception as e:
        log(f"[WARN] No se pudo leer targets.json: {e}", "WARN")

def save_targets():
    try:
        with open(TARGETS_FILE, "w", encoding="utf-8") as f:
            json.dump({"global_target": _global_target, "client_target": _client_target}, f, indent=2)
    except Exception as e:
        log(f"[WARN] No se pudo guardar targets.json: {e}", "WARN")

def parse_hostport(addr: str) -> Tuple[str, int]:
    if ":" in addr:
        h, p = addr.rsplit(":", 1)
        return h, int(p)
    return addr, 19132

def resolve_host(host: str) -> str:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        if host.endswith(".lan"):
            if "core.pensa.lan" in host:
                return "192.168.0.200"
        raise

def get_publish_ip(remote_addr: Tuple[str, int]) -> str:
    if PUBLISH_IP != "auto":
        return PUBLISH_IP
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as s:
            s.connect(remote_addr)
            return s.getsockname()[0]
    except Exception:
        return "0.0.0.0"

def make_mcep_advertisement(remote_addr):
    ip = get_publish_ip(remote_addr)
    return f"MCPE;{MOTD};{BEDROCK_PROTOCOL};{BEDROCK_VERSION};0;20;{ip};{PUBLISH_PORT};"

def build_unconnected_pong(pkt_time, guid, adv):
    b = adv.encode("utf-8")
    return bytes([RAKNET_UNCONNECTED_PONG]) + pkt_time + guid + RAKNET_MAGIC + len(b).to_bytes(2, "big") + b

# =========================
# Selección de targets
# =========================
def get_effective_target(ip: str) -> str:
    """Devuelve el destino efectivo para una IP cliente."""
    return _client_target.get(ip, _global_target)

def set_global_target(addr: str):
    """Cambia el target global (para todos los jugadores)."""
    global _global_target
    _global_target = addr
    save_targets()
    log(f"[SELECT] Target global -> {addr}", "INFO")
    # Reiniciamos las sesiones activas
    for s in list(_sessions.values()):
        s.close()
    _sessions.clear()

def set_client_target(ip: str, addr: str):
    """Cambia el target sólo para un cliente concreto."""
    _client_target[ip] = addr
    save_targets()
    log(f"[SELECT] Target {ip} -> {addr}", "INFO")

def clear_client_target(ip: str):
    """Restablece el target del cliente al global."""
    if ip in _client_target:
        del _client_target[ip]
        save_targets()
        log(f"[SELECT] Target restaurado para {ip}", "INFO")

# =========================
# Proxy UDP
# =========================
class UpstreamSession:
    __slots__ = ("loop", "client_addr", "target_addr", "transport_out", "last_seen", "up_sock", "reader_task")

    def __init__(self, loop, client_addr, target_addr, transport_out):
        self.loop = loop
        self.client_addr = client_addr
        self.target_addr = target_addr
        self.transport_out = transport_out
        self.last_seen = time.time()
        self.up_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.up_sock.setblocking(False)
        try:
            self.up_sock.connect(target_addr)
        except Exception as e:
            log(f"[PROXY] connect err {e}", "WARN")
        self.reader_task = loop.create_task(self.reader())

    async def reader(self):
        log(f"[PROXY] Relay {self.client_addr}<->{self.target_addr}", "DEBUG")
        while True:
            try:
                data = await self.loop.sock_recv(self.up_sock, 65535)
                self.transport_out.sendto(data, self.client_addr)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log(f"[PROXY] recv err {e}", "WARN")
                break

    async def send(self, data: bytes):
        try:
            await self.loop.sock_sendall(self.up_sock, data)
        except Exception as e:
            log(f"[PROXY] send err {e}", "DEBUG")

    def touch(self):
        self.last_seen = time.time()

    def is_expired(self):
        return time.time() - self.last_seen > SESSION_TTL

    def close(self):
        if not self.reader_task.done():
            self.reader_task.cancel()
        self.up_sock.close()

# =========================
# UDP Handler
# =========================
class BedrockUDP(asyncio.DatagramProtocol):
    def __init__(self, loop):
        self.loop = loop
        self.transport = None
        self.guid = (987654321).to_bytes(8, "big")

    def connection_made(self, t):
        self.transport = t
        log(f"UDP escuchando en {t.get_extra_info('socket').getsockname()}", "INFO")

    def datagram_received(self, data, addr):
        if not data:
            return
        try:
            pid = data[0]
            if pid == RAKNET_UNCONNECTED_PING and len(data) >= 25 and data[9:25] == RAKNET_MAGIC:
                pong = build_unconnected_pong(data[1:9], self.guid, make_mcep_advertisement(addr))
                self.transport.sendto(pong, addr)
                log(f"[MENU] PONG → {addr}", "INFO")
                return

            client_ip = addr[0]
            target = _client_target.get(client_ip, _global_target)
            th, tp = parse_hostport(target)
            resolved_ip = resolve_host(th)
            taddr = (resolved_ip, tp)

            sess = _sessions.get(addr)
            if not sess:
                sess = UpstreamSession(self.loop, addr, taddr, self.transport)
                _sessions[addr] = sess
                log(f"[SESSION] Nueva {addr}->{taddr}", "INFO")

            sess.touch()
            self.loop.create_task(sess.send(data))

        except Exception as e:
            log(f"[UDP ERR] {e}", "WARN")

async def run_udp_server():
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(lambda: BedrockUDP(loop), local_addr=("0.0.0.0", UDP_PORT))
    global _last_check
    try:
        while True:
            await asyncio.sleep(1)
            now = time.time()
            if now - _last_check > 15:
                expired = [k for k, s in list(_sessions.items()) if s.is_expired()]
                for k in expired:
                    _sessions.pop(k).close()
                    log(f"[SESSION] Expirada {k}", "DEBUG")
                _last_check = now
    finally:
        transport.close()

# =========================
# API HTTP + Panel
# =========================
@app.get("/whoami")
def whoami(req: Request):
    ip = (req.headers.get("x-forwarded-for") or req.headers.get("cf-connecting-ip") or req.client.host).split(",")[0].strip()
    return {"ip": ip}

@app.get("/status")
def status():
    return JSONResponse({
        "global_target": _global_target,
        "per_client": _client_target,
        "active_sessions": len(_sessions)
    })

@app.get("/panel", response_class=HTMLResponse)
def panel():
    servers = load_servers()
    buttons = "\n".join(f'<button class="server-btn" data-target="{s["address"]}">🌍 {s["name"]}</button>' for s in servers)
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>BedLink Control Panel v0.5.1</title>
<style>
body{{background:#0d1117;color:#c9d1d9;font-family:Inter,Segoe UI,Roboto,sans-serif;text-align:center;padding:20px}}
h1{{color:#58a6ff}}
.grid{{display:grid;gap:10px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));max-width:800px;margin:auto}}
.server-btn{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:14px 16px;cursor:pointer;font-weight:600;color:#c9d1d9;transition:0.2s}}
.server-btn:hover{{border-color:#58a6ff;background:#1c232d;transform:translateY(-2px)}}
.footer{{margin-top:24px;color:#8b949e;font-size:12px}}
</style></head>
<body>
<h1>BedLink Control Panel</h1>
<div class="grid">{buttons}</div>
<div class="footer">BedLink-Menu v0.5.1 · Carlos-Certified™</div>
<script>
async function api(p,o){{return fetch(p,o).then(r=>r.json())}}
async function selectTarget(t){{await api('/select?target='+encodeURIComponent(t),{{method:'POST'}});location.reload();}}
document.querySelectorAll('.server-btn').forEach(b=>b.addEventListener('click',e=>selectTarget(b.dataset.target)));
</script></body></html>"""
    return HTMLResponse(html)

@app.post("/select")
def select(target: str = Query(...)):
    try:
        th, tp = parse_hostport(target)
        set_global_target(f"{th}:{tp}")
        return {"ok": True, "global_target": _global_target}
    except Exception as e:
        log(f"[API] Error en /select: {e}", "WARN")
        return {"ok": False, "error": str(e)}

# =========================
# Lanzadores
# =========================
async def run_http_server():
    cfg = uvicorn.Config(app, host="0.0.0.0", port=WEB_PORT, log_level="warning")
    await uvicorn.Server(cfg).serve()

async def main_async():
    load_targets()
    udp = asyncio.create_task(run_udp_server())
    http = asyncio.create_task(run_http_server())
    await asyncio.gather(udp, http)

if __name__ == "__main__":
    log("Iniciando BedLink-Menu v0.5.1 (Reactive FastUDP)…", "INFO")
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        log("Saliendo por Ctrl+C", "INFO")
