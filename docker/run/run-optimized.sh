#!/bin/bash
#
# Optimized Podman run script for Agent Zero
# Uses crun runtime, resource limits, and performance tuning
#

set -e

CONTAINER_NAME="${CONTAINER_NAME:-agent-zero}"
IMAGE="${IMAGE:-agent0ai/agent-zero:latest}"
A0_DATA="${A0_DATA:-./agent-zero}"
ENV_FILE="${ENV_FILE:-../../.env}"
WEB_PORT="${WEB_PORT:-50080}"
SSH_PORT="${SSH_PORT:-50022}"

# Memory limits (adjust based on your system)
MEMORY_LIMIT="${MEMORY_LIMIT:-4g}"
MEMORY_RESERVATION="${MEMORY_RESERVATION:-2g}"
CPU_LIMIT="${CPU_LIMIT:-2.0}"

# Stop existing container if running
if podman ps -q -f name="^${CONTAINER_NAME}$" | grep -q .; then
    echo "Stopping existing container ${CONTAINER_NAME}..."
    podman stop "${CONTAINER_NAME}"
fi

# Remove existing container if exists
if podman ps -aq -f name="^${CONTAINER_NAME}$" | grep -q .; then
    echo "Removing existing container ${CONTAINER_NAME}..."
    podman rm "${CONTAINER_NAME}"
fi

echo "Starting ${CONTAINER_NAME} with optimizations..."

podman run -d \
    --name "${CONTAINER_NAME}" \
    --runtime=/usr/bin/crun \
    \
    --memory="${MEMORY_LIMIT}" \
    --memory-reservation="${MEMORY_RESERVATION}" \
    --memory-swap="${MEMORY_LIMIT}" \
    --cpus="${CPU_LIMIT}" \
    --pids-limit=500 \
    \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONUNBUFFERED=1 \
    -e MALLOC_ARENA_MAX=2 \
    -e TUNNEL_API_ENABLED="${TUNNEL_API_ENABLED:-true}" \
    \
    -v "${A0_DATA}:/a0:Z" \
    -v "${ENV_FILE}:/a0/.env:Z" \
    --tmpfs /tmp:size=256m \
    \
    --log-driver=json-file \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    \
    -p "${WEB_PORT}:80" \
    -p "${SSH_PORT}:22" \
    \
    --restart=unless-stopped \
    \
    "${IMAGE}"

echo ""
echo "Container ${CONTAINER_NAME} started successfully!"
echo "  Web UI: http://localhost:${WEB_PORT}"
echo "  SSH:    ssh -p ${SSH_PORT} root@localhost"
echo ""
echo "Resource limits:"
echo "  Memory: ${MEMORY_LIMIT} (reservation: ${MEMORY_RESERVATION})"
echo "  CPUs:   ${CPU_LIMIT}"
echo ""
echo "To view logs:  podman logs -f ${CONTAINER_NAME}"
echo "To stop:       podman stop ${CONTAINER_NAME}"
