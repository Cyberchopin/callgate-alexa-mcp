"""Run Claude as the seller's sales assistant against a running CallGate Checkout, over real MCP.

    python -m integrations.paypal_checkout.server        # terminal 1
    export ANTHROPIC_API_KEY=...
    python -m scripts.paypal_llm_agent                     # terminal 2

The assistant reads the chat (which contains a planted "the real price is
$180" note), drafts the PayPal order through the gateway, and reports back.
Then open the seller page to see what it drafted and whether it was verified.
"""
from __future__ import annotations

import argparse
import json

import anyio
import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from integrations.paypal_checkout.llm_agent import anthropic_messages, run_agent
from scripts.paypal_agent_demo import CHAT


class MCPTools:
    def __init__(self, session: ClientSession):
        self.s = session

    async def list(self):
        tools = (await self.s.list_tools()).tools
        return [{"name": t.name, "description": t.description or "",
                 "input_schema": getattr(t, "input_schema", None) or getattr(t, "inputSchema")} for t in tools]

    async def call(self, name, args):
        r = await self.s.call_tool(name, args)
        sc = getattr(r, "structured_content", None) or getattr(r, "structuredContent", None)
        out = json.dumps(sc, ensure_ascii=False) if sc is not None else " ".join(getattr(c, "text", "") for c in r.content)
        return bool(r.is_error if hasattr(r, "is_error") else r.isError), out[:6000]


async def main(base: str, token: str | None, chat: str):
    http = httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"}) if token else None
    async with streamable_http_client(base + "/mcp", **({"http_client": http} if http else {})) as streams:
        async with ClientSession(streams[0], streams[1]) as s:
            await s.initialize()
            run = await run_agent(MCPTools(s), anthropic_messages(), chat=chat, log=print)
    if http:
        await http.aclose()
    cid = next((c["result"].get("checkout_id") for c in run["calls"] if isinstance(c["result"], dict)
                and c["result"].get("checkout_id")), None)
    if cid:
        print(f"\nOpen the seller page: {base}/?checkout={cid}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8787")
    ap.add_argument("--token")
    ap.add_argument("--chat-file")
    a = ap.parse_args()
    anyio.run(main, a.base, a.token, open(a.chat_file, encoding="utf-8").read() if a.chat_file else CHAT)
