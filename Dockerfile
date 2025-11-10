# ==========================================================
# 🧱 BedLink - Dockerfile v0.6.3
# ----------------------------------------------------------
# Proxy dinámico + Panel web + Selector de mundos
# Basado en Python 3.12-slim con autoinicialización.
# ==========================================================

FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias
RUN pip install --no-cache-dir fastapi uvicorn

# Copiar el código fuente
COPY app/ /app/

# Copiar entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Exponer puertos (UDP + HTTP)
EXPOSE 19132/udp
EXPOSE 8090/tcp

# Entrypoint autoinicializable
ENTRYPOINT ["/app/entrypoint.sh"]
