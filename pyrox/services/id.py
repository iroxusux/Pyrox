"""ID generation service for Pyrox framework.
Provides a simple unique ID generator for SnowFlake objects.
"""


class IdGeneratorService:
    """Service class for generating unique IDs for SnowFlake objects.
    This class provides static methods to generate and retrieve unique IDs.
    """
    __slots__ = ()
    _ctr = 0

    @staticmethod
    def get_id() -> int:
        """Get a unique ID from the generator.

        Returns:
            int: Unique ID for a SnowFlake object.
        """
        IdGeneratorService._ctr += 1
        return IdGeneratorService._ctr

    @staticmethod
    def curr_value() -> int:
        """Retrieve the current value of the ID generator.

        Returns:
            int: Current value of the counter.
        """
        return IdGeneratorService._ctr
