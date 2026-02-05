from pyrox.interfaces import INameable, IConnectable
from pyrox.interfaces.protocols.physics import IPhysicsBody2D


class IBasePhysicsBody(
    INameable,
    IConnectable,
    IPhysicsBody2D
):
    """Interface class for custom physics bodies extending IPhysicsBody2D.
    Provides additional methods and properties for common physics body
    functionality.

    Intended for use in a physics environment where bodies may need to
    interact, be tagged, and have common checks performed.
    """

    def get_tags(self) -> list[str]:
        """Get the list of tags associated with this body.

        Returns:
            List of tags
        """
        ...

    def set_tags(self, tags: list[str]) -> None:
        """Set the list of tags for this body.

        Args:
            tags: List of tags to set
        """
        ...

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

    @classmethod
    def from_dict(cls, data: dict) -> 'IBasePhysicsBody':
        """Create a physics body from a dictionary representation.

        Args:
            data: Dictionary with body properties

        Returns:
            Instance of IBasePhysicsBody
        """
        raise NotImplementedError()

    @property
    def tags(self) -> list[str]:
        """Get the list of tags associated with this body.

        Returns:
            List of tags
        """
        return self.get_tags()
