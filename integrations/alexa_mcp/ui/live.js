(() => {
  const list = document.querySelector("[data-conversation]");
  const form = document.querySelector("[data-ask]");
  const input = document.querySelector("[data-utterance]");
  const speak = document.querySelector("[data-speak]");
  const controls = document.querySelectorAll("[data-scenario], [data-ask] button");
  const labels = {assistant: "Assistant", done: "Completed (simulated)", denied: "Denied",
                  consumed: "CallGate", blocked: "CallGate", error: "Stopped", system: "MCP connection"};
  let waiting = null;

  const dollars = (cents) => "$" + (cents / 100).toLocaleString("en-US", {minimumFractionDigits: 2});
  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const say = (text) => {
    if (speak?.checked && "speechSynthesis" in window) {
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
    }
  };
  const route = (text) => {
    const words = text.toLowerCase();
    if (/(send|transfer|pay|money|dollar)/.test(words)) return "transfer";
    if (/(lamp|find|shop|buy|search)/.test(words)) return "shopping";
    return null;
  };

  function pauseCard(item, event) {
    item.append(node("span", "who", "CallGate"), node("p", "headline", event.text));
    const facts = node("dl");
    [["Amount", dollars(event.amount_cents)], ["Destination", event.destination],
     ["Reviewer", "Saved contact for " + event.identity]].forEach(([term, value]) => {
      facts.append(node("dt", "", term), node("dd", "", value));
    });
    const link = node("a", "review-link", "Open review on the contact's device");
    link.href = event.review_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    waiting = node("p", "muted", "Waiting for the contact's decision…");
    item.append(facts, link, waiting);
    say(event.text + " Waiting for your saved contact.");
  }

  function render(event) {
    const item = node("li", "turn turn-" + event.kind);
    if (waiting && event.kind !== "pause") {
      waiting.textContent = "Decision received.";
      waiting = null;
    }
    if (event.kind === "user") {
      item.append(node("span", "who", "You"), node("p", "", "“" + event.text + "”"));
    } else if (event.kind === "products") {
      item.append(node("span", "who", "Assistant"), node("p", "", event.text));
      const row = node("div", "products");
      event.items.forEach((product) => {
        const card = node("article", "product");
        card.append(node("strong", "", product.name), node("span", "price", dollars(product.price_cents)),
                    node("span", "pid", product.id));
        row.append(card);
      });
      item.append(row);
      say(event.text);
    } else if (event.kind === "untrusted") {
      item.append(node("span", "who", "Untrusted product text"), node("blockquote", "", event.text));
    } else if (event.kind === "pause") {
      pauseCard(item, event);
    } else {
      item.append(node("span", "who", labels[event.kind] || "CallGate"), node("p", "", event.text));
      if (event.kind !== "system") say(event.text);
    }
    list.append(item);
    item.scrollIntoView({behavior: "smooth", block: "nearest"});
  }

  const setBusy = (busy) => controls.forEach((control) => { control.disabled = busy; });
  const pause = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function run(scenario) {
    list.replaceChildren();
    waiting = null;
    setBusy(true);
    try {
      const response = await fetch("/api/run", {method: "POST",
        headers: {"Content-Type": "application/json"}, body: JSON.stringify({scenario})});
      const started = await response.json();
      if (!response.ok) throw new Error(started.error || "Could not start");
      let shown = 0;
      let state;
      do {
        await pause(400);
        state = await (await fetch("/api/runs/" + started.run_id)).json();
        state.events.slice(shown).forEach(render);
        shown = state.events.length;
      } while (!state.finished);
    } catch (problem) {
      render({kind: "error", text: problem.message});
    } finally {
      setBusy(false);
    }
  }

  document.querySelectorAll("[data-scenario]").forEach((button) => {
    button.addEventListener("click", () => run(button.dataset.scenario));
  });
  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const scenario = route(input.value);
    if (scenario) {
      run(scenario);
    } else {
      list.replaceChildren();
      render({kind: "assistant", text: "In this demo I can send money or find a reading lamp."});
    }
  });
})();
