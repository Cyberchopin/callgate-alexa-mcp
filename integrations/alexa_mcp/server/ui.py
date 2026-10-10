"""No-build, local-only UI assets for the simulated phase-2 experience."""
from pathlib import Path

from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from .app import operation_resource


ASSET_ROOT = Path(__file__).resolve().parents[1] / "ui"


def _asset(name: str) -> str:
    return (ASSET_ROOT / name).read_text(encoding="utf-8")


def security_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'",
    }


async def assistant_page(_request):
    return HTMLResponse(_asset("assistant.html"), headers=security_headers())


async def stylesheet(_request):
    return Response(_asset("style.css"), media_type="text/css",
                    headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


async def javascript(_request):
    return Response(_asset("demo.js"), media_type="application/javascript",
                    headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


def render_contact_page(item) -> str:
    operation = item.arguments
    values = {
        "{{AMOUNT}}": str(int(operation["amount_cents"])),
        "{{DESTINATION}}": __import__("html").escape(operation["destination"]),
        "{{IDENTITY}}": __import__("html").escape(item.request.claimed_identity or ""),
        "{{ISSUED_AT}}": str(item.request.issued_at),
        "{{EXPIRES_AT}}": str(item.request.expires_at),
        "{{REQUEST_ID}}": __import__("html").escape(item.request.request_id),
        "{{PARAMETER_HASH}}": operation_resource("send_money", operation),
    }
    page = _asset("contact.html")
    for marker, value in values.items():
        page = page.replace(marker, value)
    return page


def ui_routes():
    return [
        Route("/demo", assistant_page, methods=["GET"]),
        Route("/ui/style.css", stylesheet, methods=["GET"]),
        Route("/ui/demo.js", javascript, methods=["GET"]),
    ]
