"""Unit tests for PLC services."""

import os
import lxml.etree
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import winreg


from pyrox.services.plc import (
    cdata,
    l5x_dict_from_file,
    dict_to_xml_file,
    get_ip_address_from_comm_path,
    get_ip_address_from_string,
    get_rung_text,
    get_xml_string_from_file,
    preprocessor,
    weird_rockwell_escape_sequence,
    find_rslogix_installations,
    KEEP_CDATA_SECTION
)


class TestCDataFunction(unittest.TestCase):
    """Test cases for cdata function."""

    def test_cdata_with_string(self):
        """Test cdata function with string input."""
        result = cdata("test string")
        self.assertEqual(result, "<![CDATA[test string]]>")

    def test_cdata_with_empty_string(self):
        """Test cdata function with empty string."""
        result = cdata("")
        self.assertEqual(result, "<![CDATA[]]>")

    def test_cdata_with_special_characters(self):
        """Test cdata function with special characters."""
        special_text = "Special chars: <>&\"'"
        result = cdata(special_text)
        self.assertEqual(result, "<![CDATA[Special chars: <>&\"']]>")

    def test_cdata_with_non_string(self):
        """Test cdata function with non-string input."""
        result = cdata(123)
        self.assertIsNone(result)

    def test_cdata_with_none(self):
        """Test cdata function with None input."""
        result = cdata(None)
        self.assertIsNone(result)


class TestL5XDictFromFile(unittest.TestCase):
    """Test cases for l5x_dict_from_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_valid_l5x_file(self):
        """Test parsing valid L5X file."""
        l5x_file = os.path.join(self.test_dir, 'test.L5X')
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<RSLogix5000Content>
    <Controller Name="TestController">
        <Tags>
            <Tag Name="TestTag" DataType="BOOL" />
        </Tags>
    </Controller>
</RSLogix5000Content>'''

        with open(l5x_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        with patch('pyrox.services.plc.dict_from_xml_file') as mock_dict:
            mock_dict.return_value = {'RSLogix5000Content': {'Controller': {'@Name': 'TestController'}}}
            result = l5x_dict_from_file(l5x_file)

            self.assertIsInstance(result, dict)
            mock_dict.assert_called_once_with(l5x_file)

    def test_invalid_file_extension(self):
        """Test with invalid file extension."""
        invalid_file = os.path.join(self.test_dir, 'test.txt')

        with self.assertRaises(ValueError) as context:
            l5x_dict_from_file(invalid_file)

        self.assertIn('can only parse .L5X files', str(context.exception))

    def test_non_string_input(self):
        """Test with non-string input that can be converted."""
        from pathlib import Path
        l5x_path = Path(self.test_dir) / 'test.L5X'

        # Create a valid file
        with open(str(l5x_path), 'w') as f:
            f.write('<?xml version="1.0"?><root></root>')

        with patch('pyrox.services.plc.dict_from_xml_file') as mock_dict:
            mock_dict.return_value = {'root': {}}
            result = l5x_dict_from_file(l5x_path)

            self.assertIsInstance(result, dict)
            mock_dict.assert_called_once_with(str(l5x_path))

    def test_unconvertible_input(self):
        """Test with input that cannot be converted to string."""
        with self.assertRaises(ValueError) as context:
            l5x_dict_from_file(object())  # Object that can't be converted to string

        self.assertIn('file_location must be a string', str(context.exception))


class TestDictToXmlFile(unittest.TestCase):
    """Test cases for dict_to_xml_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('pyrox.services.plc.save_file')
    @patch('pyrox.services.plc.xmltodict.unparse')
    def test_dict_to_xml_file(self, mock_unparse, mock_save):
        """Test converting dictionary to XML file."""
        test_dict = {'RSLogix5000Content': {'Controller': {'@Name': 'TestController'}}}
        file_path = os.path.join(self.test_dir, 'output.L5X')

        mock_unparse.return_value = '<RSLogix5000Content><Controller Name="TestController"/></RSLogix5000Content>'

        dict_to_xml_file(test_dict, file_path)

        mock_unparse.assert_called_once_with(test_dict, preprocessor=preprocessor, pretty=True)
        mock_save.assert_called_once()

        # Verify save_file was called with correct parameters
        args, kwargs = mock_save.call_args
        self.assertEqual(args[0], file_path)
        self.assertEqual(args[1], '.L5X')
        self.assertEqual(args[2], 'w')


class TestIPAddressFunctions(unittest.TestCase):
    """Test cases for IP address extraction functions."""

    def test_get_ip_address_from_comm_path_valid(self):
        """Test extracting IP address from valid communication path."""
        test_cases = [
            ("1\\192.168.1.100", "192.168.1.100"),
            ("AB_ETHIP-1\\192.168.0.1\\Backplane\\0", "192.168.0.1"),
            ("192.168.1.50\\Backplane\\1", "192.168.1.50"),
            ("Device\\10.0.0.1\\Port\\192.168.1.1", "192.168.1.1"),  # Should return last valid IP
        ]

        for comm_path, expected_ip in test_cases:
            with self.subTest(comm_path=comm_path):
                result = get_ip_address_from_comm_path(comm_path)
                self.assertEqual(result, expected_ip)

    def test_get_ip_address_from_comm_path_invalid(self):
        """Test extracting IP address from invalid communication path."""
        test_cases = [
            "",
            None,
            "1\\Backplane\\0",
            "AB_ETHIP-1\\InvalidIP\\Backplane\\0",
            "Device\\256.300.400.500\\Port",  # Invalid IP ranges
        ]

        for comm_path in test_cases:
            with self.subTest(comm_path=comm_path):
                result = get_ip_address_from_comm_path(comm_path)
                self.assertIsNone(result)

    def test_get_ip_address_from_string_valid(self):
        """Test extracting IP address from valid strings."""
        test_cases = [
            ("192.168.1.100", "192.168.1.100"),
            ("10.0.0.1", "10.0.0.1"),
            ("172.16.254.1", "172.16.254.1"),
            ("0.0.0.0", "0.0.0.0"),
            ("255.255.255.255", "255.255.255.255"),
        ]

        for ip_string, expected in test_cases:
            with self.subTest(ip_string=ip_string):
                result = get_ip_address_from_string(ip_string)
                self.assertEqual(result, expected)

    def test_get_ip_address_from_string_invalid(self):
        """Test extracting IP address from invalid strings."""
        test_cases = [
            "",
            None,
            "192.168.1",  # Too few parts
            "192.168.1.100.1",  # Too many parts
            "256.1.1.1",  # Invalid range
            "192.168.1.abc",  # Non-numeric
            "not.an.ip.address",
            "192.168.1.-1",  # Negative number
        ]

        for ip_string in test_cases:
            with self.subTest(ip_string=ip_string):
                result = get_ip_address_from_string(ip_string)
                self.assertIsNone(result)


class TestGetRungText(unittest.TestCase):
    """Test cases for get_rung_text function."""

    def test_get_rung_text_with_text_element(self):
        """Test extracting text from rung with Text element."""
        from xml.etree.ElementTree import Element, SubElement

        rung = Element("Rung")
        text_elem = SubElement(rung, "Text")
        text_elem.text = "  Test rung text  "

        result = get_rung_text(rung)
        self.assertEqual(result, "Test rung text")

    def test_get_rung_text_with_comment_element(self):
        """Test extracting text from rung with Comment element when no Text."""
        from xml.etree.ElementTree import Element, SubElement

        rung = Element("Rung")
        comment_elem = SubElement(rung, "Comment")
        comment_elem.text = "  Test comment  "

        result = get_rung_text(rung)
        self.assertEqual(result, "Test comment")

    def test_get_rung_text_with_both_elements(self):
        """Test that Text element takes precedence over Comment."""
        from xml.etree.ElementTree import Element, SubElement

        rung = Element("Rung")
        text_elem = SubElement(rung, "Text")
        text_elem.text = "Text content"
        comment_elem = SubElement(rung, "Comment")
        comment_elem.text = "Comment content"

        result = get_rung_text(rung)
        self.assertEqual(result, "Text content")

    def test_get_rung_text_no_description(self):
        """Test rung with no text or comment elements."""
        from xml.etree.ElementTree import Element

        rung = Element("Rung")

        result = get_rung_text(rung)
        self.assertEqual(result, "No description available")

    def test_get_rung_text_empty_elements(self):
        """Test rung with empty text and comment elements."""
        from xml.etree.ElementTree import Element, SubElement

        rung = Element("Rung")
        text_elem = SubElement(rung, "Text")
        text_elem.text = ""
        comment_elem = SubElement(rung, "Comment")
        comment_elem.text = ""

        result = get_rung_text(rung)
        self.assertEqual(result, "No description available")


class TestGetXmlStringFromFile(unittest.TestCase):
    """Test cases for get_xml_string_from_file function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_xml_string_valid_file(self):
        """Test getting XML string from valid file."""
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <child>content</child>
</root>'''

        xml_file = os.path.join(self.test_dir, 'test.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        result = get_xml_string_from_file(xml_file)
        self.assertIsInstance(result, str)
        self.assertIn('<root>', result)
        self.assertIn('<child>content</child>', result)

    def test_get_xml_string_nonexistent_file(self):
        """Test getting XML string from nonexistent file."""
        nonexistent_file = os.path.join(self.test_dir, 'nonexistent.xml')

        with self.assertRaises(FileNotFoundError):
            get_xml_string_from_file(nonexistent_file)

    def test_get_xml_string_invalid_xml(self):
        """Test getting XML string from invalid XML file."""
        invalid_xml = "<root><unclosed_tag></root>"

        xml_file = os.path.join(self.test_dir, 'invalid.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(invalid_xml)

        with self.assertRaises(lxml.etree.ParseError):
            _ = get_xml_string_from_file(xml_file)

    def test_get_xml_string_with_cdata(self):
        """Test getting XML string preserving CDATA sections."""
        xml_with_cdata = '''<?xml version="1.0"?>
<root>
    <![CDATA[Some CDATA content]]>
</root>'''

        xml_file = os.path.join(self.test_dir, 'cdata.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_with_cdata)

        result = get_xml_string_from_file(xml_file)
        self.assertIsInstance(result, str)
        self.assertIn('CDATA', result)


class TestPreprocessor(unittest.TestCase):
    """Test cases for preprocessor function."""

    def test_preprocessor_cdata_section_string(self):
        """Test preprocessor with CDATA section and string value."""
        key = 'Comment'  # This is in KEEP_CDATA_SECTION
        value = 'Test comment'

        result_key, result_value = preprocessor(key, value)

        self.assertEqual(result_key, key)
        self.assertEqual(result_value, '<![CDATA[Test comment]]>')

    def test_preprocessor_cdata_section_dict(self):
        """Test preprocessor with CDATA section and dict value."""
        key = 'Description'  # This is in KEEP_CDATA_SECTION
        value = {'#text': 'Test description'}

        result_key, result_value = preprocessor(key, value)

        self.assertEqual(result_key, key)
        self.assertEqual(result_value['#text'], '<![CDATA[Test description]]>')

    def test_preprocessor_cdata_section_list(self):
        """Test preprocessor with CDATA section and list value."""
        key = 'Text'  # This is in KEEP_CDATA_SECTION
        value = ['First text', 'Second text']

        result_key, result_value = preprocessor(key, value)

        self.assertEqual(result_key, key)
        self.assertEqual(result_value[0], '<![CDATA[First text]]>')
        self.assertEqual(result_value[1], '<![CDATA[Second text]]>')

    def test_preprocessor_non_cdata_section(self):
        """Test preprocessor with non-CDATA section."""
        key = 'NonCDataKey'
        value = 'Some value'

        result_key, result_value = preprocessor(key, value)

        self.assertEqual(result_key, key)
        self.assertEqual(result_value, value)  # Should remain unchanged

    def test_preprocessor_keep_cdata_sections_list(self):
        """Test that KEEP_CDATA_SECTION contains expected keys."""
        expected_keys = [
            'AdditionalHelpText', 'Comment', 'Data', 'DefaultData',
            'Description', 'Line', 'RevisionNote', 'Text'
        ]

        for key in expected_keys:
            self.assertIn(key, KEEP_CDATA_SECTION)


class TestWeirdRockwellEscapeSequence(unittest.TestCase):
    """Test cases for weird_rockwell_escape_sequence function."""

    def test_escape_simple_xml(self):
        """Test escaping simple XML without CDATA."""
        xml_input = '<tag>content with < character</tag>'
        expected = '&lt;tag>content with &lt; character&lt;/tag>'

        result = weird_rockwell_escape_sequence(xml_input)
        self.assertEqual(result, expected)

    def test_preserve_cdata_sections(self):
        """Test that CDATA sections are preserved."""
        xml_input = '<tag><![CDATA[content with < character]]></tag>'
        expected = '&lt;tag><![CDATA[content with < character]]>&lt;/tag>'

        result = weird_rockwell_escape_sequence(xml_input)
        self.assertEqual(result, expected)

    def test_mixed_cdata_and_regular_content(self):
        """Test mixed CDATA and regular content."""
        xml_input = '<root>before < CDATA<![CDATA[< inside cdata <]]>after < cdata</root>'
        expected = '&lt;root>before &lt; CDATA<![CDATA[< inside cdata <]]>after &lt; cdata&lt;/root>'

        result = weird_rockwell_escape_sequence(xml_input)
        self.assertEqual(result, expected)

    def test_multiple_cdata_sections(self):
        """Test multiple CDATA sections."""
        xml_input = '<root><![CDATA[first < section]]>middle < content<![CDATA[second < section]]></root>'
        expected = '&lt;root><![CDATA[first < section]]>middle &lt; content<![CDATA[second < section]]>&lt;/root>'

        result = weird_rockwell_escape_sequence(xml_input)
        self.assertEqual(result, expected)

    def test_empty_string(self):
        """Test with empty string."""
        result = weird_rockwell_escape_sequence('')
        self.assertEqual(result, '')

    def test_no_angle_brackets(self):
        """Test string without angle brackets."""
        xml_input = 'no brackets here'
        result = weird_rockwell_escape_sequence(xml_input)
        self.assertEqual(result, xml_input)


class TestFindRSLogixInstallations(unittest.TestCase):
    """Test cases for find_rslogix_installations function."""

    @patch('winreg.OpenKey')
    @patch('winreg.EnumKey')
    @patch('winreg.QueryValueEx')
    def test_find_installations_success(self, mock_query, mock_enum, mock_open):
        """Test successful finding of RSLogix installations."""
        # Create a mock registry key
        mock_key = MagicMock()

        # Set up context manager for OpenKey
        mock_open.return_value.__enter__.return_value = mock_key
        mock_open.return_value.__exit__.return_value = None

        # Mock enumeration - return version keys, then raise OSError when done
        # EnumKey gets called multiple times, so we need to handle the sequence properly
        def enum_key_side_effect(key, index):
            if index == 0:
                return 'v32.00'
            elif index == 1:
                return 'v33.00'
            else:
                raise OSError("No more items")  # This is what Windows registry returns

        mock_enum.side_effect = enum_key_side_effect

        # Mock query for install path - return tuple (value, type)
        mock_query.return_value = ('C:\\Program Files\\Rockwell Software\\RSLogix 5000\\v32.00', winreg.REG_SZ)

        result = find_rslogix_installations()

        # Verify it returns a list
        self.assertIsInstance(result, list)

    @patch('winreg.OpenKey')
    @patch('winreg.EnumKey')
    def test_find_installations_enum_error(self, mock_enum, mock_open):
        """Test when EnumKey raises an error immediately."""
        # Mock the context manager
        mock_key = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_key
        mock_open.return_value.__exit__.return_value = None

        # EnumKey raises OSError immediately (no registry keys found)
        mock_enum.side_effect = OSError("No items")

        result = find_rslogix_installations()

        # Should return empty list or handle gracefully
        self.assertIsInstance(result, list)

    @patch('winreg.OpenKey')
    def test_find_installations_no_registry_keys(self, mock_open):
        """Test when no registry keys are found."""
        # Mock registry key not found - OpenKey raises FileNotFoundError
        mock_open.side_effect = FileNotFoundError("Registry key not found")

        result = find_rslogix_installations()

        self.assertIsInstance(result, list)

    @patch('winreg.OpenKey')
    @patch('winreg.EnumKey')
    @patch('winreg.QueryValueEx')
    def test_find_installations_missing_install_path(self, mock_query, mock_enum, mock_open):
        """Test handling of missing InstallPath value."""
        mock_key = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_key
        mock_open.return_value.__exit__.return_value = None

        # Return one version, then stop
        def enum_key_side_effect(key, index):
            if index == 0:
                return 'v32.00'
            else:
                raise OSError("No more items")

        mock_enum.side_effect = enum_key_side_effect

        # InstallPath query fails
        mock_query.side_effect = FileNotFoundError("Value not found")

        result = find_rslogix_installations()

        self.assertIsInstance(result, list)

    def test_find_installations_registry_structure(self):
        """Test that function handles expected registry structure."""
        # This is more of an integration test that calls the real function
        result = find_rslogix_installations()

        # Just verify it returns a list and doesn't crash
        self.assertIsInstance(result, list)

        # If installations are found, verify structure
        for installation in result:
            self.assertIsInstance(installation, dict)
            if installation:  # Only check if not empty
                self.assertIn('name', installation)
                self.assertIn('version', installation)
                self.assertIn('install_path', installation)

    @patch('winreg.OpenKey')
    @patch('winreg.EnumKey')
    @patch('winreg.QueryValueEx')
    def test_find_installations_multiple_hives(self, mock_query, mock_enum, mock_open):
        """Test searching multiple registry hives."""
        mock_key = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_key
        mock_open.return_value.__exit__.return_value = None

        # Simulate finding installations in different attempts
        call_count = 0

        def open_key_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First two calls succeed
                return mock_open.return_value
            else:  # Later calls fail (no more hives/paths to check)
                raise FileNotFoundError("Key not found")

        mock_open.side_effect = open_key_side_effect

        # Mock enumeration for successful registry access
        def enum_key_side_effect(key, index):
            if index == 0:
                return 'v32.00'
            else:
                raise OSError("No more items")

        mock_enum.side_effect = enum_key_side_effect

        # Mock successful path query
        mock_query.return_value = ('C:\\Program Files\\Rockwell Software\\RSLogix 5000\\v32.00', winreg.REG_SZ)

        result = find_rslogix_installations()

        self.assertIsInstance(result, list)

    @patch('winreg.OpenKey')
    @patch('winreg.EnumKey')
    @patch('winreg.QueryValueEx')
    def test_find_installations_error_handling(self, mock_query, mock_enum, mock_open):
        """Test error handling during installation finding."""
        # Create a mock registry key
        mock_key = MagicMock()

        # Set up context manager for OpenKey
        mock_open.return_value.__enter__.return_value = mock_key
        mock_open.return_value.__exit__.return_value = None

        # Mock enumeration - return version keys, then raise OSError when done
        # EnumKey gets called multiple times, so we need to handle the sequence properly
        def enum_key_side_effect(key, index):
            if index == 0:
                return 'v32.00'
            if index == 1:
                return 'v33.00'
            else:
                raise OSError("No more items")  # This is what Windows registry returns

        mock_enum.side_effect = enum_key_side_effect

        # Mock query for install path - first call succeeds, second fails
        mock_query.return_value = [
            ('C:\\Program Files\\Rockwell Software\\RSLogix 5000\\v32.00', winreg.REG_SZ),
            FileNotFoundError("Value not found")
        ]

        result = find_rslogix_installations()

        # Should return a list, and handle the error gracefully
        self.assertIsInstance(result, list)

        # If an installation was found, verify its structure
        if result:
            for installation in result:
                self.assertIsInstance(installation, dict)
                self.assertIn('name', installation)
                self.assertIn('version', installation)
                self.assertIn('install_path', installation)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios combining multiple functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_l5x_round_trip(self):
        """Test loading L5X file and saving it back."""
        # Create a test L5X file
        original_dict = {
            'RSLogix5000Content': {
                '@SchemaRevision': '1.0',
                'Controller': {
                    '@Name': 'TestController',
                    '@ProcessorType': 'CompactLogix',
                    'Tags': {
                        'Tag': [
                            {'@Name': 'Tag1', '@DataType': 'BOOL'},
                            {'@Name': 'Tag2', '@DataType': 'DINT'}
                        ]
                    }
                }
            }
        }

        # Convert to XML and save
        l5x_file = os.path.join(self.test_dir, 'test.L5X')

        with patch('pyrox.services.plc.dict_from_xml_file') as mock_load:
            with patch('pyrox.services.plc.save_file') as mock_save:
                mock_load.return_value = original_dict

                # Load the file
                loaded_dict = l5x_dict_from_file(l5x_file)

                # Save it back
                output_file = os.path.join(self.test_dir, 'output.L5X')
                dict_to_xml_file(loaded_dict, output_file)

                # Verify both operations completed
                mock_load.assert_called_once_with(l5x_file)
                mock_save.assert_called_once()

    def test_xml_processing_with_cdata(self):
        """Test XML processing with CDATA sections."""
        xml_content = '''<?xml version="1.0"?>
<RSLogix5000Content>
    <Controller>
        <Comment><![CDATA[Original comment with < chars]]></Comment>
        <Description>Regular description without those chars</Description>
    </Controller>
</RSLogix5000Content>'''

        xml_file = os.path.join(self.test_dir, 'test_cdata.xml')
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        # Get XML string
        xml_string = get_xml_string_from_file(xml_file)
        self.assertIsNotNone(xml_string)

        # Apply Rockwell escape sequence
        escaped_xml = weird_rockwell_escape_sequence(xml_string)

        # CDATA should be preserved, other < should be escaped
        self.assertIn('<![CDATA[Original comment with < chars]]>', escaped_xml)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
