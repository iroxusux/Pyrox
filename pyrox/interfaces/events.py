"""Event and observer interface abstractions for Pyrox framework.

These interfaces define the contracts for observer patterns, event publishing,
subscriptions, and notifications without implementation dependencies, enabling
loosely-coupled event-driven architectures.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class IObserver(ABC):
    """Interface for observer pattern implementations.

    Defines the contract for objects that can observe and react to
    changes in other objects, enabling loose coupling between components.
    """

    @abstractmethod
    def update(self, source: Any, event_type: str, data: Any = None) -> None:
        """Called when the observed object changes.

        Args:
            source: The object that triggered the update.
            event_type: Type of event that occurred.
            data: Optional data associated with the event.
        """
        pass

    @abstractmethod
    def get_observer_id(self) -> str:
        """Get a unique identifier for this observer.

        Returns:
            str: Unique observer identifier.
        """
        pass


class ISubscribable(ABC):
    """Interface for objects that can be subscribed to.

    Provides functionality for managing observers and notifying them
    of changes, implementing the observable part of the observer pattern.
    """

    @abstractmethod
    def subscribe(self, observer: IObserver) -> None:
        """Subscribe an observer to this object.

        Args:
            observer: The observer to subscribe.
        """
        pass

    @abstractmethod
    def unsubscribe(self, observer: IObserver) -> None:
        """Unsubscribe an observer from this object.

        Args:
            observer: The observer to unsubscribe.
        """
        pass

    @abstractmethod
    def notify_observers(self, event_type: str, data: Any = None) -> None:
        """Notify all subscribed observers of a change.

        Args:
            event_type: Type of event that occurred.
            data: Optional data associated with the event.
        """
        pass

    @abstractmethod
    def get_observer_count(self) -> int:
        """Get the number of subscribed observers.

        Returns:
            int: Number of subscribed observers.
        """
        pass

    @abstractmethod
    def has_observer(self, observer: IObserver) -> bool:
        """Check if an observer is subscribed.

        Args:
            observer: The observer to check.

        Returns:
            bool: True if observer is subscribed, False otherwise.
        """
        pass


class IEventPublisher(ABC):
    """Interface for event publishing systems.

    Provides functionality for publishing events to multiple subscribers
    with support for different event types and filtering.
    """

    @abstractmethod
    def publish_event(self, event_type: str, data: Any = None, source: Any = None) -> None:
        """Publish an event to all interested subscribers.

        Args:
            event_type: Type of event being published.
            data: Optional data associated with the event.
            source: Optional source object that triggered the event.
        """
        pass

    @abstractmethod
    def subscribe_to_event(self, event_type: str, callback: Callable[[str, Any, Any], None]) -> str:
        """Subscribe to a specific event type.

        Args:
            event_type: Type of event to subscribe to.
            callback: Function to call when event occurs.

        Returns:
            str: Subscription ID for later unsubscription.
        """
        pass

    @abstractmethod
    def unsubscribe_from_event(self, subscription_id: str) -> bool:
        """Unsubscribe from events using subscription ID.

        Args:
            subscription_id: ID returned from subscribe_to_event.

        Returns:
            bool: True if unsubscribed successfully, False if ID not found.
        """
        pass

    @abstractmethod
    def get_event_types(self) -> List[str]:
        """Get list of available event types.

        Returns:
            List[str]: List of event type names.
        """
        pass

    @abstractmethod
    def get_subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Get number of subscribers for an event type or total.

        Args:
            event_type: Optional event type to check. If None, returns total.

        Returns:
            int: Number of subscribers.
        """
        pass


class INotificationService(ABC):
    """Interface for notification services.

    Provides functionality for sending notifications to users through
    various channels (GUI dialogs, system notifications, etc.).
    """

    @abstractmethod
    def send_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info",
        **kwargs
    ) -> bool:
        """Send a notification to the user.

        Args:
            title: Notification title.
            message: Notification message.
            notification_type: Type of notification (info, warning, error, success).
            **kwargs: Additional notification parameters.

        Returns:
            bool: True if notification was sent successfully.
        """
        pass

    @abstractmethod
    def send_toast_notification(
        self,
        message: str,
        duration_ms: int = 3000,
        **kwargs
    ) -> bool:
        """Send a temporary toast notification.

        Args:
            message: Toast message.
            duration_ms: Duration to show the toast in milliseconds.
            **kwargs: Additional toast parameters.

        Returns:
            bool: True if toast was sent successfully.
        """
        pass

    @abstractmethod
    def show_dialog(
        self,
        title: str,
        message: str,
        dialog_type: str = "info",
        buttons: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Show a dialog to the user.

        Args:
            title: Dialog title.
            message: Dialog message.
            dialog_type: Type of dialog (info, warning, error, question).
            buttons: Optional custom button labels.
            **kwargs: Additional dialog parameters.

        Returns:
            str: Button clicked by user.
        """
        pass

    @abstractmethod
    def register_notification_handler(
        self,
        notification_type: str,
        handler: Callable[[str, str, Dict[str, Any]], bool]
    ) -> None:
        """Register a custom notification handler.

        Args:
            notification_type: Type of notification to handle.
            handler: Function to handle notifications of this type.
        """
        pass

    @abstractmethod
    def set_notification_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications.

        Args:
            enabled: True to enable notifications, False to disable.
        """
        pass

    @abstractmethod
    def is_notification_enabled(self) -> bool:
        """Check if notifications are enabled.

        Returns:
            bool: True if notifications are enabled, False otherwise.
        """
        pass


__all__ = (
    'IObserver',
    'ISubscribable',
    'IEventPublisher',
    'INotificationService',
)
