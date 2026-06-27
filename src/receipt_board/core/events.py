"""In-process change-notification bus for live GUI updates (v1.3.0).

Every committed mutation bumps a monotonic ``revision``; open SSE subscribers receive the
new revision and reload. ``publish()`` is called from the request worker thread (after the
per-request commit in :func:`receipt_board.api.deps.get_session`), so delivery to the
async subscribers is bridged onto their event loop with ``call_soon_threadsafe``.

The marker is deliberately non-sensitive (just an integer): the SSE endpoint that exposes
it can stay public (``EventSource`` cannot send the session token — see ADR-0012).
"""

from __future__ import annotations

import asyncio
import contextlib
import threading

# Key set on ``Session.info`` by the audit chokepoint to flag a transaction that mutated
# state; ``get_session`` publishes once after such a transaction commits.
SESSION_DIRTY_KEY = "rb_dirty"


class Subscriber:
    """A single live subscriber's mailbox (one per open SSE connection)."""

    def __init__(self, bus: EventBus, loop: asyncio.AbstractEventLoop) -> None:
        self._bus = bus
        self._loop = loop
        self._queue: asyncio.Queue[int] = asyncio.Queue()

    def _offer(self, revision: int) -> None:
        """Hand a revision to this subscriber from any thread."""
        # A closed loop (subscriber tearing down) raises; harmless, it is dropped.
        with contextlib.suppress(RuntimeError):
            self._loop.call_soon_threadsafe(self._put, revision)

    def _put(self, revision: int) -> None:
        # Keep only the latest revision pending: a subscriber that wakes up late only needs
        # the newest marker to trigger one reload.
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:  # pragma: no cover - race guard
                break
        self._queue.put_nowait(revision)

    async def get(self) -> int:
        """Await the next revision marker."""
        return await self._queue.get()

    def close(self) -> None:
        self._bus._remove(self)


class EventBus:
    """Process-wide, thread-safe revision counter with async fan-out to subscribers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._revision = 0
        self._subscribers: set[Subscriber] = set()

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    def publish(self) -> int:
        """Bump the revision and notify all subscribers; returns the new revision."""
        with self._lock:
            self._revision += 1
            revision = self._revision
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber._offer(revision)
        return revision

    def subscribe(self) -> Subscriber:
        """Register a subscriber bound to the running event loop (call from async code)."""
        loop = asyncio.get_running_loop()
        subscriber = Subscriber(self, loop)
        with self._lock:
            self._subscribers.add(subscriber)
        return subscriber

    def _remove(self, subscriber: Subscriber) -> None:
        with self._lock:
            self._subscribers.discard(subscriber)
