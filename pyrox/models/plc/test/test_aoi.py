"""Unit tests for the aoi module."""

import pytest
from unittest.mock import Mock, patch

from pyrox.models.plc.aoi import AddOnInstruction
from pyrox.models.plc import meta as plc_meta
from pyrox.models.abc.meta import EnforcesNaming


class TestAddOnInstruction:
    """Test cases for AddOnInstruction class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Sample meta data that matches expected AOI structure
        self.sample_meta_data = {
            '@Name': 'TestAOI',
            '@Class': 'User',
            '@Revision': '1.0',
            '@ExecutePrescan': 'false',
            '@ExecutePostscan': 'false',
            '@ExecuteEnableInFalse': 'false',
            '@CreatedDate': '2023-01-01T10:00:00.000Z',
            '@CreatedBy': 'TestUser',
            '@EditedDate': '2023-01-01T10:00:00.000Z',
            '@EditedBy': 'TestUser',
            '@SoftwareRevision': '33.00',
            '@RevisionExtension': '1.0',
            'Description': 'Test AOI Description',
            'RevisionNote': 'Initial version',
            'Parameters': {
                'Parameter': [
                    {
                        '@Name': 'Input1',
                        '@TagType': 'Base',
                        '@DataType': 'BOOL',
                        '@Usage': 'Input'
                    }
                ]
            },
            'LocalTags': {
                'LocalTag': [
                    {
                        '@Name': 'LocalVar1',
                        '@DataType': 'BOOL'
                    }
                ]
            },
            'Routines': {
                'Routine': [
                    {
                        '@Name': 'Logic',
                        '@Type': 'RLL'
                    }
                ]
            }
        }

        self.mock_controller = Mock()

    @patch('pyrox.models.plc.aoi.l5x_dict_from_file')
    def test_initialization_default_meta_data(self, mock_l5x_dict):
        """Test initialization with default meta data from file."""
        mock_l5x_dict.return_value = {
            'AddOnInstructionDefinition': self.sample_meta_data
        }

        aoi = AddOnInstruction()

        mock_l5x_dict.assert_called_once_with(plc_meta.PLC_AOI_FILE)
        assert aoi.name == 'TestAOI'
        assert aoi.revision == '1.0'

    def test_initialization_with_meta_data(self):
        """Test initialization with provided meta data."""
        aoi = AddOnInstruction(
            meta_data=self.sample_meta_data,
            controller=self.mock_controller
        )

        assert aoi.name == 'TestAOI'
        assert aoi.revision == '1.0'
        assert aoi.controller is self.mock_controller

    def test_initialization_with_revision_extension_replacement(self):
        """Test that revision extension '<' characters are replaced during init."""
        meta_data_with_brackets = self.sample_meta_data.copy()
        meta_data_with_brackets['@RevisionExtension'] = 'v1.0<test>'

        aoi = AddOnInstruction(meta_data=meta_data_with_brackets)

        # Should trigger setter logic to replace '<' with '&lt;'
        assert aoi.revision_extension == 'v1.0&lt;test>'

    def test_dict_key_order(self):
        """Test that dict_key_order returns correct order."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        expected_order = [
            '@Name',
            '@Class',
            '@Revision',
            '@ExecutePrescan',
            '@ExecutePostscan',
            '@ExecuteEnableInFalse',
            '@CreatedDate',
            '@CreatedBy',
            '@EditedDate',
            '@EditedBy',
            '@SoftwareRevision',
            'Description',
            'RevisionNote',
            'Parameters',
            'LocalTags',
            'Routines',
        ]

        assert aoi.dict_key_order == expected_order

    def test_revision_property_getter(self):
        """Test revision property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.revision == '1.0'

    def test_revision_property_setter_valid(self):
        """Test revision property setter with valid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.revision = '2.1'
        assert aoi.revision == '2.1'
        assert aoi['@Revision'] == '2.1'

        aoi.revision = '10.25.3'
        assert aoi.revision == '10.25.3'

    def test_revision_property_setter_invalid(self):
        """Test revision property setter with invalid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.revision = 'invalid_revision'

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.revision = 'v1.2.3'

    def test_execute_prescan_property_getter(self):
        """Test execute_prescan property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.execute_prescan == 'false'

    def test_execute_prescan_property_setter_string(self):
        """Test execute_prescan property setter with string values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.execute_prescan = 'true'
        assert aoi.execute_prescan == 'true'
        assert aoi['@ExecutePrescan'] == 'true'

        aoi.execute_prescan = 'false'
        assert aoi.execute_prescan == 'false'

    def test_execute_prescan_property_setter_bool(self):
        """Test execute_prescan property setter with boolean values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.execute_prescan = True
        assert aoi.execute_prescan == 'true'

        aoi.execute_prescan = False
        assert aoi.execute_prescan == 'false'

    def test_execute_prescan_property_setter_invalid(self):
        """Test execute_prescan property setter with invalid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.execute_prescan = 'invalid'

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.execute_prescan = 'True'  # Case sensitive

    def test_execute_postscan_property_getter(self):
        """Test execute_postscan property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.execute_postscan == 'false'

    def test_execute_postscan_property_setter_string(self):
        """Test execute_postscan property setter with string values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.execute_postscan = 'true'
        assert aoi.execute_postscan == 'true'
        assert aoi['@ExecutePostscan'] == 'true'

    def test_execute_postscan_property_setter_bool(self):
        """Test execute_postscan property setter with boolean values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.execute_postscan = True
        assert aoi.execute_postscan == 'true'

        aoi.execute_postscan = False
        assert aoi.execute_postscan == 'false'

    def test_execute_postscan_property_setter_invalid(self):
        """Test execute_postscan property setter with invalid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.execute_postscan = 'yes'

    def test_execute_enable_in_false_property_getter(self):
        """Test execute_enable_in_false property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.execute_enable_in_false == 'false'

    def test_execute_enable_in_false_property_setter_string(self):
        """Test execute_enable_in_false property setter with string values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.execute_enable_in_false = 'true'
        assert aoi.execute_enable_in_false == 'true'
        assert aoi['@ExecuteEnableInFalse'] == 'true'

    def test_execute_enable_in_false_property_setter_bool(self):
        """Test execute_enable_in_false property setter with boolean values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.execute_enable_in_false = True
        assert aoi.execute_enable_in_false == 'true'

        aoi.execute_enable_in_false = False
        assert aoi.execute_enable_in_false == 'false'

    def test_execute_enable_in_false_property_setter_invalid(self):
        """Test execute_enable_in_false property setter with invalid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.execute_enable_in_false = '1'

    def test_read_only_properties(self):
        """Test read-only properties."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        assert aoi.created_date == '2023-01-01T10:00:00.000Z'
        assert aoi.created_by == 'TestUser'
        assert aoi.edited_date == '2023-01-01T10:00:00.000Z'
        assert aoi.edited_by == 'TestUser'

    def test_software_revision_property_getter(self):
        """Test software_revision property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.software_revision == '33.00'

    def test_software_revision_property_setter_valid(self):
        """Test software_revision property setter with valid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.software_revision = '34.00'
        assert aoi.software_revision == '34.00'
        assert aoi['@SoftwareRevision'] == '34.00'

    def test_software_revision_property_setter_invalid(self):
        """Test software_revision property setter with invalid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(EnforcesNaming.InvalidNamingException):
            aoi.software_revision = 'invalid_version'

    def test_revision_extension_property_getter(self):
        """Test revision_extension property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.revision_extension == '1.0'

    def test_revision_extension_property_setter_valid(self):
        """Test revision_extension property setter with valid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.revision_extension = 'v2.0'
        assert aoi.revision_extension == 'v2.0'
        assert aoi['@RevisionExtension'] == 'v2.0'

    def test_revision_extension_property_setter_with_brackets(self):
        """Test revision_extension property setter replaces '<' characters."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.revision_extension = 'v1.0<beta>'
        assert aoi.revision_extension == 'v1.0&lt;beta>'
        assert aoi['@RevisionExtension'] == 'v1.0&lt;beta>'

        aoi.revision_extension = '<<test>>'
        assert aoi.revision_extension == '&lt;&lt;test>>'

    def test_revision_extension_property_setter_invalid(self):
        """Test revision_extension property setter with invalid types."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(ValueError, match="Revision extension must be a string!"):
            aoi.revision_extension = 123

        with pytest.raises(ValueError, match="Revision extension must be a string!"):
            aoi.revision_extension = None

    def test_revision_note_property_getter(self):
        """Test revision_note property getter."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)
        assert aoi.revision_note == 'Initial version'

    def test_revision_note_property_setter_valid(self):
        """Test revision_note property setter with valid values."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        aoi.revision_note = 'Updated version'
        assert aoi.revision_note == 'Updated version'
        assert aoi['RevisionNote'] == 'Updated version'

        aoi.revision_note = ''
        assert aoi.revision_note == ''

    def test_revision_note_property_setter_invalid(self):
        """Test revision_note property setter with invalid types."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        with pytest.raises(ValueError, match="Revision note must be a string!"):
            aoi.revision_note = 123

        with pytest.raises(ValueError, match="Revision note must be a string!"):
            aoi.revision_note = None

    def test_parameters_property_with_list(self):
        """Test parameters property when Parameters contains a list."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        parameters = aoi.parameters
        assert isinstance(parameters, list)
        assert len(parameters) == 1
        assert parameters[0]['@Name'] == 'Input1'

    def test_parameters_property_with_single_item(self):
        """Test parameters property when Parameters contains a single item."""
        meta_data = self.sample_meta_data.copy()
        meta_data['Parameters'] = {
            'Parameter': {
                '@Name': 'SingleInput',
                '@TagType': 'Base',
                '@DataType': 'BOOL',
                '@Usage': 'Input'
            }
        }

        aoi = AddOnInstruction(meta_data=meta_data)

        parameters = aoi.parameters
        assert isinstance(parameters, list)
        assert len(parameters) == 1
        assert parameters[0]['@Name'] == 'SingleInput'

    def test_parameters_property_empty(self):
        """Test parameters property when Parameters is empty or None."""
        meta_data = self.sample_meta_data.copy()
        meta_data['Parameters'] = None

        aoi = AddOnInstruction(meta_data=meta_data)

        parameters = aoi.parameters
        assert isinstance(parameters, list)
        assert len(parameters) == 0

    def test_local_tags_property_with_list(self):
        """Test local_tags property when LocalTags contains a list."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        local_tags = aoi.local_tags
        assert isinstance(local_tags, list)
        assert len(local_tags) == 1
        assert local_tags[0]['@Name'] == 'LocalVar1'

    def test_local_tags_property_with_single_item(self):
        """Test local_tags property when LocalTags contains a single item."""
        meta_data = self.sample_meta_data.copy()
        meta_data['LocalTags'] = {
            'LocalTag': {
                '@Name': 'SingleLocalVar',
                '@DataType': 'DINT'
            }
        }

        aoi = AddOnInstruction(meta_data=meta_data)

        local_tags = aoi.local_tags
        assert isinstance(local_tags, list)
        assert len(local_tags) == 1
        assert local_tags[0]['@Name'] == 'SingleLocalVar'

    def test_local_tags_property_empty(self):
        """Test local_tags property when LocalTags is empty or None."""
        meta_data = self.sample_meta_data.copy()
        meta_data['LocalTags'] = None

        aoi = AddOnInstruction(meta_data=meta_data)

        local_tags = aoi.local_tags
        assert isinstance(local_tags, list)
        assert len(local_tags) == 0

    def test_raw_tags_property_with_existing_list(self):
        """Test raw_tags property when LocalTags already contains a list."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        raw_tags = aoi.raw_tags
        assert isinstance(raw_tags, list)
        assert len(raw_tags) == 1
        assert raw_tags[0]['@Name'] == 'LocalVar1'

        # Verify the structure is maintained in meta_data
        assert isinstance(aoi['LocalTags']['LocalTag'], list)

    def test_raw_tags_property_with_single_item(self):
        """Test raw_tags property when LocalTags contains a single item."""
        meta_data = self.sample_meta_data.copy()
        meta_data['LocalTags'] = {
            'LocalTag': {
                '@Name': 'SingleLocalVar',
                '@DataType': 'DINT'
            }
        }

        aoi = AddOnInstruction(meta_data=meta_data)

        raw_tags = aoi.raw_tags
        assert isinstance(raw_tags, list)
        assert len(raw_tags) == 1
        assert raw_tags[0]['@Name'] == 'SingleLocalVar'

        # Verify it was converted to list in meta_data
        assert isinstance(aoi['LocalTags']['LocalTag'], list)

    def test_raw_tags_property_empty_creates_structure(self):
        """Test raw_tags property creates structure when LocalTags is None."""
        meta_data = self.sample_meta_data.copy()
        meta_data['LocalTags'] = None

        aoi = AddOnInstruction(meta_data=meta_data)

        raw_tags = aoi.raw_tags
        assert isinstance(raw_tags, list)
        assert len(raw_tags) == 0

        # Verify structure was created
        assert aoi['LocalTags'] == {'LocalTag': []}
        assert isinstance(aoi['LocalTags']['LocalTag'], list)

    def test_raw_tags_property_modifiable(self):
        """Test that raw_tags property returns a modifiable reference."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        raw_tags = aoi.raw_tags
        original_length = len(raw_tags)

        # Add a new tag
        new_tag = {
            '@Name': 'NewLocalVar',
            '@DataType': 'BOOL'
        }
        raw_tags.append(new_tag)

        # Verify it was added to the original structure
        assert len(aoi.raw_tags) == original_length + 1
        assert aoi.raw_tags[-1]['@Name'] == 'NewLocalVar'


class TestAddOnInstructionInheritance:
    """Test AddOnInstruction inheritance from ContainsRoutines."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_meta_data = {
            '@Name': 'TestAOI',
            '@Class': 'User',
            '@Revision': '1.0',
            '@ExecutePrescan': 'false',
            '@ExecutePostscan': 'false',
            '@ExecuteEnableInFalse': 'false',
            '@CreatedDate': '2023-01-01T10:00:00.000Z',
            '@CreatedBy': 'TestUser',
            '@EditedDate': '2023-01-01T10:00:00.000Z',
            '@EditedBy': 'TestUser',
            '@SoftwareRevision': '33.00',
            '@RevisionExtension': '1.0',
            'Description': 'Test AOI Description',
            'RevisionNote': 'Initial version',
            'Parameters': {'Parameter': []},
            'LocalTags': {'LocalTag': []},
            'Routines': {
                'Routine': [
                    {
                        '@Name': 'Logic',
                        '@Type': 'RLL'
                    },
                    {
                        '@Name': 'EnableInFalse',
                        '@Type': 'RLL'
                    }
                ]
            }
        }

    def test_inherits_from_contains_routines(self):
        """Test that AddOnInstruction inherits from ContainsRoutines."""
        from pyrox.models.plc.collections import ContainsRoutines

        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        assert isinstance(aoi, ContainsRoutines)

        # Should have inherited methods/properties
        assert hasattr(aoi, 'routines')
        assert hasattr(aoi, 'name')

    def test_inherited_routines_functionality(self):
        """Test that inherited routines functionality works."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        # Should be able to access routines
        routines = aoi.routines
        assert len(routines) == 2
        assert routines[0]['@Name'] == 'Logic'
        assert routines[1]['@Name'] == 'EnableInFalse'

    def test_inherited_naming_validation(self):
        """Test that inherited naming validation works."""
        aoi = AddOnInstruction(meta_data=self.sample_meta_data)

        # Should inherit naming validation methods
        assert hasattr(aoi, 'is_valid_string')
        assert hasattr(aoi, 'is_valid_revision_string')
        assert hasattr(aoi, 'is_valid_rockwell_bool')

        # Test validation works
        assert aoi.is_valid_string('ValidName')
        assert not aoi.is_valid_string('Invalid Name!')
        assert aoi.is_valid_revision_string('1.2.3')
        assert aoi.is_valid_rockwell_bool('true')


class TestAddOnInstructionEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.minimal_meta_data = {
            '@Name': 'MinimalAOI',
            '@Revision': '1.0',
            '@ExecutePrescan': 'false',
            '@ExecutePostscan': 'false',
            '@ExecuteEnableInFalse': 'false',
            '@SoftwareRevision': '33.00'
        }

    def test_missing_optional_fields(self):
        """Test AOI with missing optional fields."""
        aoi = AddOnInstruction(meta_data=self.minimal_meta_data)

        assert aoi.name == 'MinimalAOI'
        assert aoi.revision == '1.0'

        # These should handle missing keys gracefully
        _ = aoi.revision_extension
        _ = aoi.revision_note

    def test_empty_parameters_and_local_tags(self):
        """Test behavior with empty parameters and local tags."""
        meta_data = self.minimal_meta_data.copy()
        meta_data.update({
            'Parameters': {},
            'LocalTags': {}
        })

        aoi = AddOnInstruction(meta_data=meta_data)

        # Should return empty lists for missing/empty structures
        assert aoi.parameters == []
        assert aoi.local_tags == []

    def test_none_values_in_collections(self):
        """Test behavior when collections contain None values."""
        meta_data = self.minimal_meta_data.copy()
        meta_data.update({
            'Parameters': None,
            'LocalTags': None
        })

        aoi = AddOnInstruction(meta_data=meta_data)

        assert aoi.parameters == []
        assert aoi.local_tags == []

        # raw_tags should create structure
        raw_tags = aoi.raw_tags
        assert isinstance(raw_tags, list)
        assert aoi['LocalTags'] == {'LocalTag': []}

    def test_boolean_conversion_edge_cases(self):
        """Test edge cases for boolean property conversions."""
        aoi = AddOnInstruction(meta_data=self.minimal_meta_data)

        # Test all boolean properties with edge cases
        boolean_properties = [
            'execute_prescan',
            'execute_postscan',
            'execute_enable_in_false'
        ]

        for prop in boolean_properties:
            # Test boolean True/False
            setattr(aoi, prop, True)
            assert getattr(aoi, prop) == 'true'

            setattr(aoi, prop, False)
            assert getattr(aoi, prop) == 'false'

            # Test string values
            setattr(aoi, prop, 'true')
            assert getattr(aoi, prop) == 'true'

            setattr(aoi, prop, 'false')
            assert getattr(aoi, prop) == 'false'

    def test_string_property_type_validation(self):
        """Test type validation for string properties."""
        aoi = AddOnInstruction(meta_data=self.minimal_meta_data)

        # Test revision_extension type validation
        with pytest.raises(ValueError, match="Revision extension must be a string!"):
            aoi.revision_extension = 123

        with pytest.raises(ValueError, match="Revision extension must be a string!"):
            aoi.revision_extension = ['list']

        # Test revision_note type validation
        with pytest.raises(ValueError, match="Revision note must be a string!"):
            aoi.revision_note = 123

        with pytest.raises(ValueError, match="Revision note must be a string!"):
            aoi.revision_note = {'dict': 'value'}


class TestAddOnInstructionIntegration:
    """Integration tests for AddOnInstruction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.full_meta_data = {
            '@Name': 'ComplexAOI',
            '@Class': 'User',
            '@Revision': '2.5',
            '@ExecutePrescan': 'true',
            '@ExecutePostscan': 'true',
            '@ExecuteEnableInFalse': 'false',
            '@CreatedDate': '2023-01-01T10:00:00.000Z',
            '@CreatedBy': 'Developer',
            '@EditedDate': '2023-06-01T15:30:00.000Z',
            '@EditedBy': 'Maintainer',
            '@SoftwareRevision': '34.00',
            '@RevisionExtension': 'v2.5<stable>',
            'Description': 'Complex AOI for testing',
            'RevisionNote': 'Added new functionality and bug fixes',
            'Parameters': {
                'Parameter': [
                    {
                        '@Name': 'Enable',
                        '@TagType': 'Base',
                        '@DataType': 'BOOL',
                        '@Usage': 'Input',
                        'Description': 'Enable input'
                    },
                    {
                        '@Name': 'Output',
                        '@TagType': 'Base',
                        '@DataType': 'BOOL',
                        '@Usage': 'Output',
                        'Description': 'Output value'
                    }
                ]
            },
            'LocalTags': {
                'LocalTag': [
                    {
                        '@Name': 'Counter',
                        '@DataType': 'DINT',
                        'Description': 'Internal counter'
                    },
                    {
                        '@Name': 'Timer',
                        '@DataType': 'TIMER',
                        'Description': 'Internal timer'
                    }
                ]
            },
            'Routines': {
                'Routine': [
                    {
                        '@Name': 'Logic',
                        '@Type': 'RLL'
                    },
                    {
                        '@Name': 'EnableInFalse',
                        '@Type': 'RLL'
                    }
                ]
            }
        }

    def test_full_aoi_functionality(self):
        """Test AOI with all features enabled."""
        aoi = AddOnInstruction(meta_data=self.full_meta_data)

        # Test all properties
        assert aoi.name == 'ComplexAOI'
        assert aoi.revision == '2.5'
        assert aoi.execute_prescan == 'true'
        assert aoi.execute_postscan == 'true'
        assert aoi.execute_enable_in_false == 'false'
        assert aoi.software_revision == '34.00'
        assert aoi.revision_extension == 'v2.5&lt;stable>'  # Should be escaped
        assert aoi.revision_note == 'Added new functionality and bug fixes'

        # Test collections
        parameters = aoi.parameters
        assert len(parameters) == 2
        assert parameters[0]['@Name'] == 'Enable'
        assert parameters[1]['@Name'] == 'Output'

        local_tags = aoi.local_tags
        assert len(local_tags) == 2
        assert local_tags[0]['@Name'] == 'Counter'
        assert local_tags[1]['@Name'] == 'Timer'

        raw_tags = aoi.raw_tags
        assert len(raw_tags) == 2
        assert raw_tags is aoi['LocalTags']['LocalTag']  # Should be same reference

    def test_property_modifications(self):
        """Test modifying various properties."""
        aoi = AddOnInstruction(meta_data=self.full_meta_data)

        # Modify revision
        aoi.revision = '3.0'
        assert aoi.revision == '3.0'

        # Modify boolean properties
        aoi.execute_prescan = False
        assert aoi.execute_prescan == 'false'

        aoi.execute_postscan = 'false'
        assert aoi.execute_postscan == 'false'

        # Modify string properties
        aoi.software_revision = '35.00'
        assert aoi.software_revision == '35.00'

        aoi.revision_extension = 'v3.0<beta>'
        assert aoi.revision_extension == 'v3.0&lt;beta>'

        aoi.revision_note = 'Major version update'
        assert aoi.revision_note == 'Major version update'

    def test_raw_tags_modification(self):
        """Test modifying AOI through raw_tags property."""
        aoi = AddOnInstruction(meta_data=self.full_meta_data)

        # Get raw tags and modify
        raw_tags = aoi.raw_tags
        original_count = len(raw_tags)

        # Add a new local tag
        new_tag = {
            '@Name': 'Status',
            '@DataType': 'BOOL',
            'Description': 'Status flag'
        }
        raw_tags.append(new_tag)

        # Verify changes are reflected
        assert len(aoi.raw_tags) == original_count + 1
        assert len(aoi.local_tags) == original_count + 1
        assert aoi.local_tags[-1]['@Name'] == 'Status'

        # Verify structure is maintained in meta_data
        assert len(aoi['LocalTags']['LocalTag']) == original_count + 1

    @patch('pyrox.models.plc.aoi.l5x_dict_from_file')
    def test_default_file_loading(self, mock_l5x_dict):
        """Test loading from default file."""
        mock_l5x_dict.return_value = {
            'AddOnInstructionDefinition': self.full_meta_data
        }

        aoi = AddOnInstruction()

        mock_l5x_dict.assert_called_once_with(plc_meta.PLC_AOI_FILE)
        assert aoi.name == 'ComplexAOI'

    def test_dict_key_order_completeness(self):
        """Test that dict_key_order includes all expected keys."""
        aoi = AddOnInstruction(meta_data=self.full_meta_data)

        key_order = aoi.dict_key_order

        # Test that all major keys are present
        expected_keys = [
            '@Name', '@Class', '@Revision', '@ExecutePrescan',
            '@ExecutePostscan', '@ExecuteEnableInFalse', '@CreatedDate',
            '@CreatedBy', '@EditedDate', '@EditedBy', '@SoftwareRevision',
            'Description', 'RevisionNote', 'Parameters', 'LocalTags', 'Routines'
        ]

        for key in expected_keys:
            assert key in key_order

        # Test order is maintained
        assert key_order == expected_keys


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
