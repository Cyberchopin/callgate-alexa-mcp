"""One command to launch the local simulated MCP services and live assistant page."""
import argparse
import logging
import secrets
import socket
import ssl
import threading
from pathlib import Path

import uvicorn

from integrations.alexa_mcp.assistant import create_assistant_app
from integrations.alexa_mcp.merchant import create_merchant_server
from integrations.alexa_mcp.phase2 import build_app, temporary_development_certificate, ensure_development_certificate


def available_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replay-db", type=Path, default=Path(".test-tmp/all-services.sqlite3"))
    parser.add_argument("--merchant-port", type=int, default=0)
    parser.add_argument("--gateway-port", type=int, default=0)
    parser.add_argument("--assistant-port", type=int, default=0)
    parser.add_argument("--contact-token",
                        help="local simulated contact credential; random when omitted")
    args = parser.parse_args()
    # The in-process assistant polls the gateway; per-request client logs would flood output.
    for name in ("httpx", "httpx2"):
        logging.getLogger(name).setLevel(logging.WARNING)
    args.merchant_port = args.merchant_port or available_port()
    args.gateway_port = args.gateway_port or available_port()
    args.assistant_port = args.assistant_port or available_port()
    contact_credential = args.contact_token or secrets.token_urlsafe(24)
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
        assistant_app = create_assistant_app(
            f"http://127.0.0.1:{args.merchant_port}/mcp",
            f"https://127.0.0.1:{args.gateway_port}/mcp",
            gateway_verify=ssl.create_default_context(cafile=str(certificate)))
        assistant = uvicorn.Server(uvicorn.Config(assistant_app, host="127.0.0.1",
                                                  port=args.assistant_port, log_level="warning"))
        threads = [threading.Thread(target=server.run, daemon=True)
                   for server in (merchant, assistant)]
        for thread in threads:
            thread.start()
        print(f"Merchant MCP: http://127.0.0.1:{args.merchant_port}/mcp")
        print(f"Gateway MCP: https://127.0.0.1:{args.gateway_port}/mcp")
        print(f"Live assistant: http://127.0.0.1:{args.assistant_port}/")
        print(f"Illustrative fixture page: https://127.0.0.1:{args.gateway_port}/demo")
        # Simulated local credential for the review page; it is not identity proof.
        print(f"Simulated contact credential: {contact_credential}", flush=True)
        try:
            gateway.run()
        finally:
            merchant.should_exit = True
            assistant.should_exit = True
            for thread in threads:
                thread.join(timeout=10)


if __name__ == "__main__":
    main()
