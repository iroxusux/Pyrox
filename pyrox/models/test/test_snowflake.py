"""Unit tests for the meta module."""

import pytest

from pyrox.models.snowflake import SnowFlake


class TestSnowFlake:
    """Test the SnowFlake class."""

    def test_equality(self):
        """Test SnowFlake equality comparison."""
        sf1 = SnowFlake()
        sf2 = SnowFlake()

        # Same object should be equal to itself
        assert sf1 == sf1

        # Different objects should not be equal
        assert sf1 != sf2

        # Test with different types
        assert sf1 != "not a snowflake"
        assert sf1 != 42

    def test_hash(self):
        """Test SnowFlake hashing."""
        sf1 = SnowFlake()
        sf2 = SnowFlake()

        # Hash should be based on ID
        assert hash(sf1) == hash(sf1.id)
        assert hash(sf1) != hash(sf2)

        # Should be usable in sets and dicts
        snowflake_set = {sf1, sf2}
        assert len(snowflake_set) == 2

    def test_string_representation(self):
        """Test SnowFlake string representation."""
        sf = SnowFlake()
        assert str(sf) == str(sf.id)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
