
from pyrox.interfaces.protocols.physics import IPhysicsBody2D


class IBasePhysicsBody(IPhysicsBody2D):
    """Interface class for custom physics bodies extending IPhysicsBody2D.
    Provides additional methods and properties for common physics body
    functionality.

    Intended for use in a physics environment where bodies may need to
    interact, be tagged, and have common checks performed.
    """

    def has_tag(self, tag: str) -> bool:
        """Check if this body has a specific tag.

        Args:
            tag: Tag to check for

        Returns:
            True if the body has the tag
        """
        ...

    def add_tag(self, tag: str) -> None:
        """Add a tag to this body.

        Args:
            tag: Tag to add
        """
        ...

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this body.

        Args:
            tag: Tag to remove
        """
        ...

    def is_on_top_of(self, other: IPhysicsBody2D) -> bool:
        """Check if this body is on top of another body.

        Useful for conveyor belts, platforms, etc.

        Args:
            other: The other physics body

        Returns:
            True if this body is resting on top of the other body
        """
        ...
