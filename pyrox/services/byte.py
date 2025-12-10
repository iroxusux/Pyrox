"""Byte services and utilies.
"""
from collections import Counter
import string
import re
from typing import Optional, Union

from pyrox.services.logging import LoggingManager

LOGGER = LoggingManager.get_or_create_logger(__name__)


def analyze_byte_stream(data: Union[bytes, bytearray],
                        sample_size: int = 1024) -> dict:
    """Analyze byte stream and provide statistics for debugging.

    Args:
        data: The byte data to analyze
        sample_size: Number of bytes to analyze for patterns (0 for all)

    Returns:
        Dictionary with analysis results
    """
    if not isinstance(data, (bytes, bytearray)):
        return {"error": f"Invalid data type: {type(data)}"}

    if not data:
        return {"error": "Empty byte stream"}

    # Use sample or full data
    sample = data[:sample_size] if sample_size > 0 else data

    analysis = {
        "total_size": len(data),
        "sample_size": len(sample),
        "byte_distribution": {},
        "printable_chars": 0,
        "null_bytes": 0,
        "high_bytes": 0,
        "entropy": 0.0,
        "possible_text": False,
        "possible_formats": [],
        "patterns": []
    }

    # Count byte occurrences
    for b in sample:
        analysis["byte_distribution"][b] = analysis["byte_distribution"].get(b, 0) + 1

        if 32 <= b <= 126:  # Printable ASCII
            analysis["printable_chars"] += 1
        elif b == 0:
            analysis["null_bytes"] += 1
        elif b > 127:
            analysis["high_bytes"] += 1

    # Calculate basic statistics
    total_sample = len(sample)
    if total_sample > 0:
        analysis["printable_percentage"] = (analysis["printable_chars"] / total_sample) * 100
        analysis["null_percentage"] = (analysis["null_bytes"] / total_sample) * 100
        analysis["high_byte_percentage"] = (analysis["high_bytes"] / total_sample) * 100

        # Simple entropy calculation
        import math
        entropy = 0
        for count in analysis["byte_distribution"].values():
            p = count / total_sample
            if p > 0:
                entropy -= p * math.log2(p)
        analysis["entropy"] = entropy

    # Determine if likely text
    analysis["possible_text"] = analysis.get("printable_percentage", 0) > 80

    # Check for common file format signatures
    if len(data) >= 4:
        header = data[:10]  # Check first 10 bytes

        if header.startswith(b'PK'):
            analysis["possible_formats"].append("ZIP/JAR/Office Document")
        elif header.startswith(b'%PDF'):
            analysis["possible_formats"].append("PDF")
        elif header.startswith(b'\x89PNG'):
            analysis["possible_formats"].append("PNG Image")
        elif header.startswith(b'GIF8'):
            analysis["possible_formats"].append("GIF Image")
        elif header.startswith(b'\xff\xd8\xff'):
            analysis["possible_formats"].append("JPEG Image")
        elif header.startswith(b'RIFF'):
            analysis["possible_formats"].append("WAV/AVI")
        elif header.startswith(b'<?xml'):
            analysis["possible_formats"].append("XML")
        elif b'EPLAN' in header:
            analysis["possible_formats"].append("EPLAN Binary")
        elif header.startswith(b'SQLite'):
            analysis["possible_formats"].append("SQLite Database")

    # Look for repeating patterns
    if len(sample) >= 8:
        # Check for simple repeating patterns
        for pattern_len in [1, 2, 4, 8]:
            if len(sample) >= pattern_len * 3:
                pattern = sample[:pattern_len]
                if sample[pattern_len:pattern_len*2] == pattern and sample[pattern_len*2:pattern_len*3] == pattern:
                    analysis["patterns"].append(f"Repeating {pattern_len}-byte pattern: {pattern.hex()}")

    return analysis


def bytes_to_readable_hex_dump(data: Union[bytes, bytearray],
                               chunk_size: int = 16,
                               show_ascii: bool = True,
                               show_offset: bool = True,
                               show_hex: bool = True,
                               max_bytes: Optional[int] = None) -> str:
    """Convert byte stream to human-readable format for debugging.

    Args:
        data: The byte data to convert
        chunk_size: Number of bytes per line (default 16)
        show_ascii: Whether to show ASCII representation
        show_offset: Whether to show byte offset numbers
        show_hex: Whether to show hexadecimal representation
        max_bytes: Maximum number of bytes to display (None for all)

    Returns:
        Formatted string representation of the byte data
    """
    if not isinstance(data, (bytes, bytearray)):
        return f"Invalid data type: {type(data)} (expected bytes or bytearray)"

    if not data:
        return "Empty byte stream"

    # Limit data if max_bytes specified
    original_length = len(data)
    if max_bytes and len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    else:
        truncated = False

    lines = []

    # Header with data info
    header = f"Byte stream ({original_length} bytes"
    if truncated:
        header += f", showing first {len(data)}"
    header += ")"
    lines.append(header)
    lines.append("-" * len(header))

    # Process data in chunks
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        line_parts = []

        # Add offset
        if show_offset:
            line_parts.append(f"{i:08x}")

        # Add hex representation
        if show_hex:
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            # Pad hex part to consistent width
            hex_width = chunk_size * 3 - 1  # 2 chars per byte + 1 space, minus last space
            hex_part = hex_part.ljust(hex_width)
            line_parts.append(hex_part)

        # Add ASCII representation
        if show_ascii:
            ascii_part = ""
            for b in chunk:
                if 32 <= b <= 126:  # Printable ASCII range
                    ascii_part += chr(b)
                else:
                    ascii_part += "."
            line_parts.append(f"|{ascii_part}|")

        lines.append("  ".join(line_parts))

    if truncated:
        lines.append(f"... ({original_length - len(data)} more bytes)")

    return "\n".join(lines)


def convert_bytes_to_str(data: bytes) -> str:
    """Convert bytes to string, handling different encodings."""
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return data.decode('latin-1')
        except UnicodeDecodeError:
            return data.decode('utf-8', errors='ignore')


def debug_bytes(data: Union[bytes, bytearray],
                detailed: bool = True,
                max_display: int = 1024) -> str:
    """Complete debugging output for byte stream.

    Args:
        data: The byte data to debug
        detailed: Whether to include detailed analysis
        max_display: Maximum bytes to display in hex dump

    Returns:
        Complete debugging information as string
    """
    if not isinstance(data, (bytes, bytearray)):
        return f"Error: Invalid data type {type(data)}"

    output = []

    # Basic info
    output.append("Byte Stream Debug Info")
    output.append("=" * 50)

    if detailed:
        # Analysis
        analysis = analyze_byte_stream(data, max_display)
        output.append(f"Total size: {analysis['total_size']} bytes")
        output.append(f"Printable chars: {analysis.get('printable_percentage', 0):.1f}%")
        output.append(f"Null bytes: {analysis.get('null_percentage', 0):.1f}%")
        output.append(f"Entropy: {analysis.get('entropy', 0):.2f}")
        output.append(f"Possible text: {analysis.get('possible_text', False)}")

        if analysis.get('possible_formats'):
            output.append(f"Detected formats: {', '.join(analysis['possible_formats'])}")

        if analysis.get('patterns'):
            output.append("Patterns found:")
            for pattern in analysis['patterns']:
                output.append(f"  - {pattern}")

        output.append("")

    # Hex dump
    output.append("Hex Dump:")
    output.append("-" * 20)
    hex_dump = bytes_to_readable_hex_dump(data, max_bytes=max_display)
    output.append(hex_dump)

    return output


def remove_non_ascii_bytes(data: bytes) -> bytes:
    """Remove non-ASCII bytes from byte stream."""
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("Input must be bytes or bytearray")
    return bytes(b for b in data if 32 <= b <= 126 or b in (9, 10, 13))  # Keep printable and whitespace


def remove_null_bytes(data: bytes) -> bytes:
    """Remove null bytes from byte stream."""
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError("Input must be bytes or bytearray")
    return data.replace(b'\x00', b'')


def filter_noise_from_string(text: str,
                             min_word_length: int = 3,
                             min_line_length: int = 8,
                             min_printable_ratio: float = 0.8,
                             remove_repeated_chars: bool = True,
                             keep_structured_data: bool = True) -> str:
    """Filter noise from string converted from binary data.

    Args:
        text: The string to filter
        min_word_length: Minimum length for words to keep
        min_line_length: Minimum line length to keep
        min_printable_ratio: Minimum ratio of printable characters per line
        remove_repeated_chars: Remove lines with too many repeated characters
        keep_structured_data: Keep lines that look like structured data

    Returns:
        Filtered string
    """
    if not text:
        return ""

    lines = text.splitlines()
    filtered_lines = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Skip lines that are too short
        if len(line) < min_line_length:
            continue

        # Check printable character ratio
        printable_count = sum(1 for c in line if c in string.printable)
        if printable_count / len(line) < min_printable_ratio:
            continue

        # Skip lines with too many repeated characters (likely noise)
        if remove_repeated_chars and _is_repetitive_noise(line):
            continue

        # Keep structured data patterns
        if keep_structured_data and _looks_like_structured_data(line):
            filtered_lines.append(line)
            continue

        # Filter by meaningful content
        if _contains_meaningful_content(line, min_word_length):
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)


def _is_repetitive_noise(line: str, max_repeat_ratio: float = 0.5) -> bool:
    """Check if line contains too many repeated characters."""
    if len(line) < 4:
        return False

    # Count character frequencies
    char_counts = Counter(line)
    most_common_char, most_common_count = char_counts.most_common(1)[0]

    # If one character dominates, it's likely noise
    if most_common_count / len(line) > max_repeat_ratio:
        return True

    # Check for repeating patterns
    for pattern_len in range(1, min(6, len(line) // 3)):
        pattern = line[:pattern_len]
        if line.count(pattern) > len(line) // pattern_len * 0.7:
            return True

    return False


def _looks_like_structured_data(line: str) -> bool:
    """Check if line looks like structured data (XML, JSON, etc.)."""
    structured_patterns = [
        r'<[^>]+>',  # XML tags
        r'{\s*"[^"]+"\s*:',  # JSON objects
        r'\[[^\]]+\]',  # Arrays/lists
        r'[A-Z][A-Z0-9_]+\s*=',  # Constants/assignments
        r'\b[A-Z][a-zA-Z0-9]*\.[A-Z][a-zA-Z0-9]*',  # Namespaced identifiers
        r'[0-9]{2,}:[0-9]{2,}',  # Timestamps or references
        r'\b[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}',  # GUIDs/UUIDs
    ]

    for pattern in structured_patterns:
        if re.search(pattern, line):
            return True
    return False


def _contains_meaningful_content(line: str, min_word_length: int = 3) -> bool:
    """Check if line contains meaningful words."""
    # Split into potential words
    words = re.findall(r'[a-zA-Z]{3,}', line)

    if not words:
        return False

    # Check for meaningful word patterns
    meaningful_words = 0
    for word in words:
        if len(word) >= min_word_length:
            # Check if word has reasonable vowel/consonant distribution
            vowels = sum(1 for c in word.lower() if c in 'aeiou')
            if vowels > 0 and vowels < len(word):
                meaningful_words += 1

    return meaningful_words > 0


def extract_meaningful_strings(
    data: bytes,
    min_length: int = 4,
    encodings: list = None
) -> list:
    """Extract meaningful strings from binary data using multiple techniques."""
    if encodings is None:
        encodings = ['utf-8', 'utf-16le', 'utf-16be', 'ascii', 'latin1']

    meaningful_strings = []

    for encoding in encodings:
        try:
            # Try different encoding approaches
            decoded = data.decode(encoding, errors='ignore')

            # Extract continuous alphabetic strings
            strings = re.findall(r'[a-zA-Z]{' + str(min_length) + r',}', decoded)
            meaningful_strings.extend(strings)

            # Extract mixed alphanumeric strings
            mixed_strings = re.findall(r'[a-zA-Z0-9_\-\.]{' + str(min_length) + r',}', decoded)
            meaningful_strings.extend(mixed_strings)

        except Exception:
            LOGGER.error(f"Decoding error with {encoding}")
            continue

    # Remove duplicates and filter
    unique_strings = list(set(meaningful_strings))
    return [s for s in unique_strings if _is_likely_meaningful(s)]


def _is_likely_meaningful(s: str) -> bool:
    """Check if a string is likely meaningful content."""
    # Too short or too long
    if len(s) < 3 or len(s) > 200:
        return False

    # Must contain some letters
    if not re.search(r'[a-zA-Z]', s):
        return False

    # Check character variety (not just repeating characters)
    unique_chars = len(set(s.lower()))
    if unique_chars < max(2, len(s) // 4):
        return False

    # Check for common meaningless patterns
    noise_patterns = [
        r'^[\.]+$',  # All dots
        r'^[_]+$',   # All underscores
        r'^[0-9]+$',  # All numbers
        r'^(.)\1{5,}',  # Same character repeated 6+ times
    ]

    for pattern in noise_patterns:
        if re.match(pattern, s):
            return False

    return True


def advanced_string_extraction(
    data: bytes,
    chunk_size: int = 1024,
    overlap: int = 100
) -> str:
    """Advanced string extraction with sliding window approach."""
    results = []

    # Process data in overlapping chunks to catch strings that span boundaries
    for i in range(0, len(data), chunk_size - overlap):
        chunk = data[i:i + chunk_size]

        # Try multiple extraction methods
        strings = extract_meaningful_strings(chunk)
        results.extend(strings)

        # Also try null-byte splitting (common in binary formats)
        null_split_strings = []
        for part in chunk.split(b'\x00'):
            if len(part) > 4:
                try:
                    decoded = part.decode('utf-8', errors='ignore').strip()
                    if decoded and _is_likely_meaningful(decoded):
                        null_split_strings.append(decoded)
                except Exception:
                    pass
        results.extend(null_split_strings)

    # Remove duplicates and join
    unique_results = list(set(results))
    return '\n'.join(sorted(unique_results, key=len, reverse=True))


def context_aware_filtering(text: str, context_keywords: list = None) -> str:
    """Filter strings based on contextual relevance."""
    if context_keywords is None:
        # Default keywords for EPLAN/engineering contexts
        context_keywords = [
            'device', 'connection', 'wire', 'cable', 'function', 'page',
            'project', 'terminal', 'signal', 'power', 'input', 'output',
            'module', 'controller', 'sensor', 'actuator', 'valve', 'motor'
        ]

    lines = text.splitlines()
    scored_lines = []

    for line in lines:
        score = 0
        line_lower = line.lower()

        # Score based on keyword matches
        for keyword in context_keywords:
            if keyword in line_lower:
                score += 10

        # Score based on structure patterns
        if re.search(r'[A-Z][0-9]+', line):  # Device references like M1, Q5
            score += 5
        if re.search(r'[0-9]+\.[0-9]+', line):  # Version numbers or coordinates
            score += 3
        if ':' in line:  # Key-value pairs
            score += 2
        if re.search(r'\b[A-Z]{2,}\b', line):  # Acronyms
            score += 2

        scored_lines.append((score, line))

    # Keep lines with score above threshold
    threshold = 2
    filtered_lines = [line for score, line in scored_lines if score >= threshold]

    return '\n'.join(filtered_lines)


# Enhanced version of your existing functions
def enhanced_convert_bytes_to_filtered_string(data: bytes,
                                              apply_noise_filtering: bool = True,
                                              context_keywords: list = None) -> str:
    """Convert bytes to string with comprehensive noise filtering."""
    # Start with your existing approach
    trimmed_bytes = remove_null_bytes(data)
    trimmed_bytes = remove_non_ascii_bytes(trimmed_bytes)
    string_data = convert_bytes_to_str(trimmed_bytes)

    if not apply_noise_filtering:
        return string_data

    # Apply noise filtering
    filtered_data = filter_noise_from_string(string_data)

    # Apply context-aware filtering if keywords provided
    if context_keywords:
        filtered_data = context_aware_filtering(filtered_data, context_keywords)

    return filtered_data
