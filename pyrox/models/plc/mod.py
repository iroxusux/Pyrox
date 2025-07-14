"""Introspective Module for a Rockwell PLC.
    This is a wrapper around the Module class to provide introspection capabilities.
    """
from __future__ import annotations


from pathlib import Path
from pyrox.services import class_services
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from pyrox.models.plc import Module


class IntrospectiveModule:

    _known_modules_built = False
    _known_modules: list[Module] = []

    @staticmethod
    def get_known_modules() -> list[Module]:
        """Get the list of known modules.
        .. ------------------------------------------------------------
        .. returns::
            :class:`list[Module]`
                The list of known modules.
        """
        if not IntrospectiveModule._known_modules:
            IntrospectiveModule._known_modules = class_services.find_and_instantiate_class(
                directory_path=str(Path(__file__).parent.parent.parent) + '\\applications\\mod',
                class_name=IntrospectiveModule.__name__,
                as_subclass=True,
                ignoring_classes=['IntrospectiveModule'],
                parent_class=IntrospectiveModule)
        IntrospectiveModule._known_modules_built = True
        return IntrospectiveModule._known_modules

    """Introspective Module for a rockwell plc.
    This is a wrapper around the Module class to provide introspection capabilities.
    Such as, a Siemens G115Drive, or a Rockwell 1756-L85E controller.
    It is used to extend capabilities of known modules, or to provide a way to introspect unknown modules.
    """

    def __init__(self, module: Optional[Module] = None):
        self._module = module

    @property
    def catalog_number(self) -> str:
        """The catalog number of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def input_cxn_point(self) -> str:
        """The input connection point of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def output_cxn_point(self) -> str:
        """The output connection point of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def input_size(self) -> int:
        """The input size of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @property
    def output_size(self) -> int:
        """The output size of the module."""
        raise NotImplementedError('This method should be implemented by the subclass.')

    @classmethod
    def from_meta_data(cls,
                       module: Module,
                       lazy_match_catalog: Optional[bool] = False) -> IntrospectiveModule:
        """Create an IntrospectiveModule from meta data.
        .. ------------------------------------------------------------
        .. arguments::
            meta_data :class:`dict`
                The meta data to create the IntrospectiveModule from.
            module :class:`Module`
                The module to wrap with the IntrospectiveModule.
        .. ------------------------------------------------------------
        .. returns::
            :class:`IntrospectiveModule`
        """
        if not module:
            raise ValueError('Module is required to create an IntrospectiveModule.')
        if not module.catalog_number:
            return cls(module)
        if not IntrospectiveModule._known_modules_built:
            IntrospectiveModule.get_known_modules()
        for m in IntrospectiveModule._known_modules:
            if (m.catalog_number == module.catalog_number and
                    m.input_cxn_point == module.input_connection_point and
                    m.output_cxn_point == module.output_connection_point and
                    m.input_size == module.input_connection_size and
                    m.output_size == module.output_connection_size):
                return m.__class__(module)
            if lazy_match_catalog and module.catalog_number != 'ETHERNET-MODULE':
                if m.catalog_number in module.catalog_number:
                    return m.__class__(module)
        return cls(module)

    @property
    def type_(self) -> str:
        """Get the type of the module."""
        return self.__class__.__name__
