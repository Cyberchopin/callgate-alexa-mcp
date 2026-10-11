"""One-command local HTTPS demo for URL-mode elicitation."""

import argparse
import datetime
import ipaddress
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.x509.oid import NameOID

from callgate.confirmation import ConfirmationCoordinator
from callgate.contacts import ContactDirectory, SavedContact

from .server import ApprovalFlow, CapabilityGateway, add_approval_routes, create_server


def ensure_development_certificate(directory: Path):
    certificate, private_key = directory / "localhost-cert.pem", directory / "localhost-key.pem"
    if certificate.exists() and private_key.exists():
        return certificate, private_key
    directory.mkdir(parents=True, exist_ok=True)
    key = Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=7))
        .add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
        .sign(key, algorithm=None))
    private_key.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    certificate.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return certificate, private_key


def temporary_development_certificate(parent=Path(".test-tmp")):
    """Keep the demo private key in an ignored runtime directory and remove it on exit."""
    parent.mkdir(parents=True, exist_ok=True)
    return TemporaryDirectory(prefix="callgate-mcp-certificate-", dir=parent)


def build_app(replay_db: Path, approval_base_url: str, contact_token: str, *,
              subject="simulated-household", clock=None, initiator_origin="participant-device",
              contact_origin="contact-device"):
    replay_db.parent.mkdir(parents=True, exist_ok=True)
    issuer, reviewer = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    gateway = CapabilityGateway(replay_db, {"local-demo": issuer.public_key()}, clock=clock)
    contacts = ContactDirectory([SavedContact(identity="saved-family", reviewer="family",
                                               credential_origin=contact_origin)])
    coordinator = ConfirmationCoordinator("local-demo", issuer,
        {"family": reviewer.public_key()}, clock=clock or __import__('time').time,
        contacts=contacts, initiator_origin=initiator_origin)
    flow = ApprovalFlow(gateway, coordinator, {"family": reviewer},
                        {"family": contact_token}, approval_base_url=approval_base_url,
                        subject=subject, rate_clock=clock or __import__('time').monotonic)
    server = create_server(gateway, flow)
    return add_approval_routes(server.streamable_http_app(streamable_http_path="/mcp"), flow), flow


def main():
    parser = argparse.ArgumentParser(description="Run the simulated phase-2 HTTPS MCP demo")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--replay-db", type=Path, required=True)
    parser.add_argument("--contact-token", required=True,
                        help="local simulated contact credential; never put it in the URL")
    parser.add_argument("--subject", default="simulated-household")
    args = parser.parse_args()
    base_url = f"https://{args.host}:{args.port}"
    app, _ = build_app(args.replay_db, base_url, args.contact_token, subject=args.subject)
    with temporary_development_certificate() as directory:
        certificate, private_key = ensure_development_certificate(Path(directory))
        uvicorn.run(app, host=args.host, port=args.port, ssl_certfile=str(certificate),
                    ssl_keyfile=str(private_key))


if __name__ == "__main__":
    main()
