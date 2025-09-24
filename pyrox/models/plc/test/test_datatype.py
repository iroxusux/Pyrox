"""Unit tests for the datatype module."""

import pytest
from unittest.mock import Mock, patch

from pyrox.models.plc.datatype import Datatype, DatatypeMember
from pyrox.models.plc import meta as plc_meta


class TestDatatypeMember:
    """Test cases for DatatypeMember class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_controller = Mock()
        self.mock_parent_datatype = Mock(spec=Datatype)

        self.sample_member_data = {
            '@Name': 'TestMember',
            '@DataType': 'BOOL',
            '@Dimension': '0',
            '@Hidden': 'false',
            'Description': 'Test member description'
        }

    def test_initialization(self):
        """Test DatatypeMember initialization."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.name == 'TestMember'
        assert member.controller is self.mock_controller
        assert member._parent_datatype is self.mock_parent_datatype

    def test_datatype_property(self):
        """Test datatype property getter."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.datatype == 'BOOL'

    def test_dimension_property(self):
        """Test dimension property getter."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.dimension == '0'

    def test_hidden_property(self):
        """Test hidden property getter."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.hidden == 'false'

    def test_hidden_property_true(self):
        """Test hidden property when set to true."""
        member_data = self.sample_member_data.copy()
        member_data['@Hidden'] = 'true'

        member = DatatypeMember(
            l5x_meta_data=member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.hidden == 'true'

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_is_atomic_true_for_atomic_datatype(self):
        """Test is_atomic property returns True for atomic datatypes."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.is_atomic is True

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['DINT', 'REAL'])
    def test_is_atomic_false_for_non_atomic_datatype(self):
        """Test is_atomic property returns False for non-atomic datatypes."""
        member_data = self.sample_member_data.copy()
        member_data['@DataType'] = 'CustomDatatype'

        member = DatatypeMember(
            l5x_meta_data=member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.is_atomic is False

    def test_parent_datatype_property(self):
        """Test parent_datatype property getter."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.parent_datatype is self.mock_parent_datatype

    def test_different_datatypes(self):
        """Test member with different datatypes."""
        datatypes = ['DINT', 'REAL', 'STRING', 'CustomType']

        for datatype in datatypes:
            member_data = self.sample_member_data.copy()
            member_data['@DataType'] = datatype

            member = DatatypeMember(
                l5x_meta_data=member_data,
                parent_datatype=self.mock_parent_datatype,
                controller=self.mock_controller
            )

            assert member.datatype == datatype

    def test_inheritance_from_named_plc_object(self):
        """Test that DatatypeMember inherits from NamedPlcObject."""
        member = DatatypeMember(
            l5x_meta_data=self.sample_member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert isinstance(member, plc_meta.NamedPlcObject)
        assert hasattr(member, 'name')
        assert hasattr(member, 'description')


class TestDatatype:
    """Test cases for Datatype class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_controller = Mock()

        # Mock controller.datatypes for endpoint operand testing
        self.mock_controller.datatypes = {}

        self.sample_datatype_data = {
            '@Name': 'TestDatatype',
            '@Family': 'NoFamily',
            '@Class': 'User',
            'Description': 'Test datatype description',
            'Members': {
                'Member': [
                    {
                        '@Name': 'BoolMember',
                        '@DataType': 'BOOL',
                        '@Dimension': '0',
                        '@Hidden': 'false'
                    },
                    {
                        '@Name': 'IntMember',
                        '@DataType': 'DINT',
                        '@Dimension': '0',
                        '@Hidden': 'false'
                    }
                ]
            }
        }

    def test_initialization_with_members(self):
        """Test Datatype initialization with members."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        assert datatype.name == 'TestDatatype'
        assert datatype.controller is self.mock_controller
        assert len(datatype._members) == 2
        assert isinstance(datatype._members[0], DatatypeMember)
        assert isinstance(datatype._members[1], DatatypeMember)

    def test_initialization_empty_members(self):
        """Test Datatype initialization with empty members."""
        datatype_data = self.sample_datatype_data.copy()
        datatype_data['Members'] = {'Member': []}

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        assert len(datatype._members) == 0

    def test_initialization_no_members_key(self):
        """Test Datatype initialization without Members key."""
        datatype_data = self.sample_datatype_data.copy()
        del datatype_data['Members']

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        # Should create empty Members structure
        assert datatype['Members'] == {'Member': []}
        assert len(datatype._members) == 0

    def test_dict_key_order(self):
        """Test dict_key_order property."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        expected_order = [
            '@Name',
            '@Family',
            '@Class',
            'Description',
            'Members',
        ]

        assert datatype.dict_key_order == expected_order

    def test_family_property(self):
        """Test family property getter."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        assert datatype.family == 'NoFamily'

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_is_atomic_false_for_user_datatype(self):
        """Test is_atomic property returns False for user datatypes."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        assert datatype.is_atomic is False

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL', 'TestDatatype'])
    def test_is_atomic_true_for_atomic_datatype(self):
        """Test is_atomic property returns True for atomic datatypes."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        assert datatype.is_atomic is True

    def test_members_property(self):
        """Test members property getter."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        members = datatype.members
        assert len(members) == 2
        assert members[0].name == 'BoolMember'
        assert members[1].name == 'IntMember'
        assert all(isinstance(member, DatatypeMember) for member in members)

    def test_raw_members_property_with_list(self):
        """Test raw_members property when Members contains a list."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        raw_members = datatype.raw_members
        assert isinstance(raw_members, list)
        assert len(raw_members) == 2
        assert raw_members[0]['@Name'] == 'BoolMember'
        assert raw_members[1]['@Name'] == 'IntMember'

    def test_raw_members_property_with_single_member(self):
        """Test raw_members property when Members contains a single member."""
        datatype_data = self.sample_datatype_data.copy()
        datatype_data['Members'] = {
            'Member': {
                '@Name': 'SingleMember',
                '@DataType': 'BOOL',
                '@Dimension': '0',
                '@Hidden': 'false'
            }
        }

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        raw_members = datatype.raw_members
        assert isinstance(raw_members, list)
        assert len(raw_members) == 1
        assert raw_members[0]['@Name'] == 'SingleMember'

        # Verify it was converted to list in meta_data
        assert isinstance(datatype['Members']['Member'], list)

    def test_raw_members_property_creates_structure_when_none(self):
        """Test raw_members property creates structure when Members is None."""
        datatype_data = self.sample_datatype_data.copy()
        datatype_data['Members'] = None

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        raw_members = datatype.raw_members
        assert isinstance(raw_members, list)
        assert len(raw_members) == 0

        # Verify structure was created
        assert datatype['Members'] == {'Member': []}

    def test_raw_members_property_modifiable(self):
        """Test that raw_members property returns a modifiable reference."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        raw_members = datatype.raw_members
        original_length = len(raw_members)

        # Add a new member
        new_member = {
            '@Name': 'NewMember',
            '@DataType': 'REAL',
            '@Dimension': '0',
            '@Hidden': 'false'
        }
        raw_members.append(new_member)

        # Verify it was added to the original structure
        assert len(datatype.raw_members) == original_length + 1
        assert datatype.raw_members[-1]['@Name'] == 'NewMember'

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_endpoint_operands_atomic_datatype(self):
        """Test endpoint_operands for atomic datatype."""
        # Create an atomic datatype
        atomic_data = self.sample_datatype_data.copy()
        atomic_data['@Name'] = 'BOOL'  # Make it atomic

        datatype = Datatype(
            meta_data=atomic_data,
            controller=self.mock_controller
        )

        # Mock is_atomic to return True
        operands = datatype.endpoint_operands
        assert operands == ['']

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_endpoint_operands_simple_members(self):
        """Test endpoint_operands for datatype with atomic members."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        operands = datatype.endpoint_operands
        expected = ['.BoolMember', '.IntMember']
        assert operands == expected

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_endpoint_operands_hidden_members_excluded(self):
        """Test endpoint_operands excludes hidden members."""
        datatype_data = self.sample_datatype_data.copy()
        datatype_data['Members']['Member'][0]['@Hidden'] = 'true'  # Hide first member

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        operands = datatype.endpoint_operands
        expected = ['.IntMember']  # Only the non-hidden member
        assert operands == expected

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_endpoint_operands_nested_datatypes(self):
        """Test endpoint_operands for datatype with nested custom datatypes."""
        # Create a nested datatype
        nested_datatype = Mock()
        nested_datatype.endpoint_operands = ['.NestedBool', '.NestedInt']

        # Set up controller to return the nested datatype
        self.mock_controller.datatypes = {'CustomType': nested_datatype}

        # Create datatype with custom member
        datatype_data = self.sample_datatype_data.copy()
        datatype_data['Members']['Member'].append({
            '@Name': 'CustomMember',
            '@DataType': 'CustomType',
            '@Dimension': '0',
            '@Hidden': 'false'
        })

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        operands = datatype.endpoint_operands
        expected = [
            '.BoolMember',
            '.IntMember',
            '.CustomMember.NestedBool',
            '.CustomMember.NestedInt'
        ]
        assert operands == expected

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_endpoint_operands_unknown_datatype(self):
        """Test endpoint_operands when member datatype is not found in controller."""
        # Create datatype with unknown member type
        datatype_data = self.sample_datatype_data.copy()
        datatype_data['Members']['Member'].append({
            '@Name': 'UnknownMember',
            '@DataType': 'UnknownType',
            '@Dimension': '0',
            '@Hidden': 'false'
        })

        # Controller doesn't have the unknown datatype
        self.mock_controller.datatypes = {}

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        operands = datatype.endpoint_operands
        expected = ['.BoolMember', '.IntMember']  # Unknown member is skipped
        assert operands == expected

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_endpoint_operands_caching(self):
        """Test that endpoint_operands are cached after first calculation."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        # First call should calculate
        operands1 = datatype.endpoint_operands

        # Second call should return cached result
        operands2 = datatype.endpoint_operands

        assert operands1 is operands2  # Should be the same object (cached)
        assert operands1 == ['.BoolMember', '.IntMember']

    def test_inheritance_from_named_plc_object(self):
        """Test that Datatype inherits from NamedPlcObject."""
        datatype = Datatype(
            meta_data=self.sample_datatype_data,
            controller=self.mock_controller
        )

        assert isinstance(datatype, plc_meta.NamedPlcObject)
        assert hasattr(datatype, 'name')
        assert hasattr(datatype, 'description')


class TestDatatypeMemberEdgeCases:
    """Test edge cases and error conditions for DatatypeMember."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()
        self.mock_parent_datatype = Mock(spec=Datatype)

    def test_member_with_missing_optional_fields(self):
        """Test member with missing optional fields."""
        minimal_data = {
            '@Name': 'MinimalMember',
            '@DataType': 'BOOL'
        }

        member = DatatypeMember(
            l5x_meta_data=minimal_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.name == 'MinimalMember'
        assert member.datatype == 'BOOL'

        # These should NOT raise KeyError if not present
        _ = member.dimension
        _ = member.hidden

    def test_member_datatype_case_sensitivity(self):
        """Test that datatype property is case sensitive."""
        member_data = {
            '@Name': 'CaseSensitiveMember',
            '@DataType': 'bool',  # lowercase
            '@Dimension': '0',
            '@Hidden': 'false'
        }

        member = DatatypeMember(
            l5x_meta_data=member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.datatype == 'bool'  # Should preserve case

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL'])
    def test_is_atomic_case_sensitive(self):
        """Test that is_atomic check is case sensitive."""
        member_data = {
            '@Name': 'CaseMember',
            '@DataType': 'bool',  # lowercase, not in ATOMIC_DATATYPES
            '@Dimension': '0',
            '@Hidden': 'false'
        }

        member = DatatypeMember(
            l5x_meta_data=member_data,
            parent_datatype=self.mock_parent_datatype,
            controller=self.mock_controller
        )

        assert member.is_atomic is False  # 'bool' != 'BOOL'


class TestDatatypeEdgeCases:
    """Test edge cases and error conditions for Datatype."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()
        self.mock_controller.datatypes = {}

    def test_datatype_with_no_family(self):
        """Test datatype with missing family field."""
        datatype_data = {
            '@Name': 'NoFamilyDatatype',
            '@Class': 'User',
            'Description': 'Test datatype',
            'Members': {'Member': []}
        }

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )
        # Should not raise error, family defaults to None
        _ = datatype.family

    def test_empty_members_structure_handling(self):
        """Test various empty members structure scenarios."""
        scenarios = [
            {'Members': None},
            {'Members': {}},
            {'Members': {'Member': None}},
            {'Members': {'Member': []}},
            {}  # No Members key at all
        ]

        for scenario in scenarios:
            datatype_data = {
                '@Name': 'EmptyDatatype',
                '@Family': 'NoFamily',
                '@Class': 'User'
            }
            datatype_data.update(scenario)

            datatype = Datatype(
                meta_data=datatype_data,
                controller=self.mock_controller
            )

            # Should always result in empty list
            assert datatype.raw_members == []
            assert len(datatype.members) == 0

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', [])
    def test_endpoint_operands_no_atomic_types(self):
        """Test endpoint_operands when no atomic types are defined."""
        datatype_data = {
            '@Name': 'TestDatatype',
            '@Family': 'NoFamily',
            '@Class': 'User',
            'Members': {
                'Member': [
                    {
                        '@Name': 'Member1',
                        '@DataType': 'BOOL',
                        '@Hidden': 'false'
                    }
                ]
            }
        }

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        # No atomic types defined, so member is not atomic
        # Controller has no datatypes, so it will be skipped
        operands = datatype.endpoint_operands
        assert operands == []

    def test_circular_reference_protection(self):
        """Test protection against circular references in nested datatypes."""
        # Create a datatype that references itself
        circular_datatype = Mock()
        circular_datatype.endpoint_operands = ['.SelfRef']

        self.mock_controller.datatypes = {'SelfType': circular_datatype}

        datatype_data = {
            '@Name': 'SelfType',
            '@Family': 'NoFamily',
            '@Class': 'User',
            'Members': {
                'Member': [
                    {
                        '@Name': 'SelfMember',
                        '@DataType': 'SelfType',
                        '@Hidden': 'false'
                    }
                ]
            }
        }

        datatype = Datatype(
            meta_data=datatype_data,
            controller=self.mock_controller
        )

        # This should work without infinite recursion
        # The mock will return a fixed value
        operands = datatype.endpoint_operands
        assert operands == ['.SelfMember.SelfRef']


class TestDatatypeIntegration:
    """Integration tests for Datatype and DatatypeMember."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()

        # Create a complex nested structure
        self.nested_datatype_data = {
            '@Name': 'NestedDatatype',
            '@Family': 'NoFamily',
            '@Class': 'User',
            'Description': 'Nested datatype',
            'Members': {
                'Member': [
                    {
                        '@Name': 'NestedBool',
                        '@DataType': 'BOOL',
                        '@Dimension': '0',
                        '@Hidden': 'false'
                    },
                    {
                        '@Name': 'NestedReal',
                        '@DataType': 'REAL',
                        '@Dimension': '0',
                        '@Hidden': 'false'
                    }
                ]
            }
        }

        self.complex_datatype_data = {
            '@Name': 'ComplexDatatype',
            '@Family': 'StringFamily',
            '@Class': 'User',
            'Description': 'Complex datatype with nested members',
            'Members': {
                'Member': [
                    {
                        '@Name': 'SimpleBool',
                        '@DataType': 'BOOL',
                        '@Dimension': '0',
                        '@Hidden': 'false',
                        'Description': 'Simple boolean member'
                    },
                    {
                        '@Name': 'HiddenInt',
                        '@DataType': 'DINT',
                        '@Dimension': '0',
                        '@Hidden': 'true',
                        'Description': 'Hidden integer member'
                    },
                    {
                        '@Name': 'NestedMember',
                        '@DataType': 'NestedDatatype',
                        '@Dimension': '0',
                        '@Hidden': 'false',
                        'Description': 'Nested custom datatype member'
                    },
                    {
                        '@Name': 'ArrayMember',
                        '@DataType': 'REAL',
                        '@Dimension': '10',
                        '@Hidden': 'false',
                        'Description': 'Array member'
                    }
                ]
            }
        }

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL', 'STRING'])
    def test_complex_datatype_creation(self):
        """Test creating a complex datatype with various member types."""
        # Set up nested datatype in controller
        nested_datatype = Datatype(
            meta_data=self.nested_datatype_data,
            controller=self.mock_controller
        )

        self.mock_controller.datatypes = {'NestedDatatype': nested_datatype}

        # Create complex datatype
        complex_datatype = Datatype(
            meta_data=self.complex_datatype_data,
            controller=self.mock_controller
        )

        # Test basic properties
        assert complex_datatype.name == 'ComplexDatatype'
        assert complex_datatype.family == 'StringFamily'
        assert not complex_datatype.is_atomic

        # Test members
        members = complex_datatype.members
        assert len(members) == 4

        # Test individual members
        assert members[0].name == 'SimpleBool'
        assert members[0].datatype == 'BOOL'
        assert members[0].hidden == 'false'
        assert members[0].is_atomic is True

        assert members[1].name == 'HiddenInt'
        assert members[1].datatype == 'DINT'
        assert members[1].hidden == 'true'
        assert members[1].is_atomic is True

        assert members[2].name == 'NestedMember'
        assert members[2].datatype == 'NestedDatatype'
        assert members[2].hidden == 'false'
        assert members[2].is_atomic is False

        assert members[3].name == 'ArrayMember'
        assert members[3].datatype == 'REAL'
        assert members[3].dimension == '10'

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL', 'STRING'])
    def test_complex_endpoint_operands(self):
        """Test endpoint operands for complex nested structure."""
        # Set up nested datatype
        nested_datatype = Datatype(
            meta_data=self.nested_datatype_data,
            controller=self.mock_controller
        )

        self.mock_controller.datatypes = {'NestedDatatype': nested_datatype}

        # Create complex datatype
        complex_datatype = Datatype(
            meta_data=self.complex_datatype_data,
            controller=self.mock_controller
        )

        operands = complex_datatype.endpoint_operands
        expected = [
            '.SimpleBool',  # Atomic, not hidden
            # '.HiddenInt' is skipped because it's hidden
            '.NestedMember.NestedBool',  # From nested datatype
            '.NestedMember.NestedReal',  # From nested datatype
            '.ArrayMember'  # Atomic array member
        ]

        assert operands == expected

    @patch('pyrox.models.plc.meta.ATOMIC_DATATYPES', ['BOOL', 'DINT', 'REAL'])
    def test_member_parent_reference(self):
        """Test that members correctly reference their parent datatype."""
        datatype = Datatype(
            meta_data=self.complex_datatype_data,
            controller=self.mock_controller
        )

        for member in datatype.members:
            assert member.parent_datatype is datatype
            assert member.controller is datatype.controller

    def test_datatype_modification_through_raw_members(self):
        """Test modifying datatype structure through raw_members."""
        datatype = Datatype(
            meta_data=self.complex_datatype_data,
            controller=self.mock_controller
        )

        original_member_count = len(datatype.members)

        # Add a new member through raw_members
        new_member_data = {
            '@Name': 'NewMember',
            '@DataType': 'STRING',
            '@Dimension': '0',
            '@Hidden': 'false',
            'Description': 'Dynamically added member'
        }

        datatype.raw_members.append(new_member_data)

        # The _members list is created during initialization and won't update
        # automatically, but raw_members should reflect the change
        assert len(datatype.raw_members) == original_member_count + 1
        assert datatype.raw_members[-1]['@Name'] == 'NewMember'

    def test_endpoint_operands_performance_caching(self):
        """Test that endpoint operands calculation is cached for performance."""
        # Create a complex structure that would be expensive to recalculate
        nested_datatype = Datatype(
            meta_data=self.nested_datatype_data,
            controller=self.mock_controller
        )

        self.mock_controller.datatypes = {'NestedDatatype': nested_datatype}

        datatype = Datatype(
            meta_data=self.complex_datatype_data,
            controller=self.mock_controller
        )

        # First call should calculate and cache
        operands1 = datatype.endpoint_operands

        # Modify the mock to return different values
        nested_datatype._endpoint_operands = ['.Modified']

        # Second call should return cached result (not recalculate)
        operands2 = datatype.endpoint_operands

        assert operands1 is operands2  # Same object reference (cached)
        # Should not reflect the mock modification


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
