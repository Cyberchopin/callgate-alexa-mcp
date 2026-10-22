"""The approval notification can arrive after the review page has already closed."""
import anyio

from integrations.alexa_mcp.assistant import CompletionWatcher


class Notification:
    def __init__(self, elicitation_id):
        self.params = type("Params", (), {"elicitation_id": elicitation_id})()


Notification.__name__ = "ElicitCompleteNotification"


def test_waits_for_a_late_completion_notification():
    async def scenario():
        watcher = CompletionWatcher()

        async def deliver_late():
            await anyio.sleep(0.5)
            await watcher(Notification("late"))

        async with anyio.create_task_group() as group:
            group.start_soon(deliver_late)
            return await watcher.wait_for("late", timeout=3)

    assert anyio.run(scenario) is True


def test_reports_no_completion_after_the_grace_period():
    async def scenario():
        return await CompletionWatcher().wait_for("never", timeout=0.3)

    assert anyio.run(scenario) is False
