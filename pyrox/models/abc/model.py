"""base model
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING, Union


from .meta import Runnable


if TYPE_CHECKING:
    from .application import Application


__all__ = (
    'Model',
)


class Model(Runnable):
    """.. description::
    A logical partial for use in an application.
    .. ------------------------------------------------------------
    .. package::
    models.abc.model
    .. ------------------------------------------------------------
    .. attributes::
    application: Optional[:class:`PartialApplication`]
        The parent application of this :class:`Model`, if any.
    """

    __slots__ = ('_application', '_view_model')

    def __init__(self,
                 application: Optional[Application] = None):
        super().__init__()

        self._application: Optional[Application] = application

    @property
    def application(self) -> Application:
        """The parent application of this :class:`Model`, if any.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: Optional[:class:`PartialApplication`]
        """
        return self._application

    @application.setter
    def application(self, application: Union[Application, None]) -> None:
        """Set the parent application of this :class:`Model`.

        .. ------------------------------------------------------------

        Parameters
        -----------
            application: Optional[:class:`PartialApplication`]
                The parent application to set.
        """
        self._application = application
