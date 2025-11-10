# 🧱 BedLink – Changelog

## v0.6.3 – Autonomous Image Release
**Date:** 2025-11-09  

### ✨ New
- Added **`entrypoint.sh`** with auto-initialization of `servers.json`, `targets.json`, and `player_sessions.json`.
- Docker image now runs standalone — ready for `docker run` or `compose up` without setup.
- Improved logging and startup messages (PensaInfra style).
- Clean separation between **FastAPI panel** and **UDP proxy**.

### 🧩 Technical
- Updated `Dockerfile` to use `ENTRYPOINT` → `/app/entrypoint.sh`.
- Optimized Docker image (base: python 3.12-slim < 150 MB).
- Fixed warnings when `/app/targets.json` was a directory.
- Unified JSON persistency handling for sessions and targets.

### 🧠 Next
- In-game menu integration (`/menu_manager.py v0.6.1` foundation).
- Docker Hub build pipeline and auto-publish workflow.