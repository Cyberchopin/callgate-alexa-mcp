"""Serve fixed UI fixtures over loopback HTTP for screenshots only.

This is not the protected HTTPS approval transport.
"""
import argparse
import asyncio
from pathlib import Path

import uvicorn
from mcp.shared.exceptions import UrlElicitationRequiredError

from integrations.alexa_mcp.phase2 import build_app


class PreviewSession:
    async def send_elicit_complete(self, _elicitation_id):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    app, flow = build_app(Path(".test-tmp/ui-preview.sqlite3"),
                          f"https://127.0.0.1:{args.port}", "preview-contact")

    async def seed():
        try:
            await flow.authorize({
                "destination": "Fictional Recovery Account", "amount_cents": 5000,
                "claimed_identity": "saved-family",
            }, session_id="ui-preview", claimed_identity="saved-family",
                mcp_session=PreviewSession())
        except UrlElicitationRequiredError as required:
            return required.elicitations[0].elicitation_id
        raise RuntimeError("preview request was not created")

    request_id = asyncio.run(seed())
    print("UI PREVIEW ONLY — approval transport is HTTP and must not be used as security evidence.")
    print(f"Assistant: http://127.0.0.1:{args.port}/demo")
    print(f"Contact: http://127.0.0.1:{args.port}/approval/{request_id}")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
