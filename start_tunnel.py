import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
CLOUDFLARED = BASE / "cloudflared"

PORT = int(os.environ.get("PORT", 8000))
# Named tunnel that routes the fixed domain api.ksmart.com.es -> local API.
TUNNEL_NAME = os.environ.get("TUNNEL_NAME", "api-ksmart-tunnel")


def main():
    if not CLOUDFLARED.exists():
        print(f"cloudflared binary not found at {CLOUDFLARED}", file=sys.stderr)
        sys.exit(1)

    # Run the named tunnel (DNS CNAME api.ksmart.com.es already routed to it).
    cmd = [
        str(CLOUDFLARED),
        "tunnel",
        "run",
        "--url", f"http://localhost:{PORT}",
        TUNNEL_NAME,
    ]
    print(f"Starting cloudflared named tunnel '{TUNNEL_NAME}' -> https://api.ksmart.com.es (local port {PORT})")
    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\nShutting down tunnel")


if __name__ == "__main__":
    main()
