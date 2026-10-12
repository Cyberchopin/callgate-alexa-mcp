"""Subprocess launcher used only by MCP integration tests."""

import argparse
import http.client
import socket
import ssl
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import uvicorn
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from integrations.alexa_mcp.phase2 import build_app, ensure_development_certificate
from integrations.alexa_mcp.server import CapabilityGateway, create_server


async def health(_request):
    return PlainTextResponse("ready")


def serve(args):
    clock = (lambda: args.clock) if args.clock is not None else None
    if args.mode == "phase1":
        issuers = ({"issuer": Ed25519PublicKey.from_public_bytes(bytes.fromhex(args.public_key))}
                   if args.public_key else None)
        gateway = CapabilityGateway(args.replay_db, issuers, clock=clock)
        app = create_server(gateway).streamable_http_app(streamable_http_path="/mcp")
        ssl_options = {}
    else:
        base_url = f"https://127.0.0.1:{args.port}"
        app, _ = build_app(args.replay_db, base_url, "family-token", clock=clock)
        certificate, private_key = ensure_development_certificate(args.certificate_dir)
        ssl_options = {"ssl_certfile": str(certificate), "ssl_keyfile": str(private_key)}
    app.routes.insert(0, Route("/health", health))
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info", **ssl_options)


def _free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@contextmanager
def running_test_server(mode, replay_db, *, public_key=None, clock=None,
                        certificate_dir=None, timeout=60):
    port = _free_port()
    command = [sys.executable, "-m", "scripts.mcp_test_process", "serve", mode,
               "--port", str(port), "--replay-db", str(replay_db)]
    if public_key:
        command.extend(("--public-key", public_key))
    if clock is not None:
        command.extend(("--clock", str(clock)))
    if certificate_dir:
        command.extend(("--certificate-dir", str(certificate_dir)))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
    scheme = "https" if mode == "phase2" else "http"
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline and process.poll() is None:
            try:
                if mode == "phase2":
                    certificate = Path(certificate_dir) / "localhost-cert.pem"
                    if not certificate.exists():
                        time.sleep(0.1)
                        continue
                    context = ssl.create_default_context(cafile=str(certificate))
                    connection = http.client.HTTPSConnection(
                        "127.0.0.1", port, timeout=1, context=context)
                else:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                try:
                    connection.request("GET", "/health")
                    response = connection.getresponse()
                finally:
                    connection.close()
                if response.status == 200:
                    yield f"{scheme}://127.0.0.1:{port}"
                    return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError(_failure(process, timeout))
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        if process.returncode not in (0, None, -15, 1):
            print(f"MCP test server exit code: {process.returncode}\nstdout:\n{stdout}\nstderr:\n{stderr}")


def _failure(process, timeout):
    if process.poll() is None:
        process.terminate()
    stdout, stderr = process.communicate(timeout=10)
    return (f"MCP test server was not ready within {timeout}s; exit code={process.returncode}\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("mode", choices=("phase1", "phase2"))
    serve_parser.add_argument("--port", type=int, required=True)
    serve_parser.add_argument("--replay-db", type=Path, required=True)
    serve_parser.add_argument("--public-key")
    serve_parser.add_argument("--clock", type=float)
    serve_parser.add_argument("--certificate-dir", type=Path)
    args = parser.parse_args()
    if args.command == "serve":
        serve(args)


if __name__ == "__main__":
    main()
