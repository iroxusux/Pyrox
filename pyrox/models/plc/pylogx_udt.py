from struct import pack, unpack_from
from typing import Optional, Self


from ...utils import clear_bit, read_bit, set_bit


class SupportsPacking:
    """abc class for pylogix data packing
    """
    def supports_io(word, bit):
        def decorator(func):
            def wrapper(self, value: bool = False):
                return func(self, word=word, bit=bit, value=value)
            return wrapper
        return decorator

    def __init__(self):
        self._data = [0] * self.__size__()

    def __size__(self):
        raise NotImplementedError()

    def __pack__(self):
        bytes = bytearray()
        for x in self._data:
            bytes += pack('>i', x)
        return bytes

    def __unpack__(self, data, offset=0):
        self._data[0] = unpack_from('>i', data, offset)[0]

    def _read(self, word, bit) -> bool:
        return read_bit(self._data[word], bit)

    def _write(self, word, bit, value) -> None:
        if value:
            self._data[word] = set_bit(self._data[word], bit)
        else:
            self._data[word] = clear_bit(self._data[word], bit)

    @classmethod
    def as_unpacked(cls, data) -> Optional[Self]:
        if not data:
            return None

        x = cls()
        x.__unpack__(data)
        return x


class ConnectionStatus(SupportsPacking):

    """PLC Connection Status
    """

    @property
    @SupportsPacking.supports_io(0, 0)
    def run_mode(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @run_mode.setter
    @SupportsPacking.supports_io(0, 0)
    def run_mode(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 1)
    def connection_faulted(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @connection_faulted.setter
    @SupportsPacking.supports_io(0, 1)
    def connection_faulted(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    def __size__(self):
        return 1


class AB_1734_IB8S_Safety5_I_0(SupportsPacking):
    """pyrox implimentation of a udt for pylogix to interact with
    """

    def __init__(self):
        super().__init__()
        self._connection_status: ConnectionStatus = ConnectionStatus()

    @property
    def connection_status(self) -> ConnectionStatus:
        return self._connection_status

    @property
    @SupportsPacking.supports_io(0, 0)
    def pt00_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt00_data.setter
    @SupportsPacking.supports_io(0, 0)
    def pt00_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 1)
    def pt01_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt01_data.setter
    @SupportsPacking.supports_io(0, 1)
    def pt01_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 2)
    def pt02_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt02_data.setter
    @SupportsPacking.supports_io(0, 2)
    def pt02_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 3)
    def pt03_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt03_data.setter
    @SupportsPacking.supports_io(0, 3)
    def pt03_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 4)
    def pt04_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt04_data.setter
    @SupportsPacking.supports_io(0, 4)
    def pt04_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 5)
    def pt05_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt05_data.setter
    @SupportsPacking.supports_io(0, 5)
    def pt05_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 6)
    def pt06_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt06_data.setter
    @SupportsPacking.supports_io(0, 6)
    def pt06_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 7)
    def pt07_data(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt07_data.setter
    @SupportsPacking.supports_io(0, 7)
    def pt07_data(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 8)
    def pt00_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt00_status.setter
    @SupportsPacking.supports_io(0, 8)
    def pt00_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 9)
    def pt01_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt01_status.setter
    @SupportsPacking.supports_io(0, 9)
    def pt01_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 10)
    def pt02_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt02_status.setter
    @SupportsPacking.supports_io(0, 10)
    def pt02_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 11)
    def pt03_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt03_status.setter
    @SupportsPacking.supports_io(0, 11)
    def pt03_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 12)
    def pt04_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt04_status.setter
    @SupportsPacking.supports_io(0, 12)
    def pt04_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 13)
    def pt05_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt05_status.setter
    @SupportsPacking.supports_io(0, 13)
    def pt05_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 14)
    def pt06_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt06_status.setter
    @SupportsPacking.supports_io(0, 14)
    def pt06_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 15)
    def pt07_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt07_status.setter
    @SupportsPacking.supports_io(0, 15)
    def pt07_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 16)
    def pt00_test_output_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt00_test_output_status.setter
    @SupportsPacking.supports_io(0, 16)
    def pt00_test_output_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 17)
    def pt01_test_output_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt01_test_output_status.setter
    @SupportsPacking.supports_io(0, 17)
    def pt01_test_output_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 18)
    def pt02_test_output_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt02_test_output_status.setter
    @SupportsPacking.supports_io(0, 18)
    def pt02_test_output_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 19)
    def pt03_test_output_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @pt03_test_output_status.setter
    @SupportsPacking.supports_io(0, 19)
    def pt03_test_output_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 24)
    def muting01_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @muting01_status.setter
    @SupportsPacking.supports_io(0, 24)
    def muting01_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 25)
    def muting03_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @muting03_status.setter
    @SupportsPacking.supports_io(0, 25)
    def muting03_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    @property
    @SupportsPacking.supports_io(0, 29)
    def input_power_status(self, word=None, bit=None, **__) -> bool:
        return self._read(word, bit)

    @input_power_status.setter
    @SupportsPacking.supports_io(0, 29)
    def input_power_status(self, word=None, bit=None, value=None) -> None:
        self._write(word=word, bit=bit, value=value)

    def __size__(self):
        return 1

    def __pack__(self):
        b = self._connection_status.__pack__()
        b.extend(super().__pack__())
        return b

    def __unpack__(self, data, offset=0):
        self._connection_status.__unpack__(data)
        self._data[0] = unpack_from('>i', data, offset+4)[0]


class AB_1734_IB8S_Safety5_O_0(object):
    """pyrox implimentation of a udt for pylogix to interact with
    """

    def __init__(self, data: bytearray):
        self._w0 = unpack_from('<i', data, 0)[0]

    @property
    def test00_data(self) -> bool:
        return read_bit(self._w0, 0)

    @property
    def test01_data(self) -> bool:
        return read_bit(self._w0, 1)

    @property
    def test02_data(self) -> bool:
        return read_bit(self._w0, 2)

    @property
    def test03_data(self) -> bool:
        return read_bit(self._w0, 3)

    def __size__(self):
        return 1
