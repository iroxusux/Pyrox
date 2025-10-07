from pyrox.services.bit import set_bit, clear_bit


class TestBitOperations:
    def test_bit_operations(self):
        my_other_val = 0
        my_other_val = set_bit(my_other_val, 0)
        assert my_other_val == 1
        my_other_val = set_bit(my_other_val, 1)
        assert my_other_val == 3
        my_other_val = clear_bit(my_other_val, 0)
        assert my_other_val == 2
