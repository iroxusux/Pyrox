from typing import Optional
from pyrox.interfaces import IConnectable
from pyrox.interfaces.protocols.physics import IPhysicsBody2D


class IBasePhysicsBody(
    IConnectable,
    IPhysicsBody2D
):
    """Interface class for custom physics bodies extending IPhysicsBody2D.
    Provides additional methods and properties for common physics body
    functionality.

    Intended for use in a physics environment where bodies may need to
    interact, be tagged, and have common checks performed.
    """

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

    def get_properties(self) -> dict[str, dict]:
        """Get properties that can be edited in the properties panel.

        Returns:
            Dictionary mapping property names to their metadata
        """
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, data: dict) -> 'IBasePhysicsBody':
        """Create a physics body from a dictionary representation.

        Args:
            data: Dictionary with body properties

        Returns:
            Instance of IBasePhysicsBody
        """
        raise NotImplementedError()

    def to_dict(self) -> dict:
        """Convert a physics body to a dictionary representation.

        Args:
            body: Instance of IBasePhysicsBody to convert

        Returns:
            Dictionary with body properties
        """
        raise NotImplementedError()

    @property
    def template_name(self) -> Optional[str]:
        """Get the template name associated with this body, if any.

        Returns:
            Template name or None if not set
        """
        return self.get_template_name()
