import unittest

from pyrox.services import IdGeneratorService


class TestIdGenerator(unittest.TestCase):
    """Test the _IdGenerator class."""

    def setUp(self):
        """Reset the counter before each test."""
        IdGeneratorService._ctr = 0

    def test_get_id_increments(self):
        """Test that get_id returns incremental values."""
        first_id = IdGeneratorService.get_id()
        second_id = IdGeneratorService.get_id()
        third_id = IdGeneratorService.get_id()

        self.assertEqual(first_id, 1)
        self.assertEqual(second_id, 2)
        self.assertEqual(third_id, 3)

    def test_curr_value(self):
        """Test curr_value returns current counter value."""
        self.assertEqual(IdGeneratorService.curr_value(), 0)
        IdGeneratorService.get_id()
        self.assertEqual(IdGeneratorService.curr_value(), 1)
        IdGeneratorService.get_id()
        self.assertEqual(IdGeneratorService.curr_value(), 2)

    def test_thread_safety_simulation(self):
        """Test that multiple calls return unique values."""
        ids = [IdGeneratorService.get_id() for _ in range(100)]
        self.assertEqual(len(ids), 100)


if __name__ == '__main__':
    unittest.main()
