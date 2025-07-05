""" A base class for all Pyrox objects to be represented in the GUI interface.
    """
from __future__ import annotations


import tkinter as tk
from typing import Any, Optional, Self


from ..abc.meta import Loggable, PyroxObject


__all__ = (
    'PyroxGuiObject',
)


class PyroxGuiObjectAttributeResolver:
    """A class to resolve attributes of PyroxGuiObject.

    This class is intended to resolve attributes of a PyroxGuiObject

    and specificy what type of GUI element should be used to display and modify

    the attribute in a GUI context."""

    def __init__(self, pyrox_object: PyroxGuiObject):
        self._pyrox_object = pyrox_object

    def resolve(self, attribute_name: str) -> Any:
        """Resolve the attribute of the PyroxGuiObject.

        Args:
            attribute_name (str): The name of the attribute to resolve.

        Returns:
            Any: The resolved value of the attribute.
        """
        return getattr(self._pyrox_object, attribute_name, None)


class PyroxGuiObject(Loggable):
    """A base class for all Pyrox objects to be represented in the GUI interface.

    .. ------------------------------------------------------------

    .. package:: models.gui.pyroxguiobject

    .. ------------------------------------------------------------

    Attributes
    -----------
    logger: :class:`logging.Logger`
        Logger for this object.
    """

    __slots__ = ('_pyrox_object',)

    def __getattr__(self, name):
        if not self._pyrox_object:
            return None
        return getattr(self._pyrox_object, name, None)

    def __init__(self,
                 pyrox_object: Optional[PyroxObject] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self._pyrox_object = pyrox_object

    @property
    def name(self) -> str:
        """        Name of this object.

        Returns:
            str: Name of the object, which is the class name of the
            underlying Pyrox object if it exists, otherwise 'PyroxOGuibject'.
        """
        return getattr(self._pyrox_object, 'name', 'PyroxGuiObject')

    @property
    def description(self) -> str:
        """Description of this object.

        This property is meant to be overridden by subclasses to provide
        a specific description for the object.

        Returns
        ----------
            :type:`str`: Description of the object.
        """
        return getattr(self._pyrox_object, 'description', '')

    @property
    def pyrox_object(self) -> Optional[PyroxObject]:
        """Get the underlying Pyrox object.

        Returns
        ----------
            :type:`Optional[PyroxObject]`: The underlying Pyrox object or None if not set.
        """
        return self._pyrox_object

    @classmethod
    def from_data(cls,
                  data: Any) -> Self:
        """get a new instance of this class from data.

        this method is intended to be overridden by subclasses to
        provide a specific way to create an instance from data.

        Args:
            data (Any): _description_
        """
        if isinstance(data, PyroxObject):
            data = PyroxGuiObject(pyrox_object=data)

    def editable_gui_interface_attributes(self) -> list[str]:
        """Return a set of attributes that are intended for GUI interface and editable.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be displayed in a GUI context and are editable.

        Returns
        ----------
            :type:`list[str]`: Set of attribute names.
        """
        return self.gui_interface_attributes()

    def get_property_choices(self, property_name: str) -> list[str]:
        """Get a list of choices for a given property.

        This method is intended to be overridden by subclasses to provide
        specific choices for a property that can be displayed in a GUI context.

        Args:
            property_name (str): The name of the property to get choices for.

        Returns
        ----------
            :type:`list[str]`: List of choices for the property.
        """
        return []

    def gui_interface_attributes(self) -> list[tuple[str, str]]:
        """Return a set of attributes that are intended for GUI interface.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be displayed in a GUI context.

        Returns
        ----------
            :type:`list[str]`: Set of attribute names.
        """
        return [
            ('name', 'Name', tk.Label, True),
            ('description', 'Description', tk.Label, True),
        ]

    def public_attributes(self) -> list[str]:
        """Return a set of public attributes for this object.

        This method is meant to be overridden by subclasses to provide
        specific attributes that should be considered public.

        Returns
        ----------
            :type:`list[str]`: Set of public attribute names.
        """
        return {attr for attr in dir(self._pyrox_object) if not attr.startswith('_')
                and not callable(getattr(self._pyrox_object, attr))
                and not isinstance(getattr(self._pyrox_object, attr), property)}
