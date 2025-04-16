"""base model
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING


from .meta import SnowFlake


if TYPE_CHECKING:
    from .application import PartialApplication
    from .viewmodel import ViewModel


__all__ = (
    'Model',
)


class Model(SnowFlake):
    """A model for use in an application.

    .. ------------------------------------------------------------

    .. package:: types.abc.model

    .. ------------------------------------------------------------

    Attributes
    -----------
    application: :class:`PartialApplication`
        The parent application of this :class:`Model`

    view_model: Optional[:class:`ViewModel`]
        The :class:`ViewModel` this :class:`Model` is associated with, if any.
    """
    application: PartialApplication
    view_model: Optional[ViewModel]
