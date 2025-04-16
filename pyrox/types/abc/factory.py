"""factory meta class to support factory assembly of classes
    """
from __future__ import annotations


from typing import Generic, TypeVar


T = TypeVar('T')


__all__ = (
    'Factory',
)


class Factory(Generic[T]):
    """meta factory used to assist in creating factories for class creation
    """

    @staticmethod
    def generic() -> T:
        """return an assembled generic version of this class

        Returns:
            T: assembled class
        """
        raise NotImplementedError('This method must be overriden by inheriting class!')
