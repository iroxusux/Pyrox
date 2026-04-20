from dataclasses import dataclass
from enum import auto
from pyrox.services.bus import EventBus, Event, EventType


class StatusUpdateEventType(EventType):
    """Enum for status update event types."""
    UPDATE = auto()


@dataclass
class StatusUpdateEvent(Event[StatusUpdateEventType]):
    """Event data for status update events."""
    status_message: str


class StatusUpdateEventBus(EventBus[StatusUpdateEventType, StatusUpdateEvent]):
    """Static event bus for status update events.
    """
    pass
