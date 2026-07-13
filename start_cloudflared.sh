#!/usr/bin/env bash
set -euo pipefail

# start_cloudflared.sh
# Helper to run a Cloudflare Tunnel exposing local port 8000.
# Requirements:
#  - Install cloudflared (https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation)
#  - Authenticate once with `cloudflared login` (opens browser) to create ~/.cloudflared/cert.pem
# Usage:
#   ./start_cloudflared.sh my-tunnel-name

TUNNEL_NAME=${1:-comfyui-tunnel}
LOCAL_URL=${2:-http://localhost:8000}

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared not found in PATH. Install from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation"
  exit 2
fi

if [ ! -f "$HOME/.cloudflared/cert.pem" ]; then
  echo "No Cloudflare credentials found (~/.cloudflared/cert.pem). Run: cloudflared login"
  exit 2
fi

echo "Creating and running tunnel named: $TUNNEL_NAME -> $LOCAL_URL"

# Create a persistent tunnel (safe to run multiple times)
cloudflared tunnel create "$TUNNEL_NAME" || true

# Create a config for the tunnel
CFG_DIR="$HOME/.cloudflared"
CFG_FILE="$CFG_DIR/$TUNNEL_NAME.yml"
cat > "$CFG_FILE" <<EOF
tunnel: $(cloudflared tunnel list | awk -v name="$TUNNEL_NAME" '$0 ~ name {print $1}')
credentials-file: $CFG_DIR/$(basename $(cloudflared tunnel list | awk -v name="$TUNNEL_NAME" '$0 ~ name {print $2}'))

ingress:
  - hostname: ""
    service: "$LOCAL_URL"
  - service: http_status:404
EOF

echo "Starting tunnel (foreground). If you want a static hostname, run 'cloudflared tunnel route dns' as described in docs."
cloudflared tunnel --config "$CFG_FILE" run "$TUNNEL_NAME"
