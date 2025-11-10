# 🌍 BedLink v0.6.3 – Proxy + Dynamic Menu for Minecraft Bedrock

**BedLink** is a lightweight, open-source **UDP proxy** and **FastAPI-based control panel** that lets you host **multiple Minecraft Bedrock worlds** under one IP.
Players can switch worlds dynamically — via the web panel, or even in-game (experimental).

---

## 🚀 Features

* 🧠 **UDP Proxy** for Bedrock servers (no mods required)
* 🌐 **Dynamic world selection** via web panel or API
* 👭 **Per-client routing** — each player can connect to a different world
* 🗄️ **Persistent targets** and player sessions (saved between restarts)
* 🐳 **Autonomous Docker image** — runs out-of-the-box
* 🔐 Works on LAN and Internet, bridging `.lan` servers externally
* 🧩 Optional **password-protected servers** and in-game MOTD menu

---

## ⚙️ Quick Start (Docker Compose)

```bash
git clone https://github.com/pensados/bedlink.git
cd bedlink
docker compose up -d
```

Then open the control panel:
🔗 **[http://localhost:8090/panel](http://localhost:8090/panel)**

The Bedrock server list will show your proxy at:
🛰️ **UDP port 19132**

---

## 🧪 Environment Variables

| Variable                 | Description                                            | Default                    |      |        |        |
| ------------------------ | ------------------------------------------------------ | -------------------------- | ---- | ------ | ------ |
| `BEDLINK_MOTD`           | MOTD shown to clients                                  | `BedLink 🌍 PensaRealms`   |      |        |        |
| `BEDROCK_VERSION`        | Bedrock version string                                 | `1.21.50`                  |      |        |        |
| `BEDROCK_PROTOCOL`       | Protocol number                                        | `475`                      |      |        |        |
| `BEDLINK_PUBLISH_IP`     | IP advertised in the server list (`auto` = autodetect) | `auto`                     |      |        |        |
| `BEDLINK_PUBLISH_PORT`   | Port advertised in the MOTD                            | `19132`                    |      |        |        |
| `WEB_PORT`               | HTTP panel port                                        | `8090`                     |      |        |        |
| `BEDLINK_LOG_LEVEL`      | `DEBUG                                                 | INFO                       | WARN | ERROR` | `INFO` |
| `BEDLINK_DEFAULT_TARGET` | Default world / server                                 | `minecraft.pensa.ar:19232` |      |        |        |
| `BEDLINK_SESSION_TTL`    | Idle session lifetime (s)                              | `300`                      |      |        |        |

---

## 📜 Example `servers.json`

```json
[
  {"name": "PensaRealms – Core",  "address": "core.pensa.lan:19233"},
  {"name": "PensaRealms – Main",  "address": "minecraft.pensa.ar:19232"},
  {"name": "PensaRealms – Realm", "address": "realm.pensa.ar:19233"}
]
```

---

## 🧩 API Endpoints

| Endpoint                         | Method | Description                      |
| -------------------------------- | ------ | -------------------------------- |
| `/panel`                         | GET    | Web control panel                |
| `/servers`                       | GET    | List available servers           |
| `/status`                        | GET    | Current targets + sessions       |
| `/select?target=`                | POST   | Set global target                |
| `/select_for?client_ip=&target=` | POST   | Set per-client target            |
| `/clear_for?client_ip=`          | POST   | Remove per-client target         |
| `/unlock?name=&password=`        | POST   | Unlock password-protected server |

---

## 🐋 Docker Image (stand-alone)

After pushing to Docker Hub:

```bash
docker run -d \
  -p 19132:19132/udp \
  -p 8090:8090 \
  -v ./servers.json:/app/servers.json:ro \
  -v ./targets.json:/app/targets.json \
  -v ./player_sessions.json:/app/player_sessions.json \
  --name bedlink \
  carolusx74/bedlink:latest
```

All required files are **auto-created** on startup via `entrypoint.sh`.

---

## 🧠 Roadmap

* ✅ Per-client routing and persistence
* ✅ Dynamic control panel
* ✅ Auto-initialization (`entrypoint.sh`)
* ⏳ In-game world-selection menu
* 🔒 Password-protected worlds
* 📊 Real-time metrics panel
* 🌍 Optional Cloudflare Tunnel support

---

## 🗾 License

MIT License — free for personal or commercial use.
(c) 2025 **Carlos Pensa** · [https://pensa.ar](https://pensa.ar)
