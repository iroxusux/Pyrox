"""Unit tests for checklist services."""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from pyrox.services.checklist import compile_checklist_from_md_file


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
        complex_content = """# Complex Checklist Template

## Designer: John Doe
### Integrator: Jane Smith
#### Company: Test Corp

##### Power Distribution Panel

Shut Off The **PDP Panel Disconnect.**
Verify That **xxxPDPxSfty.M.DiscOn** Is Not Active.

*Important Note: Always follow safety procedures*

**Bold text here**

- List item 1
- List item 2
  - Nested item
  
1. Numbered item 1
2. Numbered item 2

> Blockquote text

```
Code block example
var x = 1;
```

[Link example](http://example.com)

| Table | Header |
|-------|--------|
| Cell1 | Cell2  |

---

Final section with multiple lines
and continued text.
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
        self.assertIn('# Complex Checklist Template', content_text)
        self.assertIn('## Designer: John Doe', content_text)
        self.assertIn('### Integrator: Jane Smith', content_text)

        # Check for formatting elements
        self.assertIn('**Bold text here**', content_text)
        self.assertIn('*Important Note:', content_text)

        # Check for list items
        self.assertIn('- List item 1', content_text)
        self.assertIn('1. Numbered item 1', content_text)

        # Check for other elements
        self.assertIn('> Blockquote text', content_text)
        self.assertIn('```', content_text)
        self.assertIn('[Link example]', content_text)
        self.assertIn('| Table | Header |', content_text)

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
        expected_keys = {'file_path', 'line_count', 'content_preview', 'content'}
        self.assertEqual(set(result.keys()), expected_keys)

        # Verify data types
        self.assertIsInstance(result['file_path'], str)
        self.assertIsInstance(result['line_count'], int)
        self.assertIsInstance(result['content_preview'], list)
        self.assertIsInstance(result['content'], list)

        # Verify line count matches actual content length
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


if __name__ == '__main__':
    unittest.main()
