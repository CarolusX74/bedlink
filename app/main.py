import asyncio, json, os, socket, time
from contextlib import closing
from typing import Dict, Tuple
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

# --- Ajuste importante: importar archivos locales ---
import menu_manager
import udp_selector

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
SESSION_TTL = int(os.getenv("BEDLINK_SESSION_TTL", "300"))
DEFAULT_TARGET = os.getenv("BEDLINK_DEFAULT_TARGET", "")
SERVERS_FILE = "/app/servers.json"
TARGETS_FILE = "/app/targets.json"

UDP_PORT = 19132
RAKNET_MAGIC = bytes.fromhex("00ffff00fefefefefdfdfdfd12345678")
RAKNET_UNCONNECTED_PING = 0x01
RAKNET_UNCONNECTED_PONG = 0x1C

app = FastAPI(title="BedLink-Menu v0.5.0")

# =========================
# Estado
# =========================
_global_target: str = DEFAULT_TARGET
_client_target: Dict[str, str] = {}
_sessions: Dict[Tuple[str, int], "UpstreamSession"] = {}

# =========================
# Logging
# =========================
def log(msg: str, level: str = "INFO"):
    levels = ["DEBUG","INFO","WARN","ERROR"]
    if levels.index(level) >= levels.index(LOG_LEVEL):
        print(f"[{level}] {msg}", flush=True)

# =========================
# Servidores
# =========================
def load_servers():
    try:
        with open(SERVERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"No se pudo leer servers.json: {e}", "WARN")
        return []

def get_server_by_addr(addr: str):
    for s in load_servers():
        if s["address"] == addr:
            return s
    return None

# =========================
# Persistencia
# =========================
def load_targets():
    global _global_target, _client_target
    if not os.path.exists(TARGETS_FILE): return
    try:
        with open(TARGETS_FILE,"r",encoding="utf-8") as f:
            data=json.load(f)
            _global_target=data.get("global_target",_global_target)
            _client_target=data.get("client_target",{})
            log(f"[LOAD] Targets restaurados desde {TARGETS_FILE}","INFO")
    except Exception as e:
        log(f"[WARN] No se pudo leer targets.json: {e}","WARN")

def save_targets():
    try:
        with open(TARGETS_FILE,"w",encoding="utf-8") as f:
            json.dump({"global_target":_global_target,"client_target":_client_target},f,indent=2)
    except Exception as e:
        log(f"[WARN] No se pudo guardar targets.json: {e}","WARN")

# =========================
# Utilidades
# =========================
def parse_hostport(addr:str)->Tuple[str,int]:
    if ":" in addr:
        h,p = addr.rsplit(":",1)
        return h,int(p)
    return addr,19132

def resolve_host(host:str)->str:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        if host.endswith(".lan"):
            if "core.pensa.lan" in host: return "192.168.0.200"
        raise

def get_publish_ip(remote_addr:Tuple[str,int])->str:
    if PUBLISH_IP!="auto": return PUBLISH_IP
    try:
        with closing(socket.socket(socket.AF_INET,socket.SOCK_DGRAM)) as s:
            s.connect(remote_addr)
            return s.getsockname()[0]
    except Exception:
        return "0.0.0.0"

# =========================
# Integración con menú dinámico
# =========================

def make_mcep_advertisement(remote_addr):
    ip = get_publish_ip(remote_addr)
    client_ip = remote_addr[0]

    # --- MOTD dinámico desde menu_manager ---
    motd_text = menu_manager.build_menu_motd(client_ip)

    # --- Mantener compatibilidad con protocolo ---
    return f"MCPE;{motd_text};{BEDROCK_PROTOCOL};{BEDROCK_VERSION};0;20;{ip};{PUBLISH_PORT};"


def build_unconnected_pong(pkt_time,guid,adv):
    b=adv.encode("utf-8")
    return bytes([RAKNET_UNCONNECTED_PONG])+pkt_time+guid+RAKNET_MAGIC+len(b).to_bytes(2,"big")+b

# =========================
# Selección de destino
# =========================
def get_effective_target(ip: str) -> str:
    return _client_target.get(ip, _global_target or "")

def set_global_target(a:str):
    global _global_target
    _global_target=a
    _sessions.clear(); save_targets()
    log(f"[SELECT] Target global -> {a}","INFO")
def set_client_target(ip:str,a:str):
    _client_target[ip]=a
    _sessions.clear(); save_targets()
    log(f"[SELECT] Target {ip}->{a}","INFO")
def clear_client_target(ip:str):
    _client_target.pop(ip,None); save_targets()

# =========================
# Proxy UDP
# =========================
class UpstreamSession:
    def __init__(self,loop,client_addr,target_addr,transport_out):
        self.loop=loop; self.client_addr=client_addr; self.target_addr=target_addr
        self.transport_out=transport_out; self.last_seen=time.time()
        self.up_sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.up_sock.setblocking(False)
        self.task=loop.create_task(self.reader())

    def touch(self): self.last_seen=time.time()
    def is_expired(self): return time.time()-self.last_seen>SESSION_TTL

    async def reader(self):
        log(f"[PROXY] Relay {self.client_addr}<->{self.target_addr}","INFO")
        try:
            while True:
                data=await self.loop.sock_recv(self.up_sock,65535)
                self.transport_out.sendto(data,self.client_addr)
        except asyncio.CancelledError: pass
        except Exception as e: log(f"[PROXY] recv err {e}","WARN")
        finally: self.up_sock.close()

    async def send(self,data:bytes):
        try: await self.loop.sock_sendall(self.up_sock,data)
        except Exception as e: log(f"[PROXY] send err {e}","WARN")

    def close(self):
        if not self.task.done(): self.task.cancel()
        self.up_sock.close()

class BedrockUDP(asyncio.DatagramProtocol):
    def __init__(self,loop):
        self.loop=loop; self.transport=None; self.guid=(987654321).to_bytes(8,"big")
    def connection_made(self,t): self.transport=t; log(f"UDP escuchando en {t.get_extra_info('socket').getsockname()}","INFO")
    def datagram_received(self, data, addr):
        try:
            pid = data[0]

            # --- PING INICIAL: responder con menú dinámico ---
            if pid == RAKNET_UNCONNECTED_PING and len(data) >= 25 and data[9:25] == RAKNET_MAGIC:
                motd_text = menu_manager.build_menu_motd(addr[0])
                pong = build_unconnected_pong(
                    data[1:9],
                    self.guid,
                    f"MCPE;{motd_text};{BEDROCK_PROTOCOL};{BEDROCK_VERSION};0;20;{get_publish_ip(addr)};{PUBLISH_PORT};"
                )
                self.transport.sendto(pong, addr)
                log(f"[MENU] MOTD enviado a {addr} ({motd_text})", "DEBUG")
                return

            # --- SI NO HAY TARGET SELECCIONADO: ignorar handshake ---
            client_ip = addr[0]
            target = get_effective_target(client_ip)

            if not target:
                # Responder con MOTD también para cualquier otro paquete inicial
                # así Bedrock no muestra error sino "Cargando servidor..."
                if pid in (0x00, 0x09, 0x10):
                    motd_text = menu_manager.build_menu_motd(client_ip)
                    pong = build_unconnected_pong(
                        data[1:9],
                        self.guid,
                        f"MCPE;{motd_text};{BEDROCK_PROTOCOL};{BEDROCK_VERSION};0;20;{get_publish_ip(addr)};{PUBLISH_PORT};"
                    )
                    self.transport.sendto(pong, addr)
                    log(f"[WAIT] {client_ip} sin selección → PONG menú reenviado", "DEBUG")
                else:
                    log(f"[WAIT] {client_ip} aún no seleccionó mundo → ignorando paquete tipo {hex(pid)}", "DEBUG")
                return

            # --- Conexión normal: reenviar a servidor real ---
            th, tp = parse_hostport(target)
            resolved_ip = resolve_host(th)
            taddr = (resolved_ip, tp)
            sess = _sessions.get(addr)
            if not sess:
                sess = UpstreamSession(self.loop, addr, taddr, self.transport)
                _sessions[addr] = sess
                log(f"[SESSION] Nueva sesión {addr}->{taddr}", "INFO")

            sess.touch()
            sess.up_sock.connect(taddr)
            self.loop.create_task(sess.send(data))

        except Exception as e:
            log(f"Datagram err {addr}: {e}", "WARN")



async def run_udp_server():
    loop=asyncio.get_running_loop()
    transport,_=await loop.create_datagram_endpoint(lambda:BedrockUDP(loop),local_addr=("0.0.0.0",UDP_PORT))
    try:
        while True:
            await asyncio.sleep(5)
            expired=[k for k,s in list(_sessions.items()) if s.is_expired()]
            for k in expired:
                _sessions.pop(k).close()
                log(f"[SESSION] Expirada {k}","INFO")
    finally: transport.close()

# =========================
# HTTP API + PANEL
# =========================
@app.get("/whoami")
def whoami(req:Request):
    ip=(req.headers.get("x-forwarded-for") or
        req.headers.get("cf-connecting-ip") or
        req.client.host).split(",")[0].strip()
    return {"ip":ip}

@app.get("/servers")
def api_servers(): return JSONResponse(load_servers())

@app.get("/status")
def status():
    return JSONResponse({
        "global_target":_global_target,
        "per_client":_client_target,
        "sessions":[{"client":f"{c[0]}:{c[1]}","target":f"{s.target_addr[0]}:{s.target_addr[1]}"} for c,s in _sessions.items()]
    })

@app.post("/select")
def select(target:str=Query(...)):
    th,tp=parse_hostport(target); set_global_target(f"{th}:{tp}")
    return {"ok":True,"global_target":_global_target}

@app.post("/select_for")
def select_for(client_ip:str=Query(...),target:str=Query(...)):
    th,tp=parse_hostport(target); set_client_target(client_ip,f"{th}:{tp}")
    return {"ok":True,"client_ip":client_ip,"target":f"{th}:{tp}"}

@app.post("/clear_for")
def clear_for(client_ip:str=Query(...)):
    clear_client_target(client_ip)
    return {"ok":True,"client_ip":client_ip,"cleared":True}

@app.post("/unlock")
def unlock(name: str = Query(...), password: str = Query(...)):
    servers = load_servers()
    for s in servers:
        if s["name"] == name and "password" in s:
            if s["password"] == password:
                return {"ok": True, "address": s["address"]}
            else:
                return {"ok": False, "error": "Contraseña incorrecta"}
    return {"ok": False, "error": "Servidor no encontrado o sin contraseña"}

@app.get("/panel",response_class=HTMLResponse)
def panel():
    servers=load_servers()
    cards=""
    for s in servers:
        name=s["name"]; addr=s["address"]
        desc=s.get("description","")
        has_pass="password" in s
        lock_icon="🔒 " if has_pass else "🌍 "
        cards+=f'<div class="server-card"><h4>{lock_icon}{name}</h4>'
        if desc: cards+=f'<p>{desc}</p>'
        cards+=f'<button class="server-btn" data-target="{addr}" data-name="{name}" data-pass="{str(has_pass).lower()}">Conectar</button></div>'
    html=f"""<!doctype html>
<html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>BedLink Control Panel v0.5.0</title>
<style>
body{{background:#0d1117;color:#c9d1d9;font-family:Inter,Segoe UI,Roboto,sans-serif;display:flex;flex-direction:column;align-items:center;padding:20px}}
h1{{margin:0;font-size:24px;color:#58a6ff;text-align:center}}
h3{{margin-top:24px;color:#8b949e}}
.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));width:100%;max-width:900px}}
.server-card{{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px;text-align:center}}
.server-card h4{{margin:0 0 8px 0}}
.server-card p{{margin:0 0 10px 0;color:#8b949e;font-size:14px}}
.server-btn{{background:#21262d;border:1px solid #30363d;border-radius:10px;padding:10px 14px;cursor:pointer;font-weight:600;color:#c9d1d9;transition:0.2s}}
.server-btn:hover{{border-color:#58a6ff;background:#1c232d;transform:translateY(-2px)}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:10px 0}}
.badge{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:5px 10px;font-size:13px}}
.badge.ip{{color:#3fb950;border-color:#238636}}
pre{{background:#0d1117;border:1px solid #30363d;padding:8px;border-radius:8px;font-size:12px;width:90%;max-width:900px;overflow:auto}}
.footer{{margin-top:24px;color:#8b949e;font-size:12px;text-align:center}}
</style></head>
<body>
<h1>BedLink Control Panel</h1>
<div class="badges">
  <div id="current" class="badge">Cargando target…</div>
  <div id="myip" class="badge">Detectando IP…</div>
</div>
<h3>Servidores disponibles</h3>
<div class="grid">{cards}</div>
<h3>Sesiones activas</h3><pre id="sessions">Sin sesiones</pre>
<div class="footer">BedLink-Menu v0.5.0 · Carlos-Certified™</div>
<script>
async function api(p,o){{return fetch(p,o).then(r=>r.json())}}
async function refresh(){{let s=await api('/status');document.getElementById('current').textContent='Target actual: '+s.global_target;
 let pre=document.getElementById('sessions');pre.textContent=s.sessions.length?JSON.stringify(s.sessions,null,2):'Sin sesiones';
 document.querySelectorAll('.server-btn').forEach(b=>b.classList.toggle('active',b.dataset.target===s.global_target));}}
async function detectIP(){{let r=await api('/whoami');let el=document.getElementById('myip');el.textContent='Tu IP: '+r.ip;el.classList.add('ip');window.myip=r.ip;}}
async function selectTarget(t,name,passReq){{if(passReq==='true'){{let p=prompt(`Contraseña para ${{name}}:`);if(!p)return;let r=await api(`/unlock?name=${{encodeURIComponent(name)}}&password=${{encodeURIComponent(p)}}`,{{method:'POST'}});if(!r.ok)return alert(r.error);t=r.address;}}await api('/select?target='+encodeURIComponent(t),{{method:'POST'}});refresh();}}
async function selectForMe(t){{if(!window.myip)return alert('IP no detectada');await api(`/select_for?client_ip=${{window.myip}}&target=${{t}}`,{{method:'POST'}});refresh();}}
document.querySelectorAll('.server-btn').forEach(b=>{{b.addEventListener('click',e=>{{let t=b.dataset.target;let name=b.dataset.name;let passReq=b.dataset.pass;
 e.shiftKey?selectForMe(t):selectTarget(t,name,passReq);}});b.title='Click: Global · Shift+Click: Solo este dispositivo';}});
refresh();detectIP();setInterval(refresh,2000);
</script></body></html>"""
    return HTMLResponse(html)

# =========================
# Lanzadores
# =========================
async def run_http_server():
    cfg=uvicorn.Config(app,host="0.0.0.0",port=WEB_PORT,log_level="warning")
    await uvicorn.Server(cfg).serve()

async def main_async():
    load_targets()
    udp=asyncio.create_task(run_udp_server())
    http=asyncio.create_task(run_http_server())
    await asyncio.gather(udp,http)

if __name__=="__main__":
    log("Iniciando BedLink-Menu v0.5.0 (proxy + panel + contraseñas)…","INFO")
    try: asyncio.run(main_async())
    except KeyboardInterrupt: log("Saliendo por Ctrl+C","INFO")
