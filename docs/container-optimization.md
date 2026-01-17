# Container Performance Optimization

This guide covers performance optimizations for running Agent Zero in Podman/Docker containers.

## Quick Start

Use the optimized run script:

```bash
cd docker/run
./run-optimized.sh
```

Or with custom settings:

```bash
MEMORY_LIMIT=8g CPU_LIMIT=4.0 ./run-optimized.sh
```

## Recommended Host Configuration

### Verify Optimal Settings

```bash
# Storage driver (should be 'overlay')
podman info -f '{{.Store.GraphDriverName}}'

# Runtime (should be 'crun' for best performance)
podman info --format='{{.Host.OCIRuntime.Name}}'

# Network backend (should be 'netavark' for rootful)
podman info -f '{{.Host.NetworkBackend}}'

# Cgroups version (should be 'cgroup2fs' for resource limits)
stat -fc %T /sys/fs/cgroup/
```

### Optimal Values

| Setting | Optimal Value | Why |
|---------|---------------|-----|
| Storage Driver | `overlay` | Native kernel support, fastest |
| OCI Runtime | `crun` | Written in C, faster than runc |
| Network | `netavark` (rootful) / `pasta` (rootless) | Best network performance |
| Cgroups | v2 | Required for memory/CPU limits |

## Resource Limits

### Memory

```bash
--memory=4g              # Hard limit
--memory-reservation=2g  # Soft limit (system pressure)
--memory-swap=4g         # Total memory+swap (equal to --memory disables swap)
```

### CPU

```bash
--cpus=2.0               # Limit to 2 CPU cores
--cpuset-cpus="0,1"      # Pin to specific CPUs (optional, for NUMA)
```

### Process Limits

```bash
--pids-limit=500         # Prevent fork bombs
```

## Python Performance Environment Variables

These are set in the Dockerfile but can be overridden:

| Variable | Value | Effect |
|----------|-------|--------|
| `PYTHONDONTWRITEBYTECODE` | `1` | Skip .pyc files, reduces disk I/O |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout/stderr for real-time logs |
| `MALLOC_ARENA_MAX` | `2` | Limit glibc memory arenas, reduces memory fragmentation |

## Volume Mount Options

```bash
-v /host/path:/a0:Z      # :Z for SELinux private label
--tmpfs /tmp:size=256m   # Memory-backed /tmp for faster temp files
```

### SELinux Options

| Option | Description |
|--------|-------------|
| `:Z` | Private SELinux label (single container) |
| `:z` | Shared SELinux label (multiple containers) |
| `:ro` | Read-only mount |

## Logging Configuration

Prevent unbounded log growth:

```bash
--log-driver=json-file
--log-opt max-size=50m
--log-opt max-file=3
```

## Disabling Unnecessary Services

### Tunnel API

If you have direct access to Agent Zero (public IP, VPN, local network), disable the Tunnel API to save ~1GB RAM:

```bash
# In your .env file
TUNNEL_API_ENABLED=false
```

See [tunnel.md](tunnel.md) for more details.

## Docker Compose Configuration

Full example with all optimizations:

```yaml
services:
  agent-zero:
    container_name: agent-zero
    image: agent0ai/agent-zero:latest

    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'

    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
      - MALLOC_ARENA_MAX=2

    volumes:
      - ./agent-zero:/a0:Z

    tmpfs:
      - /tmp:size=256m

    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"

    ports:
      - "50080:80"
      - "50022:22"

    pids_limit: 500
    restart: unless-stopped
```

## Monitoring Resource Usage

```bash
# Real-time stats
podman stats agent-zero

# Detailed inspection
podman inspect agent-zero --format='Memory: {{.HostConfig.Memory}}, CPUs: {{.HostConfig.NanoCpus}}'

# Logs
podman logs -f agent-zero
```

## Troubleshooting

### Resource limits not working

Ensure cgroups v2 is enabled:

```bash
stat -fc %T /sys/fs/cgroup/
# Should return: cgroup2fs
```

### Container OOM killed

Increase memory limit or check for memory leaks:

```bash
podman logs agent-zero | grep -i "killed"
dmesg | grep -i "oom"
```

### Slow volume performance

- Use native overlay storage (kernel 5.11+)
- Consider tmpfs for temporary data
- Avoid bind mounts on network filesystems
