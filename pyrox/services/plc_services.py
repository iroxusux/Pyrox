""" plc_services
    """
from __future__ import annotations


import os

from typing import Optional

import xmltodict
import lxml.etree
from xml.sax.saxutils import unescape
import xml.etree.ElementTree as ET


from .file import save_file


KEEP_CDATA_SECTION = [
    'AdditionalHelpText',
    'Comment',
    'Data',
    'DefaultData',
    'Description',
    'Line',
    'RevisionNote',
    'Text',
]


def cdata(s):
    """get cdata of string
    """
    if isinstance(s, str):
        return '<![CDATA[' + s + ']]>'


def l5x_dict_from_file(file_location: str) -> Optional[dict]:
    """get a controller dictionary from a provided .l5x file location

    Args:
        file_location (str): file location (must end in .l5x)

    Raises:
        ValueError: if provided file location is not .L5X

    Returns:
        dict: controller
    """
    if not file_location.endswith('.L5X'):
        raise ValueError('can only parse .L5X files!')

    if not os.path.exists(file_location):
        raise FileNotFoundError

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

    # update c_data sections to create comments from all comment data
    try:
        xml_str = xml_str.replace("<![CDATA[]]>", "<![CDATA[//]]>")
        return xmltodict.parse(xml_str)
    except KeyError:
        return None


def dict_to_xml_file(controller: dict,
                     file_location: str) -> None:
    """save a dictionary "xml" controller back to .L5X

    Args:
        controller (dict): dictionary of parsed xml controller
        file_location (str): location to save controller .l5x to
    """
    save_file(file_location,
              '.L5X',
              'w',
              str(unescape(xmltodict.unparse(controller,
                                             preprocessor=preprocessor,
                                             pretty=True))))


def get_ip_address_from_comm_path(comm_path: str) -> Optional[str]:
    """Extract IP address from a communication path string

    Args:
        comm_path (str): Communication path string

    Returns:
        Optional[str]: Extracted IP address or None if not found
    """
    if not comm_path:
        return None

    parts = comm_path.split('\\')
    for part in reversed(parts):
        ip_address = get_ip_address_from_string(part.strip())
        if ip_address:
            return ip_address
    return None


def get_ip_address_from_string(ip_string: str) -> Optional[str]:
    """Extract IP address from a string

    Args:
        ip_string (str): String containing an IP address

    Returns:
        Optional[str]: Extracted IP address or None if not found
    """
    if not ip_string:
        return None

    parts = ip_string.split('.')
    if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) < 256 for part in parts):
        return ip_string
    return None


def get_rung_text(rung):
    """Extract readable text from a rung if available"""
    text_element = rung.find("./Text")
    if text_element is not None and text_element.text:
        return text_element.text.strip()
    else:
        comment_element = rung.find("./Comment")
        if comment_element is not None and comment_element.text:
            return comment_element.text.strip()
    return "No description available"


def get_xml_string_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    try:
        parser = lxml.etree.XMLParser(strip_cdata=False)
        tree = lxml.etree.parse(file_path, parser)
        root = tree.getroot()
        return lxml.etree.tostring(root, encoding='utf-8').decode("utf-8")
    except (lxml.etree.ParseError, TypeError) as e:
        print(f"Error parsing XML file: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def preprocessor(key, value):
    '''Unneccessary if you've manually wrapped the values. For example,

    xmltodict.unparse({
        'node1': {'node2': '<![CDATA[test]]>', 'node3': 'test'}
    })
    '''

    if key in KEEP_CDATA_SECTION:
        if isinstance(value, dict) and '#text' in value:
            value['#text'] = cdata(value['#text'])
        elif isinstance(value, list):
            for v in value:
                preprocessor(key, v)
        elif isinstance(value, str):
            value = cdata(value)
    return key, value
