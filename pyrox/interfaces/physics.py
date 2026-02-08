from typing import Optional
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

    def get_template_name(self) -> Optional[str]:
        """Get the template name associated with this body, if any.

        Returns:
            Template name or None if not set
        """
        ...
        
    def set_template_name(self, template_name: Optional[str]) -> None:
        """Set the template name for this body.

        Args:
            template_name: Template name to set or None to clear
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

    @property
    def template_name(self) -> Optional[str]:
        """Get the template name associated with this body, if any.

        Returns:
            Template name or None if not set
        """
        return self.get_template_name()