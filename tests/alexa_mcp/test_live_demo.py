"""End-to-end check of the recorded demo path: launcher plus visible MCP client."""
import socket
import ssl
import subprocess
import sys
import time

import pytest

from scripts.amazon_live_demo import require_loopback


def _free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _wait_for_https(port, timeout=60):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1) as raw:
                with context.wrap_socket(raw, server_hostname="127.0.0.1"):
                    return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("gateway did not start")


def test_launcher_and_client_complete_the_recorded_demo(tmp_path):
    merchant_port, gateway_port = _free_port(), _free_port()
    server = subprocess.Popen([sys.executable, "-m", "scripts.run_amazon_services",
        "--replay-db", str(tmp_path / "replay.sqlite3"), "--merchant-port", str(merchant_port),
        "--gateway-port", str(gateway_port), "--contact-token", "rehearsal-token"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        _wait_for_https(gateway_port)
        client = subprocess.run([sys.executable, "-m", "scripts.amazon_live_demo",
            "--merchant", f"http://127.0.0.1:{merchant_port}/mcp",
            "--gateway", f"https://127.0.0.1:{gateway_port}/mcp",
            "--rehearse-with-token", "rehearsal-token"],
            capture_output=True, text=True, timeout=120)
    finally:
        server.terminate()
        launcher_output, _ = server.communicate(timeout=10)
    assert "Simulated contact credential: rehearsal-token" in launcher_output
    assert client.returncode == 0, client.stdout + client.stderr
    for marker in ("Negotiated MCP protocol: 2025-11-25", "Completion notification received: True",
                   '"real_action_executed": false', "approval already consumed",
                   "403 BLOCKED: canary tool is permanently disabled",
                   "403 POLICY_PROOF_REQUIRED"):
        assert marker in client.stdout


def test_client_refuses_non_loopback_urls():
    with pytest.raises(SystemExit):
        require_loopback("https://example.com/mcp")
