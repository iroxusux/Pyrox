"""Bus module for event handling and communication between components.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar
from pyrox.services.logging import log


class EventType(Enum):
    """Base class for event types. Subclasses should define specific event types as enum members."""
    pass


T = TypeVar('T', bound=EventType)


@dataclass
class Event(Generic[T]):
    """Base class for events. Subclasses should define specific event data as fields."""
    event_type: T


E = TypeVar('E', bound=Event)


class EventBus(Generic[T, E]):
    """Base class for static event buses. Each subclass gets its own isolated subscriber registry."""

    _subscribers: dict[T, list[Callable[[E], None]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._subscribers = {}  # each subclass gets its own dict - not shared

    @classmethod
    def subscribe(
        cls,
        event_type: T | list[T],
        callback: Callable[[E], None]
    ) -> bool:
        """Subscribe a callback to an event type or list of event types.
        Returns True if subscription was successful.

        Args:
            event_type: A single event type or a list of event types to subscribe to.
            callback: A callable that takes an event object as its only argument.

        Returns:
            bool: True if subscription was successful, False if callback was already subscribed.
        """

        if isinstance(event_type, list):
            for et in event_type:
                cls.subscribe(et, callback)
            return True

        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []

        if callback not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(callback)
            return True

        return False

    @classmethod
    def unsubscribe(
        cls,
        event_type: T,
        callback: Callable[[E], None]
    ) -> bool:
        """Unsubscribe a callback from an event type.
        Returns True if unsubscription was successful.

        Args:
            event_type: The event type to unsubscribe from.
            callback: The callback to remove.

        Returns:
            bool: True if unsubscription was successful, False if callback was not found.
        """
        if event_type in cls._subscribers:
            if callback in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(callback)
                return True

        return False

    @classmethod
    def publish(
        cls,
        event: E
    ) -> None:

        subscribers = cls._subscribers.get(event.event_type, [])
        dead = []
        for cb in subscribers.copy():
            try:
                cb(event)
            except Exception as exc:
                log(cls.__name__).error(
                    "EventBus: unhandled exception in subscriber %r for %s: %s",
                    cb, event.event_type, exc, exc_info=True
                )
                dead.append(cb)
        for cb in dead:
            cls.unsubscribe(event.event_type, cb)

    @classmethod
    def clear(cls) -> None:
        cls._subscribers.clear()

    @classmethod
    def get_subscriber_count(
        cls,
        event_type: T
    ) -> int:
        return len(cls._subscribers.get(event_type, []))
