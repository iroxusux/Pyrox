from pyrox.models.meta import SliceableInt


def clear_bit(word: int,
              bit_position: int) -> int:
    """Binary slicing operation to clear a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        word: :class:`int`
            Integer word to clear bit from
        bit_position: :class:`int`
            Bit position of the word to clear to bit of.

        Returns
        ----------
            :class:`int`
        """
    return SliceableInt(word).clear_bit(bit_position).__int__()


def set_bit(word: int,
            bit_position: int) -> int:
    """Binary slicing operation to set a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        word: :class:`int`
            Integer word to set bit in
        bit_position: :class:`int`
            Bit position of the word to set to bit of.

        Returns
        ----------
            :class:`int`
        """
    return SliceableInt(word).set_bit(bit_position).__int__()


def read_bit(word: int,
             bit_position: int) -> bool:
    """Binary slicing operation to read a bit of an integer.

        .. -------------------------------------------------------

        Arguments
        ----------
        word: :class:`int`
            Integer word to set read from
        bit_position: :class:`int`
            Bit position of the word to read the bit from.

        Returns
        ----------
            :class:`bool`
        """
    return SliceableInt(word).read_bit(bit_position)
