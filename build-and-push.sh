#!/bin/bash
# ==========================================================
# 🧱 BedLink - Build & Push Script (v3 - PensaInfra Release)
# ----------------------------------------------------------
# Compila, etiqueta, publica en Docker Hub y crea git tag.
# Ideal para flujos de release controlados de PensaInfra™.
# ==========================================================

set -e

# --- 🎨 Colores ---
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
BLUE="\033[1;34m"
GRAY="\033[0;37m"
RESET="\033[0m"

# --- 🧱 Configuración ---
IMAGE_NAME="carolusx74/bedlink"
DEFAULT_VERSION="v0.6.3"
VERSION="${1:-$DEFAULT_VERSION}"
BUILD_DATE=$(date '+%Y-%m-%d %H:%M:%S')
START_TIME=$(date +%s)
RELEASE_LOG="releases.log"

echo -e "${BLUE}🚀 Iniciando build & push de BedLink ${YELLOW}${VERSION}${RESET}"
echo -e "📅 Fecha: ${BUILD_DATE}"
echo "--------------------------------------------------"

# --- 🔐 Verificar login ---
if ! docker info | grep -q "Username:"; then
  echo -e "${RED}⚠️  No estás logueado en Docker Hub.${RESET}"
  echo "Ejecuta: docker login"
  exit 1
fi

# --- 🔍 Verificar si la versión ya existe ---
if curl -s "https://hub.docker.com/v2/repositories/${IMAGE_NAME}/tags/${VERSION}" | grep -q '"name"'; then
  echo -e "${YELLOW}⚠️  La versión ${VERSION} ya existe en Docker Hub.${RESET}"
  read -p "¿Deseas continuar y sobreescribirla? (y/N): " CONFIRM
  [[ "${CONFIRM,,}" != "y" ]] && echo "❌ Operación cancelada." && exit 0
fi

# --- 🧱 Build de imagen ---
echo -e "${BLUE}🧱 Construyendo imagen...${RESET}"
docker build -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${VERSION} .

# --- 📦 Mostrar tamaño final ---
echo -e "${GRAY}📦 Tamaño de la imagen:${RESET}"
docker images ${IMAGE_NAME} --format "{{.Repository}}:{{.Tag}}  ->  {{.Size}}"

# --- ⬆️ Subir a Docker Hub ---
echo -e "${BLUE}⬆️  Subiendo a Docker Hub...${RESET}"
docker push ${IMAGE_NAME}:latest
docker push ${IMAGE_NAME}:${VERSION}

# --- 🧹 Limpieza ---
echo -e "${GRAY}🧹 Limpiando imágenes dangling...${RESET}"
docker image prune -f > /dev/null || true

# --- 🧾 Registrar en releases.log ---
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' ${IMAGE_NAME}:${VERSION} 2>/dev/null || echo "no-digest")
echo "${BUILD_DATE} | ${VERSION} | ${DIGEST}" >> "${RELEASE_LOG}"

# --- 🏷️ Crear tag Git (si es repo) ---
if [ -d .git ]; then
  if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  El tag ${VERSION} ya existe en Git.${RESET}"
  else
    echo -e "${BLUE}🏷️  Creando tag Git: ${VERSION}${RESET}"
    git tag -a "$VERSION" -m "BedLink ${VERSION} - ${BUILD_DATE}"
    git push origin "$VERSION" || echo -e "${YELLOW}⚠️  No se pudo subir el tag al remoto.${RESET}"
  fi
else
  echo -e "${GRAY}ℹ️  No es un repositorio Git, omitiendo tag.${RESET}"
fi

# --- ✅ Resumen final ---
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo "--------------------------------------------------"
echo -e "${GREEN}✅ BedLink ${VERSION} publicado correctamente!${RESET}"
echo -e "🕒 Tiempo total: ${ELAPSED}s"
echo -e "📦 Imagen Docker: ${BLUE}https://hub.docker.com/r/${IMAGE_NAME}${RESET}"
echo -e "🏷️  Git Tag: ${YELLOW}${VERSION}${RESET}"
echo -e "🧾 Log registrado en: ${GRAY}${RELEASE_LOG}${RESET}"
echo "--------------------------------------------------"
