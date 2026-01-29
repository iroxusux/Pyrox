"""Unit tests for network.py module."""

import unittest

from pyrox.models.network import Ipv4Address


class TestIpv4Address(unittest.TestCase):
    """Test cases for Ipv4Address class."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_ip_string = "192.168.1.1"
        self.valid_ip_bytes = b'\xc0\xa8\x01\x01'  # 192.168.1.1
        self.valid_ip_bytearray = bytearray([192, 168, 1, 1])
        self.valid_ip_memoryview = memoryview(b'\xc0\xa8\x01\x01')

    def test_init_with_valid_string(self):
        """Test initialization with valid string address."""
        ip = Ipv4Address(self.valid_ip_string)

        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertIsInstance(ip.octects, bytes)

    def test_init_with_valid_bytes(self):
        """Test initialization with valid bytes address."""
        ip = Ipv4Address(self.valid_ip_bytes)

        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertIsInstance(ip.octects, bytes)

    def test_init_with_valid_bytearray(self):
        """Test initialization with valid bytearray address."""
        ip = Ipv4Address(self.valid_ip_bytearray)

        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertIsInstance(ip.octects, bytes)

    def test_init_with_valid_memoryview(self):
        """Test initialization with valid memoryview address."""
        ip = Ipv4Address(self.valid_ip_memoryview)

        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertIsInstance(ip.octects, bytes)

    def test_init_with_edge_case_addresses(self):
        """Test initialization with edge case valid addresses."""
        # Test all zeros
        ip_zero = Ipv4Address("0.0.0.0")
        self.assertEqual(ip_zero.octects, b'\x00\x00\x00\x00')

        # Test all max values
        ip_max = Ipv4Address("255.255.255.255")
        self.assertEqual(ip_max.octects, b'\xff\xff\xff\xff')

        # Test localhost
        ip_localhost = Ipv4Address("127.0.0.1")
        self.assertEqual(ip_localhost.octects, b'\x7f\x00\x00\x01')

    def test_init_with_invalid_string_too_few_octets(self):
        """Test initialization with string having too few octets."""
        with self.assertRaises(ValueError) as context:
            Ipv4Address("192.168.1")

        self.assertIn("exactly 4 octets", str(context.exception))

    def test_init_with_invalid_string_too_many_octets(self):
        """Test initialization with string having too many octets."""
        with self.assertRaises(ValueError) as context:
            Ipv4Address("192.168.1.1.1")

        self.assertIn("exactly 4 octets", str(context.exception))

    def test_init_with_invalid_string_non_numeric_octets(self):
        """Test initialization with string having non-numeric octets."""
        with self.assertRaises(ValueError):
            Ipv4Address("192.168.abc.1")

    def test_init_with_invalid_string_octet_out_of_range(self):
        """Test initialization with string having octets out of valid range."""
        with self.assertRaises(ValueError):
            Ipv4Address("192.168.1.256")  # 256 > 255

        with self.assertRaises(ValueError):
            Ipv4Address("192.168.1.-1")  # Negative value

    def test_init_with_invalid_bytes_wrong_length(self):
        """Test initialization with bytes having wrong length."""
        with self.assertRaises(ValueError) as context:
            Ipv4Address(b'\xc0\xa8\x01')  # Only 3 bytes

        self.assertIn("exactly 4 octets", str(context.exception))

        with self.assertRaises(ValueError) as context:
            Ipv4Address(b'\xc0\xa8\x01\x01\x01')  # 5 bytes

        self.assertIn("exactly 4 octets", str(context.exception))

    def test_init_with_invalid_type(self):
        """Test initialization with invalid type."""
        with self.assertRaises(TypeError) as context:
            Ipv4Address(123)  # int  # type: ignore

        self.assertIn("address must be str, bytes, bytearray, or memoryview", str(context.exception))

        with self.assertRaises(TypeError) as context:
            Ipv4Address([192, 168, 1, 1])  # list # type: ignore

        self.assertIn("address must be str, bytes, bytearray, or memoryview", str(context.exception))

    def test_str_representation(self):
        """Test string representation of IPv4 address."""
        ip = Ipv4Address(self.valid_ip_string)

        self.assertEqual(str(ip), self.valid_ip_string)

    def test_str_representation_edge_cases(self):
        """Test string representation with edge case values."""
        ip_zero = Ipv4Address("0.0.0.0")
        self.assertEqual(str(ip_zero), "0.0.0.0")

        ip_max = Ipv4Address("255.255.255.255")
        self.assertEqual(str(ip_max), "255.255.255.255")

        ip_mixed = Ipv4Address("10.0.255.128")
        self.assertEqual(str(ip_mixed), "10.0.255.128")

    def test_repr_representation(self):
        """Test repr representation of IPv4 address."""
        ip = Ipv4Address(self.valid_ip_string)

        expected = f"Ipv4Address('{self.valid_ip_string}')"
        self.assertEqual(repr(ip), expected)

    def test_octects_property_getter(self):
        """Test octects property getter."""
        ip = Ipv4Address(self.valid_ip_string)

        octects = ip.octects
        self.assertEqual(octects, self.valid_ip_bytes)
        self.assertIsInstance(octects, bytes)

    def test_octects_property_setter_valid_bytes(self):
        """Test octects property setter with valid bytes."""
        ip = Ipv4Address("0.0.0.0")

        ip.octects = self.valid_ip_bytes
        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertEqual(str(ip), self.valid_ip_string)

    def test_octects_property_setter_valid_bytearray(self):
        """Test octects property setter with valid bytearray."""
        ip = Ipv4Address("0.0.0.0")

        ip.octects = self.valid_ip_bytearray
        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertEqual(str(ip), self.valid_ip_string)

    def test_octects_property_setter_valid_memoryview(self):
        """Test octects property setter with valid memoryview."""
        ip = Ipv4Address("0.0.0.0")

        ip.octects = self.valid_ip_memoryview
        self.assertEqual(ip.octects, self.valid_ip_bytes)
        self.assertEqual(str(ip), self.valid_ip_string)

    def test_octects_property_setter_invalid_type(self):
        """Test octects property setter with invalid type."""
        ip = Ipv4Address(self.valid_ip_string)

        with self.assertRaises(TypeError) as context:
            ip.octects = "192.168.1.1"  # string # type: ignore

        self.assertIn("octets must be bytes, bytearray, or memoryview", str(context.exception))

        with self.assertRaises(TypeError) as context:
            ip.octects = [192, 168, 1, 1]  # list # type: ignore

        self.assertIn("octets must be bytes, bytearray, or memoryview", str(context.exception))

    def test_octects_property_setter_invalid_length(self):
        """Test octects property setter with invalid length."""
        ip = Ipv4Address(self.valid_ip_string)

        with self.assertRaises(ValueError) as context:
            ip.octects = b'\xc0\xa8\x01'  # Only 3 bytes

        self.assertIn("exactly 4 octets", str(context.exception))

        with self.assertRaises(ValueError) as context:
            ip.octects = b'\xc0\xa8\x01\x01\x01'  # 5 bytes

        self.assertIn("exactly 4 octets", str(context.exception))

    def test_octects_immutability_after_creation(self):
        """Test that octects property creates a new bytes object."""
        ip = Ipv4Address(self.valid_ip_string)

        original_octects = ip.octects
        ip.octects = b'\x0a\x00\x00\x01'  # 10.0.0.1

        # Original octects should not be modified
        self.assertEqual(original_octects, self.valid_ip_bytes)
        self.assertEqual(ip.octects, b'\x0a\x00\x00\x01')

    def test_different_creation_methods_same_result(self):
        """Test that different creation methods produce same result."""
        ip_string = Ipv4Address("10.0.0.1")
        ip_bytes = Ipv4Address(b'\x0a\x00\x00\x01')
        ip_bytearray = Ipv4Address(bytearray([10, 0, 0, 1]))
        ip_memoryview = Ipv4Address(memoryview(b'\x0a\x00\x00\x01'))

        # All should have same octects
        self.assertEqual(ip_string.octects, ip_bytes.octects)
        self.assertEqual(ip_bytes.octects, ip_bytearray.octects)
        self.assertEqual(ip_bytearray.octects, ip_memoryview.octects)

        # All should have same string representation
        expected_str = "10.0.0.1"
        self.assertEqual(str(ip_string), expected_str)
        self.assertEqual(str(ip_bytes), expected_str)
        self.assertEqual(str(ip_bytearray), expected_str)
        self.assertEqual(str(ip_memoryview), expected_str)

    def test_common_ip_addresses(self):
        """Test common/well-known IP addresses."""
        test_cases = [
            ("127.0.0.1", b'\x7f\x00\x00\x01'),  # localhost
            ("0.0.0.0", b'\x00\x00\x00\x00'),    # any address
            ("255.255.255.255", b'\xff\xff\xff\xff'),  # broadcast
            ("192.168.0.1", b'\xc0\xa8\x00\x01'),  # common router IP
            ("10.0.0.1", b'\x0a\x00\x00\x01'),     # private network
            ("172.16.0.1", b'\xac\x10\x00\x01'),   # private network
            ("8.8.8.8", b'\x08\x08\x08\x08'),      # Google DNS
        ]

        for ip_str, expected_bytes in test_cases:
            with self.subTest(ip_address=ip_str):
                ip = Ipv4Address(ip_str)
                self.assertEqual(ip.octects, expected_bytes)
                self.assertEqual(str(ip), ip_str)

    def test_boundary_values(self):
        """Test boundary values for octets."""
        # Test minimum values
        ip_min = Ipv4Address("0.0.0.0")
        self.assertEqual(ip_min.octects, b'\x00\x00\x00\x00')

        # Test maximum values
        ip_max = Ipv4Address("255.255.255.255")
        self.assertEqual(ip_max.octects, b'\xff\xff\xff\xff')

        # Test mixed boundary values
        ip_mixed = Ipv4Address("0.255.0.255")
        self.assertEqual(ip_mixed.octects, b'\x00\xff\x00\xff')

    def test_string_with_leading_zeros(self):
        """Test string addresses with leading zeros."""
        # Note: Python's int() function handles leading zeros correctly
        ip = Ipv4Address("192.168.001.001")
        self.assertEqual(str(ip), "192.168.1.1")
        self.assertEqual(ip.octects, b'\xc0\xa8\x01\x01')

    def test_empty_string(self):
        """Test initialization with empty string."""
        with self.assertRaises(ValueError):
            Ipv4Address("")

    def test_none_value(self):
        """Test initialization with None value."""
        with self.assertRaises(TypeError):
            Ipv4Address(None)  # type: ignore

    def test_octects_modification_independence(self):
        """Test that modifying octects doesn't affect other instances."""
        ip1 = Ipv4Address("192.168.1.1")
        ip2 = Ipv4Address("10.0.0.1")

        _ = ip1.octects
        original_ip2_octects = ip2.octects

        # Modify ip1
        ip1.octects = b'\x0a\x0a\x0a\x0a'  # 10.10.10.10

        # ip2 should be unchanged
        self.assertEqual(ip2.octects, original_ip2_octects)
        self.assertEqual(str(ip2), "10.0.0.1")

        # ip1 should be changed
        self.assertEqual(ip1.octects, b'\x0a\x0a\x0a\x0a')
        self.assertEqual(str(ip1), "10.10.10.10")


if __name__ == '__main__':
    unittest.main()
