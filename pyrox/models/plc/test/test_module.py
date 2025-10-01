"""Unit tests for the module module."""

import pytest
from unittest.mock import Mock, patch
from enum import Enum

from pyrox.models.plc.module import (
    Module,
    ModuleConnectionTag,
    ModuleControlsType
)
from pyrox.models.plc import meta as plc_meta


class TestModuleControlsType:
    """Test cases for ModuleControlsType enum."""

    def test_enum_values(self):
        """Test that all enum values are correct."""
        expected_values = {
            'UNKOWN': 'Unknown',
            'PLC': 'PLC',
            'ETHERNET': 'Ethernet',
            'SERIAL': 'Serial',
            'BLOCK': 'Block',
            'SAFETY_BLOCK': 'SafetyBlock',
            'DRIVE': 'Drive',
            'POINT_IO': 'PointIO'
        }

        for attr_name, expected_value in expected_values.items():
            enum_member = getattr(ModuleControlsType, attr_name)
            assert enum_member.value == expected_value

    def test_enum_is_enum(self):
        """Test that ModuleControlsType is properly an Enum."""
        assert issubclass(ModuleControlsType, Enum)
        assert len(ModuleControlsType) >= 8

    def test_enum_members_accessible(self):
        """Test that all enum members are accessible."""
        assert ModuleControlsType.UNKOWN == ModuleControlsType.UNKOWN
        assert ModuleControlsType.PLC == ModuleControlsType.PLC
        assert ModuleControlsType.ETHERNET == ModuleControlsType.ETHERNET
        assert ModuleControlsType.SERIAL == ModuleControlsType.SERIAL
        assert ModuleControlsType.BLOCK == ModuleControlsType.BLOCK
        assert ModuleControlsType.SAFETY_BLOCK == ModuleControlsType.SAFETY_BLOCK
        assert ModuleControlsType.DRIVE == ModuleControlsType.DRIVE
        assert ModuleControlsType.POINT_IO == ModuleControlsType.POINT_IO


class TestModuleConnectionTag:
    """Test cases for ModuleConnectionTag class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_controller = Mock()

        self.sample_tag_data = {
            '@ConfigSize': '128',
            'Data': [
                {
                    '@Format': 'L5X',
                    'SomeL5XData': 'value'
                },
                {
                    '@Format': 'Decorated',
                    'Structure': {
                        '@DataType': 'DINT',
                        'ArrayMember': {
                            '@Dimensions': '10'
                        }
                    }
                }
            ]
        }

    def test_initialization(self):
        """Test ModuleConnectionTag initialization."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        assert tag.controller is self.mock_controller
        assert tag['@ConfigSize'] == '128'

    def test_config_size_property(self):
        """Test config_size property getter."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        assert tag.config_size == '128'

    def test_data_property_with_list(self):
        """Test data property when Data is a list."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        data = tag.data
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['@Format'] == 'L5X'
        assert data[1]['@Format'] == 'Decorated'

    def test_data_property_with_none(self):
        """Test data property when Data is None."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'] = None

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        data = tag.data
        assert data == [{}]

    def test_data_property_with_missing_data(self):
        """Test data property when Data key is missing."""
        tag_data = self.sample_tag_data.copy()
        del tag_data['Data']

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        data = tag.data
        assert data == [{}]

    def test_data_decorated_property(self):
        """Test data_decorated property finds Decorated format."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        decorated = tag.data_decorated
        assert decorated['@Format'] == 'Decorated'
        assert 'Structure' in decorated

    def test_data_decorated_property_not_found(self):
        """Test data_decorated property when Decorated format not found."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'] = [{'@Format': 'L5X'}]

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        decorated = tag.data_decorated
        assert decorated == {}

    def test_data_decorated_property_with_single_item(self):
        """Test data_decorated property when data is not a list."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'] = {'@Format': 'Decorated', 'Structure': {}}

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        decorated = tag.data_decorated
        assert decorated['@Format'] == 'Decorated'

    def test_data_decorated_structure_property(self):
        """Test data_decorated_structure property."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        structure = tag.data_decorated_structure
        expected = {
            '@DataType': 'DINT',
            'ArrayMember': {
                '@Dimensions': '10'
            }
        }
        assert structure == expected

    def test_data_decorated_structure_array_member_property(self):
        """Test data_decorated_structure_array_member property."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        array_member = tag.data_decorated_structure_array_member
        assert array_member == {'@Dimensions': '10'}

    def test_data_decorated_stucture_datatype_property(self):
        """Test data_decorated_stucture_datatype property."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        datatype = tag.data_decorated_stucture_datatype
        assert datatype == 'DINT'

    def test_data_decorated_stucture_size_property(self):
        """Test data_decorated_stucture_size property."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        size = tag.data_decorated_stucture_size
        assert size == '10'

    def test_data_l5x_property(self):
        """Test data_l5x property finds L5X format."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        l5x = tag.data_l5x
        assert l5x['@Format'] == 'L5X'
        assert l5x['SomeL5XData'] == 'value'

    def test_data_l5x_property_not_found(self):
        """Test data_l5x property when L5X format not found."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'] = [{'@Format': 'Decorated'}]

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        l5x = tag.data_l5x
        assert l5x == {}

    def test_get_data_multiplier_sint(self):
        """Test get_data_multiplier for SINT datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'SINT'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 1

    def test_get_data_multiplier_int(self):
        """Test get_data_multiplier for INT datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'INT'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 2

    def test_get_data_multiplier_dint(self):
        """Test get_data_multiplier for DINT datatype."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 4

    def test_get_data_multiplier_real(self):
        """Test get_data_multiplier for REAL datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'REAL'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 4

    def test_get_data_multiplier_dword(self):
        """Test get_data_multiplier for DWORD datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'DWORD'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 4

    def test_get_data_multiplier_lint(self):
        """Test get_data_multiplier for LINT datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'LINT'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 8

    def test_get_data_multiplier_lreal(self):
        """Test get_data_multiplier for LREAL datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'LREAL'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 8

    def test_get_data_multiplier_lword(self):
        """Test get_data_multiplier for LWORD datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'LWORD'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 8

    def test_get_data_multiplier_unsupported_datatype(self):
        """Test get_data_multiplier raises error for unsupported datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['@DataType'] = 'UNSUPPORTED'

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        with pytest.raises(ValueError, match="Unsupported datatype: UNSUPPORTED"):
            tag.get_data_multiplier()

    def test_get_data_multiplier_no_datatype(self):
        """Test get_data_multiplier returns 0 when no datatype."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure'] = {}

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        multiplier = tag.get_data_multiplier()
        assert multiplier == 0

    def test_get_resolved_size(self):
        """Test get_resolved_size calculation."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        # Size is '10', multiplier for DINT is 4
        resolved_size = tag.get_resolved_size()
        assert resolved_size == 40  # 10 * 4

    def test_get_resolved_size_no_size(self):
        """Test get_resolved_size returns 0 when no size."""
        tag_data = self.sample_tag_data.copy()
        tag_data['Data'][1]['Structure']['ArrayMember'] = {}

        tag = ModuleConnectionTag(
            meta_data=tag_data,
            controller=self.mock_controller
        )

        resolved_size = tag.get_resolved_size()
        assert resolved_size == 0

    def test_inheritance_from_plc_object(self):
        """Test that ModuleConnectionTag inherits from PlcObject."""
        tag = ModuleConnectionTag(
            meta_data=self.sample_tag_data,
            controller=self.mock_controller
        )

        assert isinstance(tag, plc_meta.PlcObject)


class TestModule:
    """Test cases for Module class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_controller = Mock()

        self.sample_module_data = {
            '@Name': 'TestModule',
            '@CatalogNumber': '1756-L73',
            '@Vendor': '1',
            '@ProductType': '14',
            '@ProductCode': '166',
            '@Major': '33',
            '@Minor': '11',
            '@ParentModule': 'Local',
            '@ParentModPortId': '1',
            '@Inhibited': 'false',
            '@MajorFault': 'false',
            'Description': 'Test module description',
            'EKey': {
                '@State': 'ExactMatch'
            },
            'Ports': {
                'Port': [
                    {
                        '@Id': '1',
                        '@Type': 'ICP'
                    }
                ]
            },
            'Communications': {
                'ConfigTag': {
                    '@ConfigSize': '128',
                    'Data': []
                },
                'Connections': {
                    'Connection': [
                        {
                            '@Name': 'Connection1',
                            '@ConfigCxnPoint': '1',
                            '@InputCxnPoint': '2',
                            '@OutputCxnPoint': '3',
                            '@InputSize': '64',
                            '@OutputSize': '32',
                            'InputTag': {
                                '@ConfigSize': '64',
                                'Data': []
                            },
                            'OutputTag': {
                                '@ConfigSize': '32',
                                'Data': []
                            }
                        }
                    ]
                }
            }
        }

    @patch('pyrox.models.plc.meta.l5x_dict_from_file')
    def test_initialization_default_meta_data(self, mock_l5x_dict):
        """Test initialization with default meta data from file."""
        mock_l5x_dict.return_value = {'Module': self.sample_module_data}

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module()

        mock_l5x_dict.assert_called_once_with(plc_meta.PLC_MOD_FILE)
        assert module.name == 'TestModule'

    def test_initialization_with_meta_data(self):
        """Test initialization with provided meta data."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.name == 'TestModule'
        assert module.controller is self.mock_controller

    def test_dict_key_order(self):
        """Test dict_key_order property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        expected_order = [
            '@Name',
            '@CatalogNumber',
            '@Vendor',
            '@ProductType',
            '@ProductCode',
            '@Major',
            '@Minor',
            '@ParentModule',
            '@ParentModPortId',
            '@Inhibited',
            '@MajorFault',
            'Description',
            'EKey',
            'Ports',
            'Communications',
        ]

        assert module.dict_key_order == expected_order

    def test_catalog_number_property_getter(self):
        """Test catalog_number property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.catalog_number == '1756-L73'

    def test_catalog_number_property_setter_valid(self):
        """Test catalog_number property setter with valid value."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.catalog_number = '1756-L74'
        assert module.catalog_number == '1756-L74'
        assert module['@CatalogNumber'] == '1756-L74'

    def test_catalog_number_property_setter_invalid(self):
        """Test catalog_number property setter with invalid value."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with patch.object(module, 'is_valid_module_string', return_value=False):
            with pytest.raises(module.InvalidNamingException):
                module.catalog_number = 'invalid-catalog'

    def test_communications_property_getter(self):
        """Test communications property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        communications = module.communications
        assert isinstance(communications, dict)
        assert 'ConfigTag' in communications
        assert 'Connections' in communications

    def test_communications_property_setter_valid(self):
        """Test communications property setter with valid dictionary."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        new_communications = {'NewKey': 'NewValue'}
        module.communications = new_communications
        assert module.communications == new_communications

    def test_communications_property_setter_invalid(self):
        """Test communications property setter with invalid type."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with pytest.raises(ValueError, match="Communications must be a dictionary!"):
            module.communications = "not a dictionary"

    def test_connection_property(self):
        """Test connection property returns first connection."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        connection = module.connection
        assert connection['@Name'] == 'Connection1'

    def test_connection_property_empty_connections(self):
        """Test connection property when no connections."""
        module_data = self.sample_module_data.copy()
        module_data['Communications']['Connections']['Connection'] = []

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        connection = module.connection
        assert connection == {}

    def test_connections_property_with_list(self):
        """Test connections property when Connections contains a list."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        connections = module.connections
        assert isinstance(connections, list)
        assert len(connections) == 1
        assert connections[0]['@Name'] == 'Connection1'

    def test_connections_property_with_single_connection(self):
        """Test connections property when Connection is not a list."""
        module_data = self.sample_module_data.copy()
        module_data['Communications']['Connections']['Connection'] = {
            '@Name': 'SingleConnection'
        }

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        connections = module.connections
        assert isinstance(connections, list)
        assert len(connections) == 1
        assert connections[0]['@Name'] == 'SingleConnection'

    def test_connections_property_no_communications(self):
        """Test connections property when no communications."""
        module_data = self.sample_module_data.copy()
        module_data['Communications'] = None

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        connections = module.connections
        assert connections == {}

    def test_connections_property_no_connections_key(self):
        """Test connections property when Connections key missing."""
        module_data = self.sample_module_data.copy()
        del module_data['Communications']['Connections']

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        connections = module.connections
        assert connections == {}

    def test_config_connection_point_property(self):
        """Test config_connection_point property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        config_point = module.config_connection_point
        assert config_point == '1'

    def test_config_connection_point_property_no_connections(self):
        """Test config_connection_point property when no connections."""
        module_data = self.sample_module_data.copy()
        module_data['Communications']['Connections']['Connection'] = []

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        config_point = module.config_connection_point
        assert config_point == ''

    def test_input_connection_point_property(self):
        """Test input_connection_point property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        input_point = module.input_connection_point
        assert input_point == '2'

    def test_output_connection_point_property(self):
        """Test output_connection_point property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        output_point = module.output_connection_point
        assert output_point == '3'

    def test_config_connection_size_property(self):
        """Test config_connection_size property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            # Mock the config_tag
            mock_config_tag = Mock()
            mock_config_tag.config_size = '128'
            module._config_tag = mock_config_tag

        config_size = module.config_connection_size
        assert config_size == '128'

    def test_config_connection_size_property_no_config_tag(self):
        """Test config_connection_size property when no config tag."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            module._config_tag = None

        config_size = module.config_connection_size
        assert config_size == ''

    def test_input_connection_size_property(self):
        """Test input_connection_size property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        input_size = module.input_connection_size
        assert input_size == '64'

    def test_output_connection_size_property(self):
        """Test output_connection_size property."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        output_size = module.output_connection_size
        assert output_size == '32'

    def test_vendor_property_getter(self):
        """Test vendor property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.vendor == '1'

    def test_vendor_property_setter_valid(self):
        """Test vendor property setter with valid integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.vendor = '2'
        assert module.vendor == '2'
        assert module['@Vendor'] == '2'

    def test_vendor_property_setter_invalid(self):
        """Test vendor property setter with non-integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with pytest.raises(ValueError, match="Vendor must be an integer!"):
            module.vendor = 'not_an_integer'

    def test_product_type_property_getter(self):
        """Test product_type property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.product_type == '14'

    def test_product_type_property_setter_valid(self):
        """Test product_type property setter with valid integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.product_type = '15'
        assert module.product_type == '15'

    def test_product_type_property_setter_invalid(self):
        """Test product_type property setter with non-integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with pytest.raises(ValueError, match="@ProductType must be an integer!"):
            module.product_type = 'invalid'

    def test_product_code_property_getter(self):
        """Test product_code property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.product_code == '166'

    def test_product_code_property_setter_valid(self):
        """Test product_code property setter with valid integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.product_code = '167'
        assert module.product_code == '167'

    def test_product_code_property_setter_invalid(self):
        """Test product_code property setter with non-integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with pytest.raises(ValueError, match="@ProductCode must be an integer!"):
            module.product_code = 'abc'

    def test_major_property_getter(self):
        """Test major property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.major == '33'

    def test_major_property_setter_valid(self):
        """Test major property setter with valid integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.major = '34'
        assert module.major == '34'

    def test_major_property_setter_invalid(self):
        """Test major property setter with non-integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with pytest.raises(ValueError, match="@Major must be an integer!"):
            module.major = 'v33'

    def test_minor_property_getter(self):
        """Test minor property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.minor == '11'

    def test_minor_property_setter_valid(self):
        """Test minor property setter with valid integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.minor = '12'
        assert module.minor == '12'

    def test_minor_property_setter_invalid(self):
        """Test minor property setter with non-integer string."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with pytest.raises(ValueError, match="@Minor must be an integer!"):
            module.minor = 'beta'

    def test_parent_module_property(self):
        """Test parent_module property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.parent_module == 'Local'

    def test_parent_mod_port_id_property(self):
        """Test parent_mod_port_id property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.parent_mod_port_id == '1'

    def test_inhibited_property_getter(self):
        """Test inhibited property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.inhibited == 'false'

    def test_inhibited_property_setter_string(self):
        """Test inhibited property setter with string values."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.inhibited = 'true'
        assert module.inhibited == 'true'

        module.inhibited = 'false'
        assert module.inhibited == 'false'

    def test_inhibited_property_setter_bool(self):
        """Test inhibited property setter with boolean values."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.inhibited = True
        assert module.inhibited == 'true'

        module.inhibited = False
        assert module.inhibited == 'false'

    def test_inhibited_property_setter_invalid(self):
        """Test inhibited property setter with invalid values."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with patch.object(module, 'is_valid_rockwell_bool', return_value=False):
            with pytest.raises(module.InvalidNamingException):
                module.inhibited = 'invalid'

    def test_major_fault_property_getter(self):
        """Test major_fault property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert module.major_fault == 'false'

    def test_major_fault_property_setter_string(self):
        """Test major_fault property setter with string values."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.major_fault = 'true'
        assert module.major_fault == 'true'

    def test_major_fault_property_setter_bool(self):
        """Test major_fault property setter with boolean values."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        module.major_fault = True
        assert module.major_fault == 'true'

        module.major_fault = False
        assert module.major_fault == 'false'

    def test_major_fault_property_setter_invalid(self):
        """Test major_fault property setter with invalid values."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        with patch.object(module, 'is_valid_rockwell_bool', return_value=False):
            with pytest.raises(module.InvalidNamingException):
                module.major_fault = 'maybe'

    def test_ekey_property(self):
        """Test ekey property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        ekey = module.ekey
        assert ekey['@State'] == 'ExactMatch'

    def test_ports_property_with_list(self):
        """Test ports property when Ports contains a list."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        ports = module.ports
        assert isinstance(ports, list)
        assert len(ports) == 1
        assert ports[0]['@Id'] == '1'

    def test_ports_property_with_single_port(self):
        """Test ports property when Port is not a list."""
        module_data = self.sample_module_data.copy()
        module_data['Ports']['Port'] = {'@Id': '2', '@Type': 'ICP'}

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        ports = module.ports
        assert isinstance(ports, list)
        assert len(ports) == 1
        assert ports[0]['@Id'] == '2'

    def test_ports_property_no_ports(self):
        """Test ports property when no Ports."""
        module_data = self.sample_module_data.copy()
        module_data['Ports'] = None

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        ports = module.ports
        assert ports == []

    def test_type_property_with_introspective_module(self):
        """Test type_ property when introspective module exists."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            mock_introspective = Mock()
            mock_introspective.type_ = 'TestType'
            module._introspective_module = mock_introspective

        assert module.type_ == 'TestType'

    def test_type_property_without_introspective_module(self):
        """Test type_ property when no introspective module."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            module._introspective_module = None

        assert module.type_ == 'Unknown'

    def test_introspective_module_property(self):
        """Test introspective_module property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            mock_introspective = Mock()
            module._introspective_module = mock_introspective

        assert module.introspective_module is mock_introspective

    def test_config_tag_property(self):
        """Test config_tag property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            mock_config_tag = Mock()
            module._config_tag = mock_config_tag

        assert module.config_tag is mock_config_tag

    def test_input_tag_property(self):
        """Test input_tag property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            mock_input_tag = Mock()
            module._input_tag = mock_input_tag

        assert module.input_tag is mock_input_tag

    def test_output_tag_property(self):
        """Test output_tag property getter."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

            mock_output_tag = Mock()
            module._output_tag = mock_output_tag

        assert module.output_tag is mock_output_tag

    def test_inheritance_from_named_plc_object(self):
        """Test that Module inherits from NamedPlcObject."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.sample_module_data,
                controller=self.mock_controller
            )

        assert isinstance(module, plc_meta.NamedPlcObject)


class TestModulePrivateMethods:
    """Test private methods of Module class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()

        self.sample_module_data = {
            '@Name': 'TestModule',
            '@CatalogNumber': '1756-L73',
            '@Vendor': '1',
            '@ProductType': '14',
            '@ProductCode': '166',
            '@Major': '33',
            '@Minor': '11',
            '@ParentModule': 'Local',
            '@ParentModPortId': '1',
            '@Inhibited': 'false',
            '@MajorFault': 'false',
            'Description': 'Test module description',
            'EKey': {'@State': 'ExactMatch'},
            'Ports': {'Port': []},
            'Communications': {
                'ConfigTag': {
                    '@ConfigSize': '128',
                    'Data': []
                },
                'Connections': {
                    'Connection': [
                        {
                            '@Name': 'Connection1',
                            'InputTag': {
                                '@ConfigSize': '64',
                                'Data': []
                            },
                            'OutputTag': {
                                '@ConfigSize': '32',
                                'Data': []
                            }
                        }
                    ]
                }
            }
        }

    @patch('pyrox.models.plc.imodule.IntrospectiveModule')
    def test_compile_from_meta_data(self, mock_introspective_module_class):
        """Test _compile_from_meta_data method."""
        mock_introspective_instance = Mock()
        mock_introspective_module_class.from_meta_data.return_value = mock_introspective_instance

        module = Module(
            meta_data=self.sample_module_data,
            controller=self.mock_controller
        )

        # Should have created introspective module
        mock_introspective_module_class.from_meta_data.assert_called_once_with(
            module, lazy_match_catalog=True
        )
        assert module._introspective_module is mock_introspective_instance

        # Should have created connection tags
        assert isinstance(module._config_tag, ModuleConnectionTag)
        assert isinstance(module._input_tag, ModuleConnectionTag)
        assert isinstance(module._output_tag, ModuleConnectionTag)

    def test_compile_tag_meta_data_no_communications(self):
        """Test _compile_tag_meta_data with no communications."""
        module_data = self.sample_module_data.copy()
        module_data['Communications'] = None

        with patch('pyrox.models.plc.imodule.IntrospectiveModule'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        # Should not have created any tags
        assert module._config_tag is None
        assert module._input_tag is None
        assert module._output_tag is None

    def test_compile_tag_meta_data_no_connections(self):
        """Test _compile_tag_meta_data with no connections."""
        module_data = self.sample_module_data.copy()
        del module_data['Communications']['Connections']

        with patch('pyrox.models.plc.imodule.IntrospectiveModule'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        # Should have config tag but no input/output tags
        assert isinstance(module._config_tag, ModuleConnectionTag)
        assert module._input_tag is None
        assert module._output_tag is None

    def test_compile_tag_meta_data_no_input_output_tags(self):
        """Test _compile_tag_meta_data with connection but no InputTag/OutputTag."""
        module_data = self.sample_module_data.copy()
        module_data['Communications']['Connections']['Connection'][0] = {
            '@Name': 'Connection1'
            # No InputTag or OutputTag
        }

        with patch('pyrox.models.plc.imodule.IntrospectiveModule'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        # Should have config tag but no input/output tags
        assert isinstance(module._config_tag, ModuleConnectionTag)
        assert module._input_tag is None
        assert module._output_tag is None


class TestModuleEdgeCases:
    """Test edge cases and error conditions for Module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()

        self.minimal_module_data = {
            '@Name': 'MinimalModule',
            '@CatalogNumber': '1756-L73',
            '@Vendor': '1',
            '@ProductType': '14',
            '@ProductCode': '166',
            '@Major': '33',
            '@Minor': '11',
            '@ParentModule': 'Local',
            '@ParentModPortId': '1',
            '@Inhibited': 'false',
            '@MajorFault': 'false'
        }

    def test_module_with_missing_optional_fields(self):
        """Test module with missing optional fields."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.minimal_module_data,
                controller=self.mock_controller
            )

        assert module.name == 'MinimalModule'
        assert module.catalog_number == '1756-L73'

        # These should NOT raise KeyError for missing keys
        _ = module.description
        _ = module.ekey

    def test_integer_string_validation_edge_cases(self):
        """Test integer string validation for various properties."""
        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=self.minimal_module_data,
                controller=self.mock_controller
            )

        # Test properties that require integer strings
        integer_properties = [
            ('vendor', 'Vendor must be an integer!'),
            ('product_type', '@ProductType must be an integer!'),
            ('product_code', '@ProductCode must be an integer!'),
            ('major', '@Major must be an integer!'),
            ('minor', '@Minor must be an integer!')
        ]

        for prop_name, error_msg in integer_properties:
            with pytest.raises(ValueError, match=error_msg):
                setattr(module, prop_name, 'not_an_integer')

    def test_empty_structures_handling(self):
        """Test handling of empty or None structures."""
        module_data = self.minimal_module_data.copy()
        module_data.update({
            'Ports': None,
            'Communications': {}
        })

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        assert module.ports == []
        assert module.connections == {}
        assert module.connection == {}

    def test_connections_structure_normalization(self):
        """Test that connections structure gets normalized properly."""
        module_data = self.minimal_module_data.copy()
        module_data['Communications'] = {
            'Connections': 'not_a_dict'  # Invalid structure
        }

        with patch('pyrox.models.plc.module.Module._compile_from_meta_data'):
            module = Module(
                meta_data=module_data,
                controller=self.mock_controller
            )

        # Should normalize to proper structure
        connections = module.connections
        assert connections == []

        # Check that the structure was normalized
        assert module.communications['Connections'] == {'Connection': []}


class TestModuleIntegration:
    """Integration tests for Module class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_controller = Mock()

        self.complex_module_data = {
            '@Name': 'ComplexModule',
            '@CatalogNumber': '1756-L73',
            '@Vendor': '1',
            '@ProductType': '14',
            '@ProductCode': '166',
            '@Major': '33',
            '@Minor': '11',
            '@ParentModule': 'Local',
            '@ParentModPortId': '1',
            '@Inhibited': 'false',
            '@MajorFault': 'false',
            'Description': 'Complex test module',
            'EKey': {'@State': 'ExactMatch'},
            'Ports': {
                'Port': [
                    {'@Id': '1', '@Type': 'ICP'},
                    {'@Id': '2', '@Type': 'Ethernet'}
                ]
            },
            'Communications': {
                'ConfigTag': {
                    '@ConfigSize': '256',
                    'Data': [
                        {'@Format': 'L5X'},
                        {
                            '@Format': 'Decorated',
                            'Structure': {
                                '@DataType': 'DINT',
                                'ArrayMember': {'@Dimensions': '20'}
                            }
                        }
                    ]
                },
                'Connections': {
                    'Connection': [
                        {
                            '@Name': 'Connection1',
                            '@ConfigCxnPoint': '1',
                            '@InputCxnPoint': '2',
                            '@OutputCxnPoint': '3',
                            '@InputSize': '128',
                            '@OutputSize': '64',
                            'InputTag': {
                                '@ConfigSize': '128',
                                'Data': [
                                    {
                                        '@Format': 'Decorated',
                                        'Structure': {
                                            '@DataType': 'REAL',
                                            'ArrayMember': {'@Dimensions': '32'}
                                        }
                                    }
                                ]
                            },
                            'OutputTag': {
                                '@ConfigSize': '64',
                                'Data': [
                                    {
                                        '@Format': 'Decorated',
                                        'Structure': {
                                            '@DataType': 'INT',
                                            'ArrayMember': {'@Dimensions': '512'}
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }

    @patch('pyrox.models.plc.imodule.IntrospectiveModule')
    def test_complex_module_creation(self, mock_introspective_module_class):
        """Test creating a complex module with all features."""
        mock_introspective = Mock()
        mock_introspective.type_ = 'ComplexType'
        mock_introspective_module_class.from_meta_data.return_value = mock_introspective

        module = Module(
            meta_data=self.complex_module_data,
            controller=self.mock_controller
        )

        # Test basic properties
        assert module.name == 'ComplexModule'
        assert module.catalog_number == '1756-L73'
        assert module.vendor == '1'
        assert module.type_ == 'ComplexType'

        # Test complex structures
        assert len(module.ports) == 2
        assert module.ports[0]['@Id'] == '1'
        assert module.ports[1]['@Id'] == '2'

        # Test connection properties
        assert module.config_connection_point == '1'
        assert module.input_connection_point == '2'
        assert module.output_connection_point == '3'
        assert module.input_connection_size == '128'
        assert module.output_connection_size == '64'

        # Test connection tags
        assert isinstance(module.config_tag, ModuleConnectionTag)
        assert isinstance(module.input_tag, ModuleConnectionTag)
        assert isinstance(module.output_tag, ModuleConnectionTag)

        # Test connection tag functionality
        assert module.config_tag.config_size == '256'
        assert module.input_tag.config_size == '128'
        assert module.output_tag.config_size == '64'

        # Test resolved sizes
        config_resolved = module.config_tag.get_resolved_size()  # 20 * 4 (DINT)
        assert config_resolved == 80

        input_resolved = module.input_tag.get_resolved_size()  # 32 * 4 (REAL)
        assert input_resolved == 128

        output_resolved = module.output_tag.get_resolved_size()  # 512 * 2 (INT)
        assert output_resolved == 1024

    @patch('pyrox.models.plc.imodule.IntrospectiveModule')
    def test_module_property_modifications(self, mock_introspective_module_class):
        """Test modifying various module properties."""
        mock_introspective_module_class.from_meta_data.return_value = Mock()

        module = Module(
            meta_data=self.complex_module_data,
            controller=self.mock_controller
        )

        # Test catalog number modification
        module.catalog_number = '1756-L74'
        assert module.catalog_number == '1756-L74'

        # Test numeric property modifications
        module.vendor = '2'
        assert module.vendor == '2'

        module.product_type = '15'
        assert module.product_type == '15'

        module.product_code = '167'
        assert module.product_code == '167'

        module.major = '34'
        assert module.major == '34'

        module.minor = '12'
        assert module.minor == '12'

        # Test boolean property modifications
        module.inhibited = True
        assert module.inhibited == 'true'

        module.major_fault = True
        assert module.major_fault == 'true'

        # Test communications modification
        new_communications = {'NewKey': 'NewValue'}
        module.communications = new_communications
        assert module.communications == new_communications

    @patch('pyrox.models.plc.module.l5x_dict_from_file')
    @patch('pyrox.models.plc.imodule.IntrospectiveModule')
    def test_default_file_loading_integration(self, mock_introspective_module_class, mock_l5x_dict):
        """Test complete integration with default file loading."""
        mock_l5x_dict.return_value = {'Module': self.complex_module_data}
        mock_introspective_module_class.from_meta_data.return_value = Mock()

        module = Module()

        mock_l5x_dict.assert_called_once_with(plc_meta.PLC_MOD_FILE)
        assert module.name == 'ComplexModule'
        assert isinstance(module.config_tag, ModuleConnectionTag)
        assert isinstance(module.input_tag, ModuleConnectionTag)
        assert isinstance(module.output_tag, ModuleConnectionTag)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
