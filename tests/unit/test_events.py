"""EventBus unit tests (v1.3.0 live updates)."""

from __future__ import annotations

import asyncio
import threading

from receipt_board.core.events import EventBus


def test_publish_increments_revision():
    bus = EventBus()
    assert bus.revision == 0
    assert bus.publish() == 1
    assert bus.publish() == 2
    assert bus.revision == 2


def test_subscriber_receives_published_revision():
    async def scenario() -> int:
        bus = EventBus()
        sub = bus.subscribe()
        bus.publish()
        rev = await asyncio.wait_for(sub.get(), timeout=1)
        sub.close()
        return rev

    assert asyncio.run(scenario()) == 1


def test_publish_from_another_thread_is_delivered():
    async def scenario() -> int:
        bus = EventBus()
        sub = bus.subscribe()
        thread = threading.Thread(target=bus.publish)
        thread.start()
        thread.join()
        rev = await asyncio.wait_for(sub.get(), timeout=1)
        sub.close()
        return rev

    assert asyncio.run(scenario()) == 1


def test_subscriber_coalesces_to_latest_revision():
    async def scenario() -> int:
        bus = EventBus()
        sub = bus.subscribe()
        bus.publish()  # 1
        bus.publish()  # 2
        await asyncio.sleep(0.01)  # let both scheduled deliveries run
        rev = await asyncio.wait_for(sub.get(), timeout=1)
        sub.close()
        return rev

    # The late subscriber only sees the newest marker, not every intermediate one.
    assert asyncio.run(scenario()) == 2


def test_closed_subscriber_is_not_notified():
    async def scenario() -> bool:
        bus = EventBus()
        sub = bus.subscribe()
        sub.close()
        bus.publish()
        await asyncio.sleep(0.01)
        return sub._queue.empty()

    assert asyncio.run(scenario()) is True
