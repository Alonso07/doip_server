#!/bin/sh
set -e

# On first run, copy all built-in config files from the package to /config.
# This gives the user a complete, editable config structure:
#   /config/sovd_gateway.yaml
#   /config/entities/areas.yaml   (and components.yaml, apps.yaml)
#   /config/resources/data/...
#   /config/resources/faults/...
#   etc.
if [ ! -f /config/sovd_gateway.yaml ]; then
    echo "[SOVD] Initializing /config from package defaults..."
    python3 - <<'PYEOF'
import os, shutil, sovd_server
pkg_config = os.path.join(os.path.dirname(sovd_server.__file__), "config")
for item in os.listdir(pkg_config):
    src = os.path.join(pkg_config, item)
    dst = os.path.join("/config", item)
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)
print("[SOVD] Config initialized at /config")
PYEOF
fi

exec sovd-server \
    --gateway-config /config/sovd_gateway.yaml \
    --host 0.0.0.0 \
    --port 8080
