"""Unit tests for the EventBus base class in pyrox.services.bus.

Tests cover subscriber isolation between subclasses, subscribe/unsubscribe
mechanics, event publishing (including dead-callback cleanup), clear(), and
get_subscriber_count().
"""

import unittest
from enum import auto
from dataclasses import dataclass
from pyrox.services.bus import Event, EventBus, EventType


# ---------------------------------------------------------------------------
# Minimal concrete types used across all tests
# ---------------------------------------------------------------------------

class FooEventType(EventType):
    FOO_A = auto()
    FOO_B = auto()


class BarEventType(EventType):
    BAR_A = auto()


@dataclass
class FooEvent(Event[FooEventType]):
    payload: str = ""


@dataclass
class BarEvent(Event[BarEventType]):
    value: int = 0


class FooBus(EventBus[FooEventType, FooEvent]):
    pass


class BarBus(EventBus[BarEventType, BarEvent]):
    pass


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _make_recording_callback():
    """Return a callback that records every event it receives."""
    received = []

    def callback(event):
        received.append(event)

    callback.received = received  # type: ignore
    return callback


def _make_raising_callback(exc_type=RuntimeError, message="boom"):
    """Return a callback that always raises."""
    def bad_callback(event):
        raise exc_type(message)
    return bad_callback


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEventBusIsolation(unittest.TestCase):
    """Each EventBus subclass must own its own _subscribers dict."""

    def setUp(self):
        FooBus.clear()
        BarBus.clear()

    def tearDown(self):
        FooBus.clear()
        BarBus.clear()

    def test_subclasses_have_distinct_subscriber_dicts(self):
        self.assertIsNot(FooBus._subscribers, BarBus._subscribers)

    def test_subscribing_to_one_bus_does_not_affect_other(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)
        self.assertEqual(BarBus.get_subscriber_count(BarEventType.BAR_A), 0)

    def test_clearing_one_bus_does_not_affect_other(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        BarBus.subscribe(BarEventType.BAR_A, cb)

        FooBus.clear()

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)
        self.assertEqual(BarBus.get_subscriber_count(BarEventType.BAR_A), 1)

    def test_publishing_to_one_bus_does_not_trigger_other(self):
        foo_cb = _make_recording_callback()
        bar_cb = _make_recording_callback()

        FooBus.subscribe(FooEventType.FOO_A, foo_cb)
        BarBus.subscribe(BarEventType.BAR_A, bar_cb)

        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A, payload="hello"))

        self.assertEqual(len(foo_cb.received), 1)  # type: ignore
        self.assertEqual(len(bar_cb.received), 0)  # type: ignore


class TestEventBusSubscribe(unittest.TestCase):
    """Tests for subscribe() mechanics."""

    def setUp(self):
        FooBus.clear()

    def tearDown(self):
        FooBus.clear()

    def test_subscribe_registers_callback(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)

    def test_subscribe_multiple_callbacks(self):
        cb1 = _make_recording_callback()
        cb2 = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb1)
        FooBus.subscribe(FooEventType.FOO_A, cb2)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 2)

    def test_duplicate_subscribe_is_ignored(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        FooBus.subscribe(FooEventType.FOO_A, cb)  # second call is a no-op
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)

    def test_subscribe_to_different_event_types_independently(self):
        cb_a = _make_recording_callback()
        cb_b = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb_a)
        FooBus.subscribe(FooEventType.FOO_B, cb_b)

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_B), 1)


class TestEventBusUnsubscribe(unittest.TestCase):
    """Tests for unsubscribe() mechanics."""

    def setUp(self):
        FooBus.clear()

    def tearDown(self):
        FooBus.clear()

    def test_unsubscribe_removes_callback(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        FooBus.unsubscribe(FooEventType.FOO_A, cb)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)

    def test_unsubscribe_only_removes_specified_callback(self):
        cb1 = _make_recording_callback()
        cb2 = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb1)
        FooBus.subscribe(FooEventType.FOO_A, cb2)

        FooBus.unsubscribe(FooEventType.FOO_A, cb1)

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)

    def test_unsubscribe_nonexistent_callback_is_noop(self):
        cb = _make_recording_callback()
        # Never subscribed — should not raise
        FooBus.unsubscribe(FooEventType.FOO_A, cb)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)

    def test_unsubscribe_unknown_event_type_is_noop(self):
        cb = _make_recording_callback()
        # Event type never registered at all — should not raise
        FooBus.unsubscribe(FooEventType.FOO_B, cb)


class TestEventBusPublish(unittest.TestCase):
    """Tests for publish() mechanics."""

    def setUp(self):
        FooBus.clear()

    def tearDown(self):
        FooBus.clear()

    def test_publish_calls_subscriber(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)

        event = FooEvent(event_type=FooEventType.FOO_A, payload="test")
        FooBus.publish(event)

        self.assertEqual(len(cb.received), 1)  # type: ignore
        self.assertIs(cb.received[0], event)  # type: ignore

    def test_publish_calls_all_subscribers(self):
        cb1 = _make_recording_callback()
        cb2 = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb1)
        FooBus.subscribe(FooEventType.FOO_A, cb2)

        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))

        self.assertEqual(len(cb1.received), 1)  # type: ignore
        self.assertEqual(len(cb2.received), 1)  # type: ignore

    def test_publish_only_notifies_matching_event_type(self):
        cb_a = _make_recording_callback()
        cb_b = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb_a)
        FooBus.subscribe(FooEventType.FOO_B, cb_b)

        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))

        self.assertEqual(len(cb_a.received), 1)  # type: ignore
        self.assertEqual(len(cb_b.received), 0)  # type: ignore

    def test_publish_with_no_subscribers_is_noop(self):
        # Should not raise when no one is subscribed
        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))

    def test_publish_multiple_events(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)

        for i in range(5):
            FooBus.publish(FooEvent(event_type=FooEventType.FOO_A, payload=str(i)))

        self.assertEqual(len(cb.received), 5)  # type: ignore

    def test_dead_callback_is_removed_after_exception(self):
        bad_cb = _make_raising_callback()
        good_cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, bad_cb)
        FooBus.subscribe(FooEventType.FOO_A, good_cb)

        # First publish — bad_cb raises but good_cb still receives the event
        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))

        self.assertEqual(len(good_cb.received), 1)  # type: ignore
        # bad_cb should have been pruned
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)

        # Second publish — only good_cb should fire
        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))
        self.assertEqual(len(good_cb.received), 2)  # type: ignore

    def test_all_dead_callbacks_removed_when_all_raise(self):
        bad1 = _make_raising_callback()
        bad2 = _make_raising_callback()
        FooBus.subscribe(FooEventType.FOO_A, bad1)
        FooBus.subscribe(FooEventType.FOO_A, bad2)

        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)


class TestEventBusClear(unittest.TestCase):
    """Tests for clear() mechanics."""

    def setUp(self):
        FooBus.clear()

    def tearDown(self):
        FooBus.clear()

    def test_clear_removes_all_subscriptions(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        FooBus.subscribe(FooEventType.FOO_B, cb)

        FooBus.clear()

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_B), 0)

    def test_clear_allows_resubscription(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        FooBus.clear()
        FooBus.subscribe(FooEventType.FOO_A, cb)

        FooBus.publish(FooEvent(event_type=FooEventType.FOO_A))

        self.assertEqual(len(cb.received), 1)  # type: ignore

    def test_clear_on_empty_bus_is_noop(self):
        # Should not raise on an already-empty bus
        FooBus.clear()


class TestEventBusGetSubscriberCount(unittest.TestCase):
    """Tests for get_subscriber_count()."""

    def setUp(self):
        FooBus.clear()

    def tearDown(self):
        FooBus.clear()

    def test_count_zero_when_no_subscribers(self):
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)

    def test_count_reflects_subscribe(self):
        cb1 = _make_recording_callback()
        cb2 = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb1)
        FooBus.subscribe(FooEventType.FOO_A, cb2)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 2)

    def test_count_reflects_unsubscribe(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)
        FooBus.unsubscribe(FooEventType.FOO_A, cb)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 0)

    def test_count_independent_per_event_type(self):
        cb = _make_recording_callback()
        FooBus.subscribe(FooEventType.FOO_A, cb)

        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_A), 1)
        self.assertEqual(FooBus.get_subscriber_count(FooEventType.FOO_B), 0)


if __name__ == "__main__":
    unittest.main()
