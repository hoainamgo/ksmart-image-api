#!/usr/bin/env bash
# start_server.sh - Khoi dong server + tunnel ksmart tren Linux (studio)
# Chay: bash start_server.sh   hoac   ./start_server.sh
set -euo pipefail
cd "$(dirname "$0")"

BASE="https://api.ksmart.com.es"
KEY="ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"
export API_KEY="$KEY"

echo "==> Khoi dong API server (server.py) tren port 8000..."
setsid python server.py > api_server.log 2>&1 &
echo "    server pid: $!"

sleep 4
echo "    local GUI : http://127.0.0.1:8000/  -> $(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/)"
echo "    local /queue (key): $(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:8000/queue?api_key=$KEY")"

echo "==> Khoi dong Cloudflare tunnel -> $BASE ..."
setsid python start_tunnel.py > tunnel.log 2>&1 &
echo "    tunnel pid: $!"

sleep 6
echo "    public /queue (key): $(curl -s -o /dev/null -w '%{http_code}' "$BASE/queue?api_key=$KEY")"
echo "Done. Xem log: api_server.log, tunnel.log"
