# 🌍 BedLink - Proxy + Menu for Minecraft Bedrock

**BedLink** is a lightweight, open-source UDP proxy and FastAPI-based control panel that allows you to host **multiple Minecraft Bedrock worlds** under one IP, switch them dynamically, and even expose local servers securely.

---

## 🚀 Features

* 🧠 **UDP Proxy** for Bedrock servers (no mods required)
* 🌐 **Dynamic world selection** via web panel or API
* 👭 **Per-client routing** — each player can connect to a different world
* 🗾 **Persistent targets** (saved between restarts)
* ⚙️ **Simple Docker setup** — ready to run anywhere
* 🔐 LAN + Internet bridging — connect to local `.lan` servers from outside!

---

## 📦 Installation

### 🐳 Using Docker Compose

```bash
git clone https://github.com/pensados/bedlink.git
cd bedlink
docker compose up -d
```

By default, the panel will be available at:
🔗 **[http://localhost:8090/panel](http://localhost:8090/panel)**

and the Bedrock discovery/proxy on:
🔗 **UDP port 19132**

---

## 🧪 Environment Variables

| Variable                 | Description                                              | Default                    |
| ------------------------ | -------------------------------------------------------- | -------------------------- |
| `BEDLINK_MOTD`           | MOTD shown to clients                                    | `BedLink 🌍`               |
| `BEDROCK_VERSION`        | Bedrock version string                                   | `1.21.50`                  |
| `BEDROCK_PROTOCOL`       | Protocol number                                          | `475`                      |
| `BEDLINK_PUBLISH_IP`     | IP to advertise in server list (`auto` uses outbound IP) | `auto`                     |
| `BEDLINK_PUBLISH_PORT`   | Port to advertise                                        | `19132`                    |
| `WEB_PORT`               | HTTP control panel port                                  | `8090`                     |
| `BEDLINK_LOG_LEVEL`      | Logging level (`DEBUG`, `INFO`, `WARN`, `ERROR`)         | `INFO`                     |
| `BEDLINK_DEFAULT_TARGET` | Default server destination                               | `minecraft.pensa.ar:19232` |
| `BEDLINK_SESSION_TTL`    | Time (seconds) to keep inactive sessions                 | `300`                      |

---

## 📜 Example `servers.json`

```json
[
  {"name": "PensaRealms - Core", "address": "core.pensa.lan:19233"},
  {"name": "PensaRealms - Main", "address": "minecraft.pensa.ar:19232"},
  {"name": "PensaRealms - Realm", "address": "realm.pensa.ar:19233"}
]
```

---

## 🦯 API Endpoints

| Endpoint                         | Method | Description                        |
| -------------------------------- | ------ | ---------------------------------- |
| `/panel`                         | GET    | Web control panel                  |
| `/servers`                       | GET    | List available servers             |
| `/select?target=`                | POST   | Set global target                  |
| `/select_for?client_ip=&target=` | POST   | Set per-client target              |
| `/clear_for?client_ip=`          | POST   | Remove per-client target           |
| `/status`                        | GET    | Current status (targets, sessions) |

---

## 🐋 Docker Hub Image

Once published:

```bash
docker run -d \
  -p 19132:19132/udp \
  -p 8090:8090 \
  -v ./servers.json:/app/servers.json:ro \
  --name bedlink \
  pensa/bedlink:latest
```

---

## 🧠 Roadmap

* ✅ Per-client target selection
* ✅ Persistent state
* ⏳ In-game menu for world selection
* 🔒 Password-protected servers
* 📊 Real-time panel stats (players, bytes, TTL)
* 🌍 Optional Cloudflare Tunnel integration

---

## 🧪 License

MIT — do whatever you like, just credit the project.
(c) 2025 **Carlos Pensa** — [pensa.ar](https://pensa.ar)
