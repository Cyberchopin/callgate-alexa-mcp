import base64
import datetime
import http.server
import ipaddress
import json
import ssl
import threading
import urllib.request
from pathlib import Path

import cryptography
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.x509.oid import NameOID


ROOT = Path(__file__).resolve().parents[1]


def _pins(path):
    return {
        name.strip().lower(): version.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "==" in line
        for name, version in [line.split("==", 1)]
    }


def test_all_manifests_pin_the_selected_cryptography_version():
    paths = (
        ROOT / "requirements-lock.txt",
        ROOT / "requirements-verification.txt",
        ROOT / "integrations/alexa_mcp/requirements.txt",
    )
    assert {_pins(path)["cryptography"] for path in paths} == {"50.0.2"}
    assert cryptography.__version__ == "50.0.2"


def test_cryptography_46_ed25519_vector_verifies_on_50():
    vector = json.loads((ROOT / "tests/fixtures/ed25519_cryptography_46_0_5.json")
                        .read_text(encoding="utf-8"))
    assert vector["generated_with"] == "46.0.5"
    public_key = Ed25519PublicKey.from_public_bytes(
        base64.b64decode(vector["public_key_b64"]))
    public_key.verify(base64.b64decode(vector["signature_b64"]),
                      base64.b64decode(vector["message_b64"]))


def test_phase2_style_self_signed_certificate_serves_https(tmp_path):
    key = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (x509.CertificateBuilder()
        .subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]), critical=False)
        .sign(key, algorithm=None))
    cert_path, key_path = tmp_path / "localhost-cert.pem", tmp_path / "localhost-key.pem"
    cert_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *_args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    server.socket = server_context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        context = ssl.create_default_context(cafile=str(cert_path))
        with urllib.request.urlopen(
                f"https://localhost:{server.server_port}/", context=context) as response:
            assert response.status == 200
            assert response.read() == b"ok"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
