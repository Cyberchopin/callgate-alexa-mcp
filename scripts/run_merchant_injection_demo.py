"""Offline deterministic injection comparison; no network or LLM required."""
import argparse
import json
from pathlib import Path

from integrations.alexa_mcp.merchant import MerchantStore
from integrations.alexa_mcp.server import CapabilityGateway
from integrations.alexa_mcp.vulnerable_demo_agent import VulnerableDemoAgent


def run(database: Path):
    merchant = MerchantStore()
    product = merchant.get_product("lamp-injected")
    agent = VulnerableDemoAgent()
    unguarded = agent.run(product["description"])
    protected = agent.run(product["description"], gateway=CapabilityGateway(database))
    return {"mode": "offline_scripted", "simulated": True,
            "unguarded": unguarded, "callgate": protected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path,
                        default=Path(".test-tmp/merchant-injection-replay.sqlite3"))
    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    result = run(args.database)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
