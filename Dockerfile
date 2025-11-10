# ==========================================================
# 🧱 BedLink - Dockerfile v0.5.1-stable
# ----------------------------------------------------------
# Proxy dinámico + Panel web + Selector de mundos
# Basado en Python 3.12-slim con inicialización automática.
# ==========================================================

FROM python:3.12-slim

# Directorio de trabajo
WORKDIR /app

# Actualizar pip y dependencias base
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir fastapi uvicorn

# Copiar código fuente y entrypoint
COPY app/ /app/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Exponer puertos (UDP + HTTP)
EXPOSE 19132/udp
EXPOSE 8090/tcp

# Variables de entorno por defecto
ENV BEDLINK_MOTD="BedLink 🌍 PensaRealms" \
    BEDROCK_VERSION="1.21.50" \
    BEDROCK_PROTOCOL="475" \
    BEDLINK_PUBLISH_IP="auto" \
    BEDLINK_PUBLISH_PORT="19132" \
    WEB_PORT="8090" \
    BEDLINK_LOG_LEVEL="INFO" \
    BEDLINK_SESSION_TTL="240" \
    BEDLINK_DEFAULT_TARGET="minecraft.pensa.ar:19232"

# Entrypoint autoinicializable
ENTRYPOINT ["/app/entrypoint.sh"]
