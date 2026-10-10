"""One command to launch both local simulated MCP services."""
import argparse
import secrets
import threading
from pathlib import Path

import uvicorn

from integrations.alexa_mcp.merchant import create_merchant_server
from integrations.alexa_mcp.phase2 import build_app, temporary_development_certificate, ensure_development_certificate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-db", type=Path, default=Path(".test-tmp/all-services.sqlite3"))
    parser.add_argument("--merchant-port", type=int, default=8001)
    parser.add_argument("--gateway-port", type=int, default=8443)
    args = parser.parse_args()
    contact_credential = secrets.token_urlsafe(24)
    merchant_app = create_merchant_server().streamable_http_app(streamable_http_path="/mcp")
    gateway_app, _ = build_app(args.replay_db, f"https://127.0.0.1:{args.gateway_port}",
                               contact_credential)
    merchant = uvicorn.Server(uvicorn.Config(merchant_app, host="127.0.0.1",
                                             port=args.merchant_port, log_level="warning"))
    with temporary_development_certificate() as directory:
        certificate, private_key = ensure_development_certificate(Path(directory))
        gateway = uvicorn.Server(uvicorn.Config(gateway_app, host="127.0.0.1",
            port=args.gateway_port, log_level="warning", ssl_certfile=str(certificate),
            ssl_keyfile=str(private_key)))
        thread = threading.Thread(target=merchant.run, daemon=True)
        thread.start()
        try:
            gateway.run()
        finally:
            merchant.should_exit = True
            thread.join(timeout=10)


if __name__ == "__main__":
    main()
