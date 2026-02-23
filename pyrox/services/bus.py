"""Bus module for event handling and communication between components.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Generic, TypeVar
from pyrox.services import log


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
        event_type: T,
        callback: Callable[[E], None]
    ) -> None:
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        if callback not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(callback)
            log(cls).debug(f"Subscribed {callback.__name__} to {event_type.name}")

    @classmethod
    def unsubscribe(
            cls,
            event_type: T,
            callback: Callable[[E], None]) -> None:
        if event_type in cls._subscribers:
            if callback in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(callback)
                log(cls).debug(f"Unsubscribed {callback.__name__} from {event_type.name}")

    @classmethod
    def publish(
        cls,
        event: E
    ) -> None:
        subscribers = cls._subscribers.get(event.event_type, [])
        log(cls).debug(f"Publishing {event.event_type.name} to {len(subscribers)} subscribers")
        dead = []
        for cb in subscribers.copy():
            try:
                cb(event)
            except Exception as e:
                log(cls).error(f"Error in subscriber {cb.__name__}: {e}")
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
