(() => {
  const status = document.querySelector("[data-live-status]");
  const error = document.querySelector("[data-error]");
  const reset = document.querySelector("[data-reset]");
  const advance = document.querySelector("[data-advance]");
  const decide = document.querySelectorAll("[data-decision]");

  const initial = status?.textContent || "";
  reset?.addEventListener("click", () => {
    status.textContent = initial;
    if (error) error.style.display = "none";
  });
  advance?.addEventListener("click", () => {
    status.textContent = "Approved fixture: the exact simulated operation completed once.";
  });
  decide.forEach((button) => button.addEventListener("click", async () => {
    const credential = document.querySelector("[data-contact-token]")?.value || "";
    status.textContent = "Submitting simulated contact decision…";
    if (error) error.style.display = "none";
    try {
      const response = await fetch(location.pathname, {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CallGate-Contact-Token": credential},
        body: JSON.stringify({approved: button.dataset.decision === "approve"}),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || "Decision failed");
      status.textContent = body.status === "approved"
        ? "Approved. The simulated voice assistant may retry the exact request once."
        : "Denied. No simulated operation was authorized.";
      decide.forEach((item) => { item.disabled = true; });
    } catch (problem) {
      status.textContent = "The decision was not recorded.";
      if (error) { error.textContent = problem.message; error.style.display = "block"; }
    }
  }));
})();
