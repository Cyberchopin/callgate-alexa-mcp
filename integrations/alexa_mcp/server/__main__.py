import argparse
from pathlib import Path

from .app import CapabilityGateway, create_server


def main():
    parser = argparse.ArgumentParser(description="Run the simulated CallGate MCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--replay-db", type=Path, required=True)
    args = parser.parse_args()
    args.replay_db.parent.mkdir(parents=True, exist_ok=True)
    server = create_server(CapabilityGateway(args.replay_db))
    server.run(transport="streamable-http", host=args.host, port=args.port,
               streamable_http_path="/mcp")


if __name__ == "__main__":
    main()
