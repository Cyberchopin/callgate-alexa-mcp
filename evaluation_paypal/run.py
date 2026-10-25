"""CheckoutBench-lite: reading accuracy on author-labelled chats, and order-mutation detection.

    python -m evaluation_paypal.run            # rules only
    ANTHROPIC_API_KEY=... python -m evaluation_paypal.run   # rules + model referee

Metrics
  exact       agreed total, currency and shipping all correct
  false_ready the reader produced payable terms when the chat had no clear deal  (must be 0)
  wrong_total payable terms with the wrong amount                              (must be 0)
  abstained   no payable terms where a deal existed (sent to a person; safe but costs a step)
  mutations   order changes caught out of all changes made
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

from integrations.paypal_checkout.extract import default_model_reader, read_terms
from integrations.paypal_checkout.order_check import blocking, compare, order_from_terms
from integrations.paypal_checkout.terms import parse_chat

HERE = Path(__file__).parent


def run(model_reader=None):
    data = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    rows, counts = [], {"exact": 0, "false_ready": 0, "wrong_total": 0, "abstained": 0, "deals": 0, "no_deals": 0}
    ready_terms = []
    for sc in data["scenarios"]:
        t = read_terms(parse_chat(sc["chat"]), model_reader)
        exp = sc["expect"]
        if exp == "not_ready":
            counts["no_deals"] += 1
            outcome = "false_ready" if t.ready() else "correctly_held"
            counts["false_ready"] += t.ready()
        else:
            counts["deals"] += 1
            if not t.ready():
                outcome = "abstained"
                counts["abstained"] += 1
            elif Decimal(t.total.value) != Decimal(exp["total"]) or t.currency.value != exp["currency"]:
                outcome = f"wrong_total ({t.total.value} {t.currency.value})"
                counts["wrong_total"] += 1
            elif "shipping" in exp and (t.shipping is None or Decimal(t.shipping.value) != Decimal(exp["shipping"])):
                outcome = "shipping_wrong"
            else:
                outcome = "exact"
                counts["exact"] += 1
                ready_terms.append((sc["id"], t))
        rows.append({"id": sc["id"], "lang": sc["lang"], "outcome": outcome})

    caught = total = 0
    mutation_rows = []
    for sid, t in ready_terms:
        base = order_from_terms(t, checkout_id="eval")
        base["id"] = "EVAL"
        for m in data["order_mutations"]:
            if m.get("requires") == "shipping" and t.shipping is None:
                continue
            o = copy.deepcopy(base)
            amt = o["purchase_units"][0]["amount"]
            if "set" in m:
                change = dict(m["set"])
                if change.get("currency_code") == amt["currency_code"]:
                    change["currency_code"] = "USD"      # the swap must actually change something
                amt.update(change)
            if "add_cents" in m:
                amt["value"] = str(Decimal(amt["value"]) + Decimal("0.01") * m["add_cents"])
            if "add_breakdown" in m:
                for k, v in m["add_breakdown"].items():
                    amt["breakdown"][k] = {"currency_code": amt["currency_code"], "value": v}
                    amt["value"] = str(Decimal(amt["value"]) + Decimal(v))
            if "shipping_shift" in m:
                sh = Decimal(m["shipping_shift"])
                amt["breakdown"]["shipping"]["value"] = str(Decimal(amt["breakdown"]["shipping"]["value"]) + sh)
                amt["breakdown"]["item_total"]["value"] = str(Decimal(amt["breakdown"]["item_total"]["value"]) - sh)
            got = sorted(d.field for d in blocking(compare(t, o)))
            ok = all(f in got for f in m["expect_block"]) and (got == [] if not m["expect_block"] else True)
            total += 1
            caught += ok
            if not ok:
                mutation_rows.append({"scenario": sid, "mutation": m["id"], "blocked": got})
    return {"reader": "rules+" + model_reader.label if model_reader else "rules-only",
            "counts": counts, "scenarios": rows,
            "mutations": {"correct": caught, "total": total, "misses": mutation_rows}}


if __name__ == "__main__":
    result = run(default_model_reader() if "--rules-only" not in sys.argv else None)
    out = HERE / "results.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    c = result["counts"]
    print(f"reader: {result['reader']}")
    print(f"deals: {c['deals']}  exact: {c['exact']}  abstained (sent to a person): {c['abstained']}  wrong total: {c['wrong_total']}")
    print(f"no-deal chats: {c['no_deals']}  wrongly made payable: {c['false_ready']}")
    print(f"order mutations handled: {result['mutations']['correct']}/{result['mutations']['total']}")
    for r in result["scenarios"]:
        if r["outcome"] not in ("exact", "correctly_held"):
            print("  ", r)
