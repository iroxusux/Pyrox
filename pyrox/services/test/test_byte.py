"""Test suite for byte services and utilities."""

import unittest

from pyrox.services.byte import (
    analyze_byte_stream,
    bytes_to_readable_hex_dump,
    convert_bytes_to_str,
    debug_bytes,
    remove_non_ascii_bytes,
    remove_null_bytes,
    filter_noise_from_string,
    extract_meaningful_strings,
    advanced_string_extraction,
    context_aware_filtering,
    enhanced_convert_bytes_to_filtered_string,
    _is_repetitive_noise,
    _looks_like_structured_data,
    _contains_meaningful_content,
    _is_likely_meaningful,
)


class TestByteServices(unittest.TestCase):
    """Test class for byte services and utilities."""

    def setUp(self):
        """Set up test data."""
        self.sample_text_bytes = b"Hello World! This is a test string."
        self.sample_binary_bytes = b"\x00\x01\x02\xFF\xFE\x03Hello\x00World\x00"
        self.sample_mixed_bytes = b"Device_A01\x00\x00Connection\x00\x89PNG\r\n"
        self.empty_bytes = b""
        self.null_bytes = b"\x00\x00\x00\x00"

    def test_analyze_byte_stream_valid_text(self):
        """Test analyze_byte_stream with text data."""
        result = analyze_byte_stream(self.sample_text_bytes)

        self.assertNotIn("error", result)
        self.assertEqual(result["total_size"], len(self.sample_text_bytes))
        self.assertTrue(result["possible_text"])
        self.assertGreater(result["printable_percentage"], 80)
        self.assertEqual(result["null_bytes"], 0)

    def test_analyze_byte_stream_binary_data(self):
        """Test analyze_byte_stream with binary data."""
        result = analyze_byte_stream(self.sample_binary_bytes)

        self.assertNotIn("error", result)
        self.assertEqual(result["total_size"], len(self.sample_binary_bytes))
        self.assertFalse(result["possible_text"])
        self.assertGreater(result["null_bytes"], 0)
        self.assertGreater(result["high_bytes"], 0)

    def test_analyze_byte_stream_empty_data(self):
        """Test analyze_byte_stream with empty data."""
        result = analyze_byte_stream(self.empty_bytes)

        self.assertIn("error", result)
        self.assertEqual(result["error"], "Empty byte stream")

    def test_analyze_byte_stream_invalid_type(self):
        """Test analyze_byte_stream with invalid data type."""
        result = analyze_byte_stream("invalid")

        self.assertIn("error", result)
        self.assertIn("Invalid data type", result["error"])

    def test_analyze_byte_stream_file_format_detection(self):
        """Test file format detection in analyze_byte_stream."""
        # Test PNG format
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"data"
        result = analyze_byte_stream(png_bytes)
        self.assertIn("PNG Image", result["possible_formats"])

        # Test PDF format
        pdf_bytes = b"%PDF-1.4" + b"data"
        result = analyze_byte_stream(pdf_bytes)
        self.assertIn("PDF", result["possible_formats"])

        # Test ZIP format
        zip_bytes = b"PK\x03\x04" + b"data"
        result = analyze_byte_stream(zip_bytes)
        self.assertIn("ZIP/JAR/Office Document", result["possible_formats"])

    def test_analyze_byte_stream_pattern_detection(self):
        """Test pattern detection in analyze_byte_stream."""
        # Create data with repeating pattern
        pattern_bytes = b"ABCDABCDABCD" + b"extra"
        result = analyze_byte_stream(pattern_bytes)

        self.assertTrue(len(result["patterns"]) > 0)

    def test_analyze_byte_stream_sample_size(self):
        """Test analyze_byte_stream with different sample sizes."""
        large_data = self.sample_text_bytes * 100

        # Test with sample size limit
        result = analyze_byte_stream(large_data, sample_size=50)
        self.assertEqual(result["sample_size"], 50)
        self.assertEqual(result["total_size"], len(large_data))

        # Test with sample size 0 (analyze all)
        result = analyze_byte_stream(large_data, sample_size=0)
        self.assertEqual(result["sample_size"], len(large_data))

    def test_bytes_to_readable_hex_dump_basic(self):
        """Test basic hex dump functionality."""
        result = bytes_to_readable_hex_dump(b"Hello")

        self.assertIn("Byte stream", result)
        self.assertIn("48 65 6c 6c 6f", result)  # "Hello" in hex
        self.assertIn("|Hello|", result)  # ASCII representation
        self.assertIn("00000000", result)  # Offset

    def test_bytes_to_readable_hex_dump_options(self):
        """Test hex dump with different options."""
        test_data = b"Hello World!"

        # Test without ASCII
        result = bytes_to_readable_hex_dump(test_data, show_ascii=False)
        self.assertNotIn("|Hello", result)

        # Test without offset
        result = bytes_to_readable_hex_dump(test_data, show_offset=False)
        self.assertNotIn("00000000", result)

        # Test without hex
        result = bytes_to_readable_hex_dump(test_data, show_hex=False)
        self.assertNotIn("48 65", result)

    def test_bytes_to_readable_hex_dump_max_bytes(self):
        """Test hex dump with max_bytes limit."""
        large_data = b"A" * 100

        result = bytes_to_readable_hex_dump(large_data, max_bytes=10)
        self.assertIn("100 bytes, showing first 10", result)
        self.assertIn("... (90 more bytes)", result)

    def test_bytes_to_readable_hex_dump_invalid_input(self):
        """Test hex dump with invalid input."""
        result = bytes_to_readable_hex_dump("invalid")
        self.assertIn("Invalid data type", result)

        result = bytes_to_readable_hex_dump(b"")
        self.assertEqual(result, "Empty byte stream")

    def test_bytes_to_readable_hex_dump_chunk_size(self):
        """Test hex dump with different chunk sizes."""
        test_data = b"ABCDEFGHIJKLMNOP"  # 16 bytes

        result = bytes_to_readable_hex_dump(test_data, chunk_size=8)
        lines = result.split('\n')
        # Should have header, separator, 2 data lines
        self.assertGreater(len(lines), 3)

    def test_convert_bytes_to_str_utf8(self):
        """Test convert_bytes_to_str with UTF-8 data."""
        utf8_data = "Hello 世界".encode('utf-8')
        result = convert_bytes_to_str(utf8_data)
        self.assertEqual(result, "Hello 世界")

    def test_convert_bytes_to_str_latin1(self):
        """Test convert_bytes_to_str with Latin-1 data."""
        # Create data that's invalid UTF-8 but valid Latin-1
        latin1_data = b'\xe9\xe8\xe7'  # é, è, ç in Latin-1
        result = convert_bytes_to_str(latin1_data)
        self.assertEqual(result, 'éèç')

    def test_convert_bytes_to_str_fallback(self):
        """Test convert_bytes_to_str with invalid encoding (fallback to ignore)."""
        # Data that should cause encoding errors
        invalid_data = b'\xff\xfe\xfd'
        result = convert_bytes_to_str(invalid_data)
        # Should not raise exception and return some result
        self.assertIsInstance(result, str)

    def test_debug_bytes_basic(self):
        """Test basic debug_bytes functionality."""
        result = debug_bytes(self.sample_text_bytes)

        # Should be a list (based on the code structure)
        self.assertIsInstance(result, list)
        self.assertTrue(any("Byte Stream Debug Info" in str(item) for item in result))

    def test_debug_bytes_invalid_input(self):
        """Test debug_bytes with invalid input."""
        result = debug_bytes("invalid")
        self.assertIn("Error: Invalid data type", result)

    def test_debug_bytes_no_details(self):
        """Test debug_bytes without detailed analysis."""
        result = debug_bytes(self.sample_text_bytes, detailed=False)
        self.assertIsInstance(result, list)

    def test_remove_non_ascii_bytes(self):
        """Test remove_non_ascii_bytes function."""
        mixed_data = b"Hello\x00\xff\x01World\t\n\r!"
        result = remove_non_ascii_bytes(mixed_data)

        expected = b"HelloWorld\t\n\r!"  # Should keep printable ASCII and whitespace
        self.assertEqual(result, expected)

    def test_remove_non_ascii_bytes_invalid_input(self):
        """Test remove_non_ascii_bytes with invalid input."""
        with self.assertRaises(ValueError):
            remove_non_ascii_bytes("invalid")

    def test_remove_null_bytes(self):
        """Test remove_null_bytes function."""
        data_with_nulls = b"Hello\x00World\x00\x00Test"
        result = remove_null_bytes(data_with_nulls)

        expected = b"HelloWorldTest"
        self.assertEqual(result, expected)

    def test_remove_null_bytes_invalid_input(self):
        """Test remove_null_bytes with invalid input."""
        with self.assertRaises(ValueError):
            remove_null_bytes("invalid")

    def test_filter_noise_from_string_basic(self):
        """Test basic noise filtering from string."""
        noisy_text = "Good line here\nxxx\nAnother good line\n...\nShort\n" + "A" * 50
        result = filter_noise_from_string(noisy_text)

        self.assertIn("Good line here", result)
        self.assertIn("Another good line", result)
        self.assertNotIn("xxx", result)  # Too repetitive
        self.assertNotIn("Short", result)  # Too short

    def test_filter_noise_from_string_empty(self):
        """Test filter_noise_from_string with empty input."""
        result = filter_noise_from_string("")
        self.assertEqual(result, "")

    def test_filter_noise_from_string_parameters(self):
        """Test filter_noise_from_string with different parameters."""
        text = "Short\nLonger line here\nVery long line with content"

        # Test with different min_line_length
        result = filter_noise_from_string(text, min_line_length=6)
        self.assertNotIn("Short", result)

        # Test with different min_word_length
        result = filter_noise_from_string(text, min_word_length=1)
        self.assertIsInstance(result, str)

    def test_is_repetitive_noise(self):
        """Test _is_repetitive_noise helper function."""
        # Test repetitive strings
        self.assertTrue(_is_repetitive_noise("aaaaaaaaaa"))
        self.assertTrue(_is_repetitive_noise("abababababab"))

        # Test normal strings
        self.assertFalse(_is_repetitive_noise("Hello World"))
        self.assertFalse(_is_repetitive_noise("abc"))  # Too short

    def test_looks_like_structured_data(self):
        """Test _looks_like_structured_data helper function."""
        # Test structured data patterns
        self.assertTrue(_looks_like_structured_data("<tag>content</tag>"))
        self.assertTrue(_looks_like_structured_data('{"key": "value"}'))
        self.assertTrue(_looks_like_structured_data("CONSTANT = value"))
        self.assertTrue(_looks_like_structured_data("12:34:56"))
        self.assertTrue(_looks_like_structured_data("12345678-1234-1234"))

        # Test non-structured data
        self.assertFalse(_looks_like_structured_data("just plain text"))

    def test_contains_meaningful_content(self):
        """Test _contains_meaningful_content helper function."""
        # Test meaningful content
        self.assertTrue(_contains_meaningful_content("Hello world"))
        self.assertTrue(_contains_meaningful_content("Device connection"))

        # Test non-meaningful content
        self.assertFalse(_contains_meaningful_content("123 456 789"))
        self.assertFalse(_contains_meaningful_content("xx"))

    def test_extract_meaningful_strings(self):
        """Test extract_meaningful_strings function."""
        binary_data = b"Hello\x00World\x00Device_A01\x00\xff\x00Connection"
        result = extract_meaningful_strings(binary_data)

        self.assertIsInstance(result, list)
        self.assertTrue(any("Hello" in s for s in result))
        self.assertTrue(any("World" in s for s in result))

    def test_extract_meaningful_strings_custom_encodings(self):
        """Test extract_meaningful_strings with custom encodings."""
        test_data = b"Test\x00Data"
        result = extract_meaningful_strings(test_data, encodings=['ascii', 'utf-8'])

        self.assertIsInstance(result, list)

    def test_extract_meaningful_strings_with_logging(self):
        """Test extract_meaningful_strings with logging on encoding errors."""
        # This should trigger encoding errors and logging
        result = extract_meaningful_strings(b'\xff\xfe', encodings=['utf-8'])
        self.assertIsInstance(result, list)

    def test_is_likely_meaningful(self):
        """Test _is_likely_meaningful helper function."""
        # Test meaningful strings
        self.assertTrue(_is_likely_meaningful("Hello"))
        self.assertTrue(_is_likely_meaningful("Device_A01"))
        self.assertTrue(_is_likely_meaningful("Connection"))

        # Test non-meaningful strings
        self.assertFalse(_is_likely_meaningful("xx"))  # Too short
        self.assertFalse(_is_likely_meaningful("a" * 250))  # Too long
        self.assertFalse(_is_likely_meaningful("123456"))  # No letters
        self.assertFalse(_is_likely_meaningful("aaaaaaa"))  # Repetitive
        self.assertFalse(_is_likely_meaningful("......"))  # All dots
        self.assertFalse(_is_likely_meaningful("______"))  # All underscores

    def test_advanced_string_extraction(self):
        """Test advanced_string_extraction function."""
        test_data = b"Device\x00Connection\x00Terminal\x00Function\x00" * 10
        result = advanced_string_extraction(test_data)

        self.assertIsInstance(result, str)
        self.assertIn("Device", result)
        self.assertIn("Connection", result)

    def test_advanced_string_extraction_parameters(self):
        """Test advanced_string_extraction with different parameters."""
        test_data = b"Test\x00Data" * 100
        result = advanced_string_extraction(test_data, chunk_size=50, overlap=10)

        self.assertIsInstance(result, str)

    def test_context_aware_filtering_default_keywords(self):
        """Test context_aware_filtering with default keywords."""
        text = "Device connection here\nRandom text\nTerminal function\nIrrelevant line"
        result = context_aware_filtering(text)

        self.assertIn("Device connection", result)
        self.assertIn("Terminal function", result)
        # May or may not contain "Irrelevant line" depending on scoring

    def test_context_aware_filtering_custom_keywords(self):
        """Test context_aware_filtering with custom keywords."""
        text = "Custom keyword here\nIrrelevant text\nAnother custom word"
        keywords = ["custom", "keyword"]
        result = context_aware_filtering(text, context_keywords=keywords)

        self.assertIn("Custom keyword", result)

    def test_context_aware_filtering_patterns(self):
        """Test context_aware_filtering with various scoring patterns."""
        text = "M1 device here\nVersion 1.2.3\nKey: value\nACRONYM here\nplain text"
        result = context_aware_filtering(text)

        # These should score well due to patterns
        self.assertIn("M1 device", result)

    def test_enhanced_convert_bytes_to_filtered_string_no_filtering(self):
        """Test enhanced_convert_bytes_to_filtered_string without filtering."""
        test_data = b"Hello\x00World\xffTest"
        result = enhanced_convert_bytes_to_filtered_string(test_data, apply_noise_filtering=False)

        self.assertIsInstance(result, str)
        self.assertIn("Hello", result)

    def test_enhanced_convert_bytes_to_filtered_string_with_filtering(self):
        """Test enhanced_convert_bytes_to_filtered_string with filtering."""
        test_data = b"Device connection\x00\x00Test line\x00Noise\x01\x02"
        result = enhanced_convert_bytes_to_filtered_string(test_data, apply_noise_filtering=True)

        self.assertIsInstance(result, str)

    def test_enhanced_convert_bytes_to_filtered_string_with_context(self):
        """Test enhanced_convert_bytes_to_filtered_string with context keywords."""
        test_data = b"Device connection\x00\x00Random text\x00Terminal function"
        keywords = ["device", "terminal"]
        result = enhanced_convert_bytes_to_filtered_string(
            test_data,
            apply_noise_filtering=True,
            context_keywords=keywords
        )

        self.assertIsInstance(result, str)

    def test_bytearray_support(self):
        """Test that functions properly handle bytearray input."""
        test_data = bytearray(b"Hello World")

        # Test analyze_byte_stream
        result = analyze_byte_stream(test_data)
        self.assertNotIn("error", result)

        # Test bytes_to_readable_hex_dump
        result = bytes_to_readable_hex_dump(test_data)
        self.assertIn("Hello", result)

        # Test debug_bytes
        result = debug_bytes(test_data)
        self.assertIsInstance(result, list)

    def test_edge_cases_entropy_calculation(self):
        """Test entropy calculation edge cases."""
        # Test with uniform distribution (high entropy)
        uniform_data = bytes(range(256))
        result = analyze_byte_stream(uniform_data)
        self.assertGreater(result["entropy"], 7)  # Should be close to 8 for uniform

        # Test with single repeated byte (low entropy)
        repeated_data = b"A" * 100
        result = analyze_byte_stream(repeated_data)
        self.assertLess(result["entropy"], 1)  # Should be close to 0

    def test_large_data_handling(self):
        """Test handling of large data sets."""
        # Create large test data
        large_data = b"Test data with various content. " * 10000

        # Should handle large data without issues
        result = analyze_byte_stream(large_data, sample_size=1000)
        self.assertEqual(result["sample_size"], 1000)
        self.assertEqual(result["total_size"], len(large_data))

    def test_unicode_edge_cases(self):
        """Test Unicode handling in string functions."""
        # Test with emoji and special characters
        unicode_text = "Hello 👋 World 🌍\nDevice ⚡ Connection"
        result = filter_noise_from_string(unicode_text)
        self.assertIsInstance(result, str)

    def test_xml_json_detection(self):
        """Test XML and JSON pattern detection."""
        xml_text = "<device id='1'>Connection</device>"
        self.assertTrue(_looks_like_structured_data(xml_text))

        json_text = '{"device": "connection"}'
        self.assertTrue(_looks_like_structured_data(json_text))


if __name__ == '__main__':
    unittest.main()
