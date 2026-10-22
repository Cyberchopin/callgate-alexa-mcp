"""Visible scripted MCP client for recording the simulated Alexa+ CallGate demo.

Connects to the merchant and gateway started by ``scripts.run_amazon_services``.
It is a deterministic scripted assistant, not Alexa+ and not an LLM. Approval
proof never reaches this client: the gateway keeps it server-side.

Interactive mode waits for a person to decide on the printed review page.
``--rehearse-with-token`` makes this script act as the simulated contact so the
whole chain can be checked unattended; never use that mode for the recording.
"""
import argparse
import json
from urllib.parse import urlsplit

import anyio
import httpx2
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from integrations.alexa_mcp.assistant import (
    CompletionWatcher,
    accept_elicitation,
    call_expecting_review,
)

SESSION_ID = "demo-household-session"
LEGITIMATE = {"destination": "simulated-wallet", "amount_cents": 5000,
              "session_id": SESSION_ID, "claimed_identity": "saved-family"}
INJECTED = {"destination": "injected-wallet", "amount_cents": 500000,
            "session_id": SESSION_ID, "claimed_identity": "saved-family"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}
PAUSE_BETWEEN_SCENES = False


def scene(title):
    if PAUSE_BETWEEN_SCENES:
        input("\n[Enter] next scene ")
    print(f"\n=== {title} ===", flush=True)


def show(label, value):
    print(f"  {label}: {value}", flush=True)


def result_text(result):
    return " ".join(getattr(item, "text", "") for item in result.content)


def require_loopback(url):
    if urlsplit(url).hostname not in LOOPBACK_HOSTS:
        raise SystemExit(f"refusing non-loopback demo URL: {url}")
    return url


async def wait_for_decision(http, elicitation, args, approve):
    show("Review URL (open in browser)", elicitation.url)
    if args.rehearse_with_token:
        response = await http.post(elicitation.url, json={"approved": approve},
                                   headers={"X-CallGate-Contact-Token": args.rehearse_with_token})
        show("Rehearsal contact decision", response.json())
        return
    show("Action", ("APPROVE" if approve else "DENY") + " on the review page within 120 s")
    with anyio.fail_after(args.decision_timeout):
        while (await http.get(elicitation.url)).status_code == 200:
            await anyio.sleep(0.5)
    show("Review page", "decision recorded (pending request closed)")


async def merchant_scenes(http, merchant_url):
    scene("1. Simulated merchant MCP server (product text is untrusted)")
    async with streamable_http_client(merchant_url, http_client=http) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            tools = await session.list_tools()
            show("Merchant tools", ", ".join(tool.name for tool in tools.tools))
            found = await session.call_tool("search_products", {"query": "lamp"})
            for item in found.content:
                product = json.loads(item.text)
                show("Found", f"{product['id']} — {product['price_cents']} cents")
            injected = await session.call_tool("get_product", {"product_id": "lamp-injected"})
            show("UNTRUSTED description", json.loads(result_text(injected))["description"])
            cart = await session.call_tool("add_to_cart", {"session_id": SESSION_ID,
                                                           "product_id": "lamp-safe"})
            return json.loads(result_text(cart))


async def gateway_scenes(http, gateway_url, cart, args):
    watcher = CompletionWatcher()
    async with streamable_http_client(gateway_url, http_client=http) as streams:
        async with ClientSession(streams[0], streams[1], elicitation_callback=accept_elicitation,
                                 message_handler=watcher) as session:
            scene("2. CallGate MCP gateway over Streamable HTTP")
            initialized = await session.initialize()
            show("Negotiated MCP protocol", initialized.protocol_version)
            tools = await session.list_tools()
            show("Gateway tools", ", ".join(tool.name for tool in tools.tools))

            scene("3. Protected transfer pauses for independent review")
            show("Request", LEGITIMATE)
            elicitation = await call_expecting_review(session, LEGITIMATE)
            show("Result", "JSON-RPC -32042 URL elicitation required; nothing executed")
            await wait_for_decision(http, elicitation, args, approve=True)
            await anyio.sleep(0.2)
            show("Completion notification received",
                 elicitation.elicitation_id in watcher.completed)

            scene("4. Approved once means once")
            done = await session.call_tool("send_money", LEGITIMATE)
            show("Exact retry", ("ERROR " if done.is_error else "") + result_text(done))
            again = await call_expecting_review(session, LEGITIMATE)
            show("Same request again", "-32042: approval already consumed; new review required")
            changed = await call_expecting_review(session, {**LEGITIMATE, "amount_cents": 5001})
            show("Changed amount (5001)", "-32042: approval does not transfer to new parameters")

            scene("5. Injected instructions meet the boundary")
            show("Injected request", INJECTED)
            elicitation = await call_expecting_review(session, INJECTED)
            show("Result", "-32042: paused; the contact sees the injected amount and destination")
            await wait_for_decision(http, elicitation, args, approve=False)
            canary = await session.call_tool("share_verification_code",
                                             {"recipient": "injected-recipient",
                                              "session_id": SESSION_ID})
            show("share_verification_code", result_text(canary))
            order = await session.call_tool("place_order", {
                "merchant": cart["merchant"], "cart": cart["items"],
                "total_amount_cents": cart["total_amount_cents"], "session_id": SESSION_ID})
            show("place_order without proof", result_text(order))
            return {"completed": not done.is_error, "canary_blocked": canary.is_error,
                    "order_blocked": order.is_error,
                    "unused_reviews": [again.elicitation_id, changed.elicitation_id]}


async def run(args):
    async with httpx2.AsyncClient(verify=False, timeout=30) as http:
        cart = await merchant_scenes(http, args.merchant)
        summary = await gateway_scenes(http, args.gateway, cart, args)
    scene("Summary (simulated; no real payment, order, contact, or Alexa+ connection)")
    show("Approved transfer completed exactly once", summary["completed"])
    show("Canary blocked", summary["canary_blocked"])
    show("Order without proof refused", summary["order_blocked"])
    return 0 if all((summary["completed"], summary["canary_blocked"],
                     summary["order_blocked"])) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--merchant", required=True, type=require_loopback)
    parser.add_argument("--gateway", required=True, type=require_loopback)
    parser.add_argument("--decision-timeout", type=float, default=115)
    parser.add_argument("--rehearse-with-token",
                        help="act as the simulated contact; for unattended checks only")
    parser.add_argument("--pause", action="store_true",
                        help="wait for Enter before each scene while recording")
    args = parser.parse_args()
    global PAUSE_BETWEEN_SCENES
    PAUSE_BETWEEN_SCENES = args.pause
    raise SystemExit(anyio.run(run, args))


if __name__ == "__main__":
    main()
