"""Unit tests for checklist services."""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pyrox.services.checklist import (
    compile_checklist_from_md_file,
    _categorize_sections_by_header,
    _get_all_tests,
    _get_sections_tests,
    _strip_new_lines_from_list
)


class TestChecklistServices(unittest.TestCase):
    """Test cases for checklist services."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

        # Create various test markdown files
        self.valid_md_file = os.path.join(self.test_dir, 'valid_checklist.md')
        self.empty_md_file = os.path.join(self.test_dir, 'empty_checklist.md')
        self.complex_md_file = os.path.join(self.test_dir, 'complex_checklist.md')
        self.simple_md_file = os.path.join(self.test_dir, 'simple_checklist.md')

        # Create valid markdown content
        valid_content = """# Test Checklist

## Section 1: Power Tests

### Subsection A: Panel Tests

Turn off the **Main Disconnect**.
Verify that **Power Light** is off.

Check the **Emergency Stop**.
Verify that **System Stops** immediately.

## Section 2: Communication Tests

Test **Network Connection**.
Verify that **Status LED** is green.
"""

        # Create empty file
        empty_content = ""

        # Create complex markdown content with various formatting
        complex_content = """

# Checklist Template

## Designer: John Doe

### Integrator: Jane Smith

#### Indicon LLC

##### Power Distribution Panel

Shut Off The **PDP Panel Disconnect.**
Verify That **xxxPDPxSfty.M.DiscOn** Is Not Active.

Shut Off The **PDP Panel Disconnect.**
Verify That **Manual Intervention Message** Appears.
"*xxxPDPx Control Power Distribution Panel Disconnect Not On. Col#*"

Remove Power From The **Surge Protection Device.**
Verify That **Manual Intervention Message** Appears.
"*xxxPDPx Surge Protection Disconnect Off. Col#*"

Remove Power From **QA01 Circuit Breaker.**
Verify That **Fault Message** Of First Device Appears.
"*xxxxxxx Communication Faulted Col.#*"
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

Remove Power From **1AC01 Circuit Breaker.**
"*xxxxxxx Communication Faulted Col.#*"
Verify That No Other Alarms Appear, And That All Correct Devices Power Off.

##### HMI

Verify **Device IP** Is Correct, And That The **Safety Network Number** Is Unique To This Device.

Verify That The **Requested Packet Interval (RPI)** Is Set To **20ms**

**Remove Communications** To The HMI Enclosure.
Verify That **Fault Message** Appears.
"*HMIx Enclosure Safety IO Comm Fault Col.#*"
Verify That No Other Alarms Appear.

**Remove Communications** To The HMI PanelView.
Verify That **Fault Message** Appears.
"*HMIx PV Communication Heartbeat Lost Col.#*"
Verify That No Other Alarms Appear.

Verify Correct **Input Configuration** In The Devices Properties Pane.

Verify Correct **Test Output Configuration** In The Devices Properties Pane.
"""

        # Create simple markdown content
        simple_content = """# Simple Test

Just a single line of content.
"""

        # Write test files
        with open(self.valid_md_file, 'w', encoding='utf-8') as f:
            f.write(valid_content)

        with open(self.empty_md_file, 'w', encoding='utf-8') as f:
            f.write(empty_content)

        with open(self.complex_md_file, 'w', encoding='utf-8') as f:
            f.write(complex_content)

        with open(self.simple_md_file, 'w', encoding='utf-8') as f:
            f.write(simple_content)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_compile_checklist_from_valid_md_file(self):
        """Test compile_checklist_from_md_file with a valid markdown file."""
        result = compile_checklist_from_md_file(self.valid_md_file)

        # Verify result is a dictionary
        self.assertIsInstance(result, dict)

        # Verify expected keys are present (from default transform function)
        self.assertIn('file_path', result)
        self.assertIn('line_count', result)
        self.assertIn('content_preview', result)
        self.assertIn('content', result)

        # Verify file path is correct
        self.assertEqual(result['file_path'], self.valid_md_file)

        # Verify line count is greater than 0
        self.assertGreater(result['line_count'], 0)

        # Verify content is a list
        self.assertIsInstance(result['content'], list)

        # Verify content preview is limited to first 5 lines
        self.assertLessEqual(len(result['content_preview']), 5)

        # Verify actual content contains expected markdown elements
        content_text = ''.join(result['content'])
        self.assertIn('# Test Checklist', content_text)
        self.assertIn('## Section 1: Power Tests', content_text)
        self.assertIn('**Main Disconnect**', content_text)

    def test_compile_checklist_from_empty_md_file(self):
        """Test compile_checklist_from_md_file with an empty markdown file."""
        result = compile_checklist_from_md_file(self.empty_md_file)

        # Verify result is a dictionary
        self.assertIsInstance(result, dict)

        # Verify file path is correct
        self.assertEqual(result['file_path'], self.empty_md_file)

        # For empty file, line count should be 0 or 1 depending on file ending
        self.assertIn(result['line_count'], [0, 1])

        # Content should be empty or contain single empty string
        if result['line_count'] == 0:
            self.assertEqual(result['content'], [])
        else:
            self.assertEqual(result['content'], [''])

    def test_compile_checklist_from_complex_md_file(self):
        """Test compile_checklist_from_md_file with complex markdown formatting."""
        result = compile_checklist_from_md_file(self.complex_md_file)

        # Verify result is a dictionary
        self.assertIsInstance(result, dict)

        # Verify content contains various markdown elements
        content_text = ''.join(result['content'])

        # Check for headers
        self.assertIn('# Checklist Template', content_text)
        self.assertIn('## Designer: John Doe', content_text)
        self.assertIn('### Integrator: Jane Smith', content_text)

    def test_compile_checklist_from_simple_md_file(self):
        """Test compile_checklist_from_md_file with simple markdown content."""
        result = compile_checklist_from_md_file(self.simple_md_file)

        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['file_path'], self.simple_md_file)

        # Should have minimal content
        content_text = ''.join(result['content'])
        self.assertIn('# Simple Test', content_text)
        self.assertIn('Just a single line of content.', content_text)

    def test_compile_checklist_from_nonexistent_file(self):
        """Test compile_checklist_from_md_file with non-existent file."""
        nonexistent_file = os.path.join(self.test_dir, 'nonexistent.md')

        with self.assertRaises(FileNotFoundError) as context:
            compile_checklist_from_md_file(nonexistent_file)

        # Verify error message contains file path
        self.assertIn('File not found:', str(context.exception))
        self.assertIn(nonexistent_file, str(context.exception))

    def test_compile_checklist_from_directory_path(self):
        """Test compile_checklist_from_md_file with directory path instead of file."""
        with self.assertRaises(FileNotFoundError) as context:
            compile_checklist_from_md_file(self.test_dir)

        self.assertIn('File not found:', str(context.exception))

    def test_compile_checklist_from_none_path(self):
        """Test compile_checklist_from_md_file with None as file path."""
        with self.assertRaises((TypeError, AttributeError)):
            compile_checklist_from_md_file(None)

    def test_compile_checklist_from_empty_string_path(self):
        """Test compile_checklist_from_md_file with empty string as file path."""
        with self.assertRaises(TypeError):
            compile_checklist_from_md_file("")

    def test_compile_checklist_return_type_consistency(self):
        """Test that compile_checklist_from_md_file always returns consistent dict structure."""
        result = compile_checklist_from_md_file(self.valid_md_file)

        # Verify all expected keys are present
        expected_keys = {'file_path', 'line_count', 'content_preview', 'content', 'sections'}
        self.assertEqual(set(result.keys()), expected_keys)

        # Verify data types
        self.assertIsInstance(result['file_path'], str)
        self.assertIsInstance(result['line_count'], int)
        self.assertIsInstance(result['content_preview'], list)
        self.assertIsInstance(result['content'], list)

        # Verify line counts differ since new lines are stripped
        self.assertEqual(result['line_count'], len(result['content']))

    @patch('pyrox.services.checklist.transform_file_to_dict')
    def test_compile_checklist_calls_transform_file_to_dict(self, mock_transform):
        """Test that compile_checklist_from_md_file properly calls transform_file_to_dict."""
        expected_result = {
            'file_path': self.valid_md_file,
            'line_count': 10,
            'content_preview': ['# Test'],
            'content': ['# Test\n', 'Content\n']
        }
        mock_transform.return_value = expected_result

        result = compile_checklist_from_md_file(self.valid_md_file)

        # Verify transform_file_to_dict was called with correct arguments
        mock_transform.assert_called_once_with(self.valid_md_file)

        # Verify result is what was returned by the mock
        self.assertEqual(result, expected_result)

    @patch('pyrox.services.checklist.transform_file_to_dict')
    def test_compile_checklist_propagates_exceptions(self, mock_transform):
        """Test that compile_checklist_from_md_file propagates exceptions from transform_file_to_dict."""
        # Test FileNotFoundError propagation
        mock_transform.side_effect = FileNotFoundError("Mock file not found")

        with self.assertRaises(FileNotFoundError) as context:
            compile_checklist_from_md_file(self.valid_md_file)

        self.assertIn("Mock file not found", str(context.exception))

        # Test other exceptions
        mock_transform.side_effect = PermissionError("Mock permission denied")

        with self.assertRaises(PermissionError) as context:
            compile_checklist_from_md_file(self.valid_md_file)

        self.assertIn("Mock permission denied", str(context.exception))

    def test_compile_checklist_with_unicode_content(self):
        """Test compile_checklist_from_md_file with Unicode characters."""
        unicode_md_file = os.path.join(self.test_dir, 'unicode_checklist.md')
        unicode_content = """# Checklist with Unicode

## Testing Special Characters: αβγδε

### Check Items:
- Test with émojis: 🔧⚡🔍
- Test with accénted characters: café, naïve, résumé
- Test with symbols: ©®™€£¥

**Important**: Ensure proper ëncoding handling.
"""

        with open(unicode_md_file, 'w', encoding='utf-8') as f:
            f.write(unicode_content)

        result = compile_checklist_from_md_file(unicode_md_file)

        # Verify Unicode content is properly handled
        content_text = ''.join(result['content'])
        self.assertIn('αβγδε', content_text)
        self.assertIn('🔧⚡🔍', content_text)
        self.assertIn('café, naïve, résumé', content_text)
        self.assertIn('©®™€£¥', content_text)
        self.assertIn('ëncoding', content_text)

    def test_compile_checklist_with_very_large_file(self):
        """Test compile_checklist_from_md_file with a large markdown file."""
        large_md_file = os.path.join(self.test_dir, 'large_checklist.md')

        # Create a large file with repetitive content
        large_content = "# Large Checklist\n\n"
        for i in range(1000):
            large_content += f"## Section {i}\n\nTest step {i}: Perform action {i}.\nVerify result {i}.\n\n"

        with open(large_md_file, 'w', encoding='utf-8') as f:
            f.write(large_content)

        result = compile_checklist_from_md_file(large_md_file)

        # Verify large file is handled correctly
        self.assertIsInstance(result, dict)
        self.assertGreater(result['line_count'], 3000)  # Should be many lines
        self.assertEqual(len(result['content_preview']), 5)  # Preview limited to 5 lines
        self.assertEqual(result['line_count'], len(result['content']))

        # Verify content contains expected repeated elements
        content_text = ''.join(result['content'])
        self.assertIn('# Large Checklist', content_text)
        self.assertIn('Section 0', content_text)
        self.assertIn('Section 999', content_text)

    def test_compile_checklist_sections_parsing(self):
        """Test that compile_checklist_from_md_file properly parses sections with ##### headers."""
        result = compile_checklist_from_md_file(self.complex_md_file)

        # Verify sections key is present
        self.assertIn('sections', result)
        self.assertIsInstance(result['sections'], dict)

        # Verify specific sections are extracted
        sections = result['sections']
        self.assertIn('Power Distribution Panel', sections)
        self.assertIn('HMI', sections)

        # Verify each section has the expected structure
        for section_name, section_data in sections.items():
            self.assertIn('lines', section_data)
            self.assertIn('tests', section_data)
            self.assertIsInstance(section_data['lines'], list)
            self.assertIsInstance(section_data['tests'], dict)

    def test_compile_checklist_no_sections_handling(self):
        """Test compile_checklist_from_md_file when there are no ##### headers."""
        result = compile_checklist_from_md_file(self.valid_md_file)

        # Should still have sections key but it should be empty
        self.assertIn('sections', result)
        self.assertIsInstance(result['sections'], dict)
        self.assertEqual(len(result['sections']), 0)

    # Tests for helper methods
    def test_categorize_sections_by_header(self):
        """Test _categorize_sections_by_header function."""
        test_lines = [
            '##### Section 1\n',
            'Line 1 in section 1\n',
            'Line 2 in section 1\n',
            '##### Section 2\n',
            'Line 1 in section 2\n',
            '##### Section 3\n',
            'Line 1 in section 3\n',
            'Line 2 in section 3\n',
            'Line 3 in section 3\n'
        ]

        result = _categorize_sections_by_header(test_lines, '#####')

        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 3)

        # Verify section names
        self.assertIn('Section 1', result)
        self.assertIn('Section 2', result)
        self.assertIn('Section 3', result)

        # Verify section contents
        self.assertEqual(len(result['Section 1']['lines']), 2)
        self.assertEqual(len(result['Section 2']['lines']), 1)
        self.assertEqual(len(result['Section 3']['lines']), 3)

        # Verify specific content
        self.assertIn('Line 1 in section 1\n', result['Section 1']['lines'])
        self.assertIn('Line 2 in section 1\n', result['Section 1']['lines'])
        self.assertIn('Line 1 in section 2\n', result['Section 2']['lines'])

    def test_categorize_sections_by_header_empty_lines(self):
        """Test _categorize_sections_by_header with empty lines."""
        test_lines = ['##### Test Section\n', '', 'Content line\n', '']

        result = _categorize_sections_by_header(test_lines, '#####')

        self.assertIn('Test Section', result)
        self.assertEqual(len(result['Test Section']['lines']), 3)
        self.assertIn('', result['Test Section']['lines'])
        self.assertIn('Content line\n', result['Test Section']['lines'])

    def test_categorize_sections_by_header_no_headers(self):
        """Test _categorize_sections_by_header with no matching headers."""
        test_lines = ['Line 1\n', 'Line 2\n', '## Not matching header\n']

        result = _categorize_sections_by_header(test_lines, '#####')

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_categorize_sections_by_header_different_header(self):
        """Test _categorize_sections_by_header with different header patterns."""
        test_lines = [
            '### Header 1\n',
            'Content 1\n',
            '### Header 2\n',
            'Content 2\n'
        ]

        result = _categorize_sections_by_header(test_lines, '###')

        self.assertEqual(len(result), 2)
        self.assertIn('Header 1', result)
        self.assertIn('Header 2', result)

    def test_get_sections_tests(self):
        """Test _get_sections_tests function."""
        test_lines = [
            'Test Step 1\n',
            'Verify Step 1\n',
            '\n',  # Empty line should reset current_test
            'Test Step 2\n',
            'Verify Step 2\n'
        ]

        result = _get_sections_tests(test_lines)

        # Verify structure
        self.assertIsInstance(result, dict)

        # Each non-empty line should create a test entry
        expected_tests = {'Test Step 1', 'Verify Step 1', 'Test Step 2', 'Verify Step 2'}
        actual_tests = set(result.keys())
        self.assertEqual(actual_tests, expected_tests)

        # Each test should have a 'lines' key with empty list
        for test_name in result:
            self.assertIn('lines', result[test_name])
            self.assertEqual(result[test_name]['lines'], [])

    def test_get_sections_tests_empty_lines_only(self):
        """Test _get_sections_tests with only empty lines."""
        test_lines = ['', '\n', '   \n']

        result = _get_sections_tests(test_lines)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    def test_get_sections_tests_mixed_content(self):
        """Test _get_sections_tests with mixed content including empty lines."""
        test_lines = [
            'Step 1\n',
            '',
            'Step 2\n',
            '   \n',  # Whitespace line
            'Step 3\n'
        ]

        result = _get_sections_tests(test_lines)

        self.assertEqual(len(result), 3)
        self.assertIn('Step 1', result)
        self.assertIn('Step 2', result)
        self.assertIn('Step 3', result)

    def test_get_all_tests(self):
        """Test _get_all_tests function."""
        sections = {
            'Section 1': {
                'lines': ['Test A\n', 'Test B\n', '', 'Test C\n']
            },
            'Section 2': {
                'lines': ['Test X\n', 'Test Y\n']
            }
        }

        # This function modifies the sections dict in place
        _get_all_tests(sections)

        # Verify tests were added to each section
        self.assertIn('tests', sections['Section 1'])
        self.assertIn('tests', sections['Section 2'])

        # Verify test structure
        self.assertIsInstance(sections['Section 1']['tests'], dict)
        self.assertIsInstance(sections['Section 2']['tests'], dict)

        # Verify test content
        section1_tests = sections['Section 1']['tests']
        self.assertIn('Test A', section1_tests)
        self.assertIn('Test B', section1_tests)
        self.assertIn('Test C', section1_tests)

        section2_tests = sections['Section 2']['tests']
        self.assertIn('Test X', section2_tests)
        self.assertIn('Test Y', section2_tests)

    def test_get_all_tests_empty_sections(self):
        """Test _get_all_tests with empty sections."""
        sections = {}

        _get_all_tests(sections)

        # Should not crash and sections should still be empty
        self.assertEqual(len(sections), 0)

    def test_strip_new_lines_from_list(self):
        """Test _strip_new_lines_from_list function."""
        test_list = [
            'Line with content\n',
            '',
            '   ',  # Whitespace only
            'Another line\n',
            '\n',
            'Final line'
        ]

        result = _strip_new_lines_from_list(test_list)

        # Should only contain lines with non-whitespace content
        expected = ['Line with content\n', 'Another line\n', 'Final line']
        self.assertEqual(result, expected)

    def test_strip_new_lines_from_list_all_empty(self):
        """Test _strip_new_lines_from_list with all empty lines."""
        test_list = ['', '   ', '\n', '\t\n']

        result = _strip_new_lines_from_list(test_list)

        self.assertEqual(result, [])

    def test_strip_new_lines_from_list_no_empty_lines(self):
        """Test _strip_new_lines_from_list with no empty lines."""
        test_list = ['Line 1', 'Line 2', 'Line 3']

        result = _strip_new_lines_from_list(test_list)

        self.assertEqual(result, test_list)

    def test_integration_checklist_with_real_template_structure(self):
        """Integration test using structure similar to the actual checklist template."""
        template_md_file = os.path.join(self.test_dir, 'template_checklist.md')
        template_content = """# Checklist Template

## Designer: Test Designer

### Integrator: Test Integrator

#### Test Company

##### Power Distribution Panel

Shut Off The **PDP Panel Disconnect.**
Verify That **xxxPDPxSfty.M.DiscOn** Is Not Active.

Shut Off The **PDP Panel Disconnect.**
Verify That **Manual Intervention Message** Appears.

##### HMI

Verify **Device IP** Is Correct.

Verify That The **Requested Packet Interval (RPI)** Is Set To **20ms**

**Remove Communications** To The HMI Enclosure.
Verify That **Fault Message** Appears.

##### Safety System

Test Safety Circuit 1.
Verify Safety Response 1.

Test Safety Circuit 2.
Verify Safety Response 2.
"""

        with open(template_md_file, 'w', encoding='utf-8') as f:
            f.write(template_content)

        result = compile_checklist_from_md_file(template_md_file)

        # Verify basic structure
        self.assertIn('sections', result)
        sections = result['sections']

        # Verify expected sections
        expected_sections = {'Power Distribution Panel', 'HMI', 'Safety System'}
        actual_sections = set(sections.keys())
        self.assertEqual(actual_sections, expected_sections)

        # Verify each section has tests
        for section_name in expected_sections:
            self.assertIn('tests', sections[section_name])
            self.assertGreater(len(sections[section_name]['tests']), 0)

        # Verify specific content exists
        pdp_tests = sections['Power Distribution Panel']['tests']
        self.assertIn('Shut Off The **PDP Panel Disconnect.**', pdp_tests)
        self.assertIn('Verify That **xxxPDPxSfty.M.DiscOn** Is Not Active.', pdp_tests)

        hmi_tests = sections['HMI']['tests']
        self.assertIn('Verify **Device IP** Is Correct.', hmi_tests)
        self.assertIn('**Remove Communications** To The HMI Enclosure.', hmi_tests)


if __name__ == '__main__':
    unittest.main()
