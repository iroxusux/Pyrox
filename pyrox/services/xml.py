"""handles XML parsing and validation for Pyrox."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
import lxml.etree
import xml.etree.ElementTree as ET
import xmltodict

import pandas as pd


def dict_from_xml_file(
    file_location: str
) -> Optional[dict]:
    """get a dictionary from a provided file location

    Args:
        file_location (str): file location

    Raises:
        ValueError: if provided file location is not a valid xml file

    Returns:
        dict: file data object
    """
    if isinstance(file_location, Path):
        file_location = str(file_location)

    if not os.path.exists(file_location):
        raise FileNotFoundError(f"File {file_location} does not exist.")

    # use lxml and parse the .l5x xml into a dictionary
    try:
        parser = lxml.etree.XMLParser(strip_cdata=False)
        tree = lxml.etree.parse(file_location, parser)
        root = tree.getroot()
        xml_str = lxml.etree.tostring(root, encoding='utf-8').decode("utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {file_location}")
        return None
    except ET.ParseError:
        print(f"Error: Invalid XML format in {file_location}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    if not xml_str:
        return None

    xml_str = xml_str.replace("<![CDATA[]]>", "<![CDATA[//]]>")
    return xmltodict.parse(xml_str)


def parse_xml(file_location: str) -> dict[str, pd.DataFrame]:
    """Parse an XML file and return its content as a dictionary.

    Args:
        file_location (str): The path to the XML file.

    Returns:
        dict[str, Any]: Parsed XML content as a dictionary.
    """
    return pd.read_excel(file_location, sheet_name=None)


def is_valid_xml_file(file_path: str) -> bool:
    """Check if file is actually XML by examining first few bytes."""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(1024)  # Read first 1KB

        # Check for XML declaration or common XML patterns
        header_lower = header.lower()

        # Look for XML declaration
        if header_lower.startswith(b'<?xml'):
            return True

        # Look for common XML root elements
        xml_patterns = [b'<project', b'<eplan', b'<root', b'<document']
        for pattern in xml_patterns:
            if pattern in header_lower:
                return True

        # Check if it's mostly text (not binary)
        try:
            header.decode('utf-8')
            # If it decodes as UTF-8 and contains '<', might be XML without declaration
            return b'<' in header and b'>' in header
        except UnicodeDecodeError:
            return False

    except Exception as e:
        raise RuntimeError(f"Error reading file {file_path}: {e}")
