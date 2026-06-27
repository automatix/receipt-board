"""SSE endpoint tests: the /events stream and its frame generator (v1.3.0)."""

from __future__ import annotations

import asyncio

from receipt_board.api.routers import event_stream, events, privileged_router, public_router
from receipt_board.core.events import EventBus

# -- frame generator (deterministic, no HTTP) ---------------------------------


def test_event_stream_yields_ready_then_change():
    async def never() -> bool:
        return False

    async def scenario() -> tuple[str, str]:
        bus = EventBus()
        gen = event_stream(bus, never, keepalive=5)
        ready = await gen.__anext__()
        bus.publish()
        change = await gen.__anext__()
        await gen.aclose()
        return ready, change

    ready, change = asyncio.run(scenario())
    assert "event: ready" in ready and '"revision": 0' in ready
    assert "retry: 3000" in ready
    assert "event: change" in change and '"revision": 1' in change


def test_event_stream_emits_keepalive_when_idle():
    async def never() -> bool:
        return False

    async def scenario() -> str:
        bus = EventBus()
        gen = event_stream(bus, never, keepalive=0.01)
        await gen.__anext__()  # ready
        frame = await gen.__anext__()  # no publish -> times out -> keepalive
        await gen.aclose()
        return frame

    assert asyncio.run(scenario()).startswith(": keepalive")


def test_event_stream_stops_on_disconnect():
    async def disconnected() -> bool:
        return True

    async def scenario() -> list[str]:
        bus = EventBus()
        frames = [frame async for frame in event_stream(bus, disconnected, keepalive=5)]
        return frames

    # Only the initial ready frame is sent, then the loop sees the disconnect and stops.
    frames = asyncio.run(scenario())
    assert len(frames) == 1 and "event: ready" in frames[0]


# -- HTTP endpoint ------------------------------------------------------------
#
# The stream is intentionally endless, which deadlocks TestClient teardown; the frame
# logic above is covered deterministically. Here we assert the response wiring (content
# type / headers) and that the route is public (no token dependency) without consuming it.


class _FakeRequest:
    def __init__(self, bus: EventBus) -> None:
        self.app = type("App", (), {"state": type("State", (), {"event_bus": bus})})()

    async def is_disconnected(self) -> bool:  # pragma: no cover - never consumed here
        return True


def test_events_response_is_event_stream():
    response = asyncio.run(events(_FakeRequest(EventBus())))
    assert response.media_type == "text/event-stream"
    assert response.headers["cache-control"] == "no-cache"


def test_events_is_registered_on_the_public_router():
    public_paths = {route.path for route in public_router.routes}
    privileged_paths = {route.path for route in privileged_router.routes}
    assert "/events" in public_paths  # public: the token-gated router has no dependency
    assert "/events" not in privileged_paths
