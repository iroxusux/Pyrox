"""Test suite for tag module"""
import unittest
from unittest.mock import Mock, patch
from pyrox.models.plc import meta as plc_meta
from pyrox.models.plc.tag import Tag, DataValueMember, TagEndpoint


class TestDataValueMember(unittest.TestCase):
    """Test class for DataValueMember"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_controller = Mock()
        self.mock_parent = Mock()
        self.valid_metadata = {'@Name': 'TestMember', '@DataType': 'BOOL'}

    def test_init_with_valid_params(self):
        """Test DataValueMember initialization with valid parameters"""
        member = DataValueMember(
            name="TestMember",
            l5x_meta_data=self.valid_metadata,
            controller=self.mock_controller,
            parent=self.mock_parent
        )

        self.assertEqual(member.parent, self.mock_parent)
        self.assertEqual(member.name, "TestMember")

    def test_init_without_metadata_raises_error(self):
        """Test that missing metadata raises ValueError"""
        with self.assertRaises(ValueError) as context:
            DataValueMember(
                name="TestMember",
                l5x_meta_data=None,
                controller=self.mock_controller,
                parent=self.mock_parent
            )

        self.assertEqual(str(context.exception), 'Cannot have an empty DataValueMember!')

    def test_init_without_parent_raises_error(self):
        """Test that missing parent raises ValueError"""
        with self.assertRaises(ValueError) as context:
            DataValueMember(
                name="TestMember",
                l5x_meta_data=self.valid_metadata,
                controller=self.mock_controller,
                parent=None
            )

        self.assertEqual(str(context.exception), 'Cannot have a datavalue member without a parent!')

    def test_parent_property(self):
        """Test parent property returns correct parent"""
        member = DataValueMember(
            l5x_meta_data=self.valid_metadata,
            controller=self.mock_controller,
            parent=self.mock_parent
        )

        self.assertEqual(member.parent, self.mock_parent)


class TestTagEndpoint(unittest.TestCase):
    """Test class for TagEndpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_controller = Mock()
        self.mock_parent_tag = Mock()
        self.test_meta_data = "TestTag.Endpoint"

    def test_init(self):
        """Test TagEndpoint initialization"""
        endpoint = TagEndpoint(
            meta_data=self.test_meta_data,
            controller=self.mock_controller,
            parent_tag=self.mock_parent_tag
        )

        self.assertEqual(endpoint._parent_tag, self.mock_parent_tag)

    def test_name_property(self):
        """Test name property returns meta_data"""
        endpoint = TagEndpoint(
            meta_data=self.test_meta_data,
            controller=self.mock_controller,
            parent_tag=self.mock_parent_tag
        )

        self.assertEqual(endpoint.name, self.test_meta_data)


class TestTag(unittest.TestCase):
    """Test class for Tag"""

    def setUp(self):
        """Set up test fixtures"""
        from pyrox.models.plc.controller import Controller
        self.mock_controller = Mock(spec=Controller)
        self.mock_container = Mock()
        self.valid_metadata = {
            '@Name': 'TestTag',
            '@Class': 'Standard',
            '@TagType': 'Base',
            '@DataType': 'BOOL',
            '@Dimensions': '',
            '@Constant': 'false',
            '@ExternalAccess': 'ReadOnly',
            'Data': []
        }

    @patch('pyrox.models.plc.tag.l5x_dict_from_file')
    def test_init_with_minimal_params(self, mock_l5x_dict):
        """Test Tag initialization with minimal parameters"""
        mock_l5x_dict.return_value = {'Tag': self.valid_metadata}

        tag = Tag(controller=self.mock_controller)

        self.assertEqual(tag.controller, self.mock_controller)
        mock_l5x_dict.assert_called_once()

    def test_init_with_all_params(self):
        """Test Tag initialization with all parameters"""
        tag = Tag(
            meta_data=self.valid_metadata,
            controller=self.mock_controller,
            name="TestTag",
            description="Test Description",
            class_="Standard",
            tag_type="Base",
            datatype="BOOL",
            dimensions="1",
            constant=True,
            external_access="ReadOnly",
            container=self.mock_container
        )

        self.assertEqual(tag.name, "TestTag")
        self.assertEqual(tag.description, "Test Description")
        self.assertEqual(tag.container, self.mock_container)

    def test_dict_key_order(self):
        """Test dict_key_order property returns correct order"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        expected_order = [
            '@Name', '@Class', '@TagType', '@DataType', '@Dimensions',
            '@Radix', '@AliasFor', '@Constant', '@ExternalAccess',
            'ConsumeInfo', 'ProduceInfo', 'Description', 'Data'
        ]

        self.assertEqual(tag.dict_key_order, expected_order)

    def test_alias_for_property(self):
        """Test alias_for property"""
        metadata_with_alias = self.valid_metadata.copy()
        metadata_with_alias['@AliasFor'] = 'OriginalTag.Member'

        tag = Tag(meta_data=metadata_with_alias, controller=self.mock_controller)

        self.assertEqual(tag.alias_for, 'OriginalTag.Member')

    def test_alias_for_base_name(self):
        """Test alias_for_base_name property"""
        metadata_with_alias = self.valid_metadata.copy()
        metadata_with_alias['@AliasFor'] = 'OriginalTag.Member:Bit0'

        tag = Tag(meta_data=metadata_with_alias, controller=self.mock_controller)

        self.assertEqual(tag.alias_for_base_name, 'OriginalTag')

    def test_alias_for_base_name_none(self):
        """Test alias_for_base_name returns None when no alias"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertIsNone(tag.alias_for_base_name)

    def test_class_property(self):
        """Test class_ property getter and setter"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertEqual(tag.class_, 'Standard')

        tag.class_ = 'Safety'
        self.assertEqual(tag.class_, 'Safety')

    def test_class_setter_invalid_type(self):
        """Test class_ setter with invalid type raises error"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            tag.class_ = 123

        self.assertEqual(str(context.exception), "Class must be a string!")

    def test_class_setter_invalid_value(self):
        """Test class_ setter with invalid value raises error"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            tag.class_ = "Invalid"

        self.assertEqual(str(context.exception), "Class must be one of: Standard, Safety!")

    def test_constant_property(self):
        """Test constant property getter and setter"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertEqual(tag.constant, 'false')

        tag.constant = True
        self.assertEqual(tag.constant, 'true')

        tag.constant = False
        self.assertEqual(tag.constant, 'false')

    def test_datatype_property(self):
        """Test datatype property getter and setter"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertEqual(tag.datatype, 'BOOL')

        tag.datatype = 'DINT'
        self.assertEqual(tag.datatype, 'DINT')

    def test_dimensions_property(self):
        """Test dimensions property getter and setter"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        tag.dimensions = '10'
        self.assertEqual(tag.dimensions, '10')

        tag.dimensions = 5
        self.assertEqual(tag.dimensions, '5')

    def test_dimensions_setter_negative_int(self):
        """Test dimensions setter with negative integer raises error"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            tag.dimensions = -1

        self.assertEqual(str(context.exception), "Dimensions must be a positive integer!")

    def test_external_access_property(self):
        """Test external_access property getter and setter"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertEqual(tag.external_access, 'ReadOnly')

        tag.external_access = 'Read/Write'
        self.assertEqual(tag.external_access, 'Read/Write')

    def test_external_access_setter_invalid_value(self):
        """Test external_access setter with invalid value raises error"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            tag.external_access = "Invalid"

        self.assertEqual(str(context.exception), "External access must be one of: None, ReadOnly, Read/Write!")

    def test_tag_type_property(self):
        """Test tag_type property getter and setter"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertEqual(tag.tag_type, 'Base')

        tag.tag_type = 'Structure'
        self.assertEqual(tag.tag_type, 'Structure')

    def test_tag_type_setter_invalid_value(self):
        """Test tag_type setter with invalid value raises error"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        with self.assertRaises(ValueError) as context:
            tag.tag_type = "Invalid"

        self.assertEqual(str(context.exception), "Tag type must be one of: Atomic, Structure, Array!")

    def test_data_property_single_item(self):
        """Test data property with single data item"""
        metadata = self.valid_metadata.copy()
        metadata['Data'] = {'@Format': 'L5K', 'Value': '0'}

        tag = Tag(meta_data=metadata, controller=self.mock_controller)

        self.assertEqual(len(tag.data), 1)
        self.assertEqual(tag.data[0]['@Format'], 'L5K')

    def test_data_property_list(self):
        """Test data property with list of data items"""
        metadata = self.valid_metadata.copy()
        metadata['Data'] = [{'@Format': 'L5K'}, {'@Format': 'Decorated'}]

        tag = Tag(meta_data=metadata, controller=self.mock_controller)

        self.assertEqual(len(tag.data), 2)

    def test_decorated_data_property(self):
        """Test decorated_data property"""
        metadata = self.valid_metadata.copy()
        metadata['Data'] = [
            {'@Format': 'L5K', 'Value': '0'},
            {'@Format': 'Decorated', 'Structure': {}}
        ]

        tag = Tag(meta_data=metadata, controller=self.mock_controller)

        decorated = tag.decorated_data
        self.assertEqual(decorated['@Format'], 'Decorated')

    def test_l5k_data_property(self):
        """Test l5k_data property"""
        metadata = self.valid_metadata.copy()
        metadata['Data'] = [
            {'@Format': 'L5K', 'Value': '0'},
            {'@Format': 'Decorated', 'Structure': {}}
        ]

        tag = Tag(meta_data=metadata, controller=self.mock_controller)

        l5k = tag.l5k_data
        self.assertEqual(l5k['@Format'], 'L5K')

    def test_scope_property(self):
        """Test scope property for different container types"""
        # Test controller scope
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)
        tag._container = self.mock_controller
        self.assertEqual(tag.scope, plc_meta.LogixTagScope.CONTROLLER)

    def test_get_alias_string_no_alias(self):
        """Test get_alias_string method without alias"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)
        tag.name = 'TestTag'

        result = tag.get_alias_string()
        self.assertEqual(result, 'TestTag')

    def test_get_alias_string_with_additional_elements(self):
        """Test get_alias_string method with additional elements"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)
        tag.name = 'TestTag'

        result = tag.get_alias_string('.Member')
        self.assertEqual(result, 'TestTag.Member')

    def test_get_base_tag_no_alias(self):
        """Test get_base_tag method without alias"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        result = tag.get_base_tag()
        self.assertEqual(result, tag)

    def test_get_parent_tag_no_alias(self):
        """Test get_parent_tag static method without alias"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        result = Tag.get_parent_tag(tag)
        self.assertIsNone(result)

    def test_datavalue_members_property_empty(self):
        """Test datavalue_members property with no decorated data"""
        tag = Tag(meta_data=self.valid_metadata, controller=self.mock_controller)

        self.assertEqual(tag.datavalue_members, [])

    def test_endpoint_operands_property_no_datatype(self):
        """Test endpoint_operands property with no datatype"""
        metadata = self.valid_metadata.copy()
        metadata['@DataType'] = ''

        tag = Tag(meta_data=metadata, controller=self.mock_controller)

        self.assertEqual(tag.endpoint_operands, [])

    def test_init_with_container_program(self):
        """Test initialization with Program container"""
        from pyrox.models.plc.program import Program
        mock_program = Mock(spec=Program)

        tag = Tag(container=mock_program)

        self.assertEqual(tag.container, mock_program)
