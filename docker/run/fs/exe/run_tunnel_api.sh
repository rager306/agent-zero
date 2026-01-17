#!/bin/bash

# Check if tunnel API is disabled via environment variable
if [ "${TUNNEL_API_ENABLED:-true}" = "false" ]; then
    echo "Tunnel API disabled (TUNNEL_API_ENABLED=false)"
    # Sleep forever to keep supervisor happy (prevents restart loops)
    exec sleep infinity
fi

# Wait until run_tunnel.py exists
echo "Starting tunnel API..."

sleep 1
while [ ! -f /a0/run_tunnel.py ]; do
    echo "Waiting for /a0/run_tunnel.py to be available..."
    sleep 1
done

. "/ins/setup_venv.sh" "$@"

exec python /a0/run_tunnel.py \
    --dockerized=true \
    --port=80 \
    --tunnel_api_port=55520 \
    --host="0.0.0.0" \
    --code_exec_docker_enabled=false \
    --code_exec_ssh_enabled=true \
    # --code_exec_ssh_addr="localhost" \
    # --code_exec_ssh_port=22 \
    # --code_exec_ssh_user="root" \
    # --code_exec_ssh_pass="toor"
