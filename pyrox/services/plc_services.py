""" plc_services
    """
from __future__ import annotations
import winreg


import os
import re
from typing import Optional
import xmltodict
import lxml.etree
from xml.sax.saxutils import unescape

from .file import save_file
from .xml import dict_from_xml_file


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
    if not isinstance(file_location, str):
        try:
            file_location = str(file_location)
        except Exception as e:
            raise ValueError('file_location must be a string!') from e

    if not file_location.endswith('.L5X'):
        raise ValueError('can only parse .L5X files!')

    return dict_from_xml_file(file_location)


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
              unescape(xmltodict.unparse(controller,
                                         preprocessor=preprocessor,
                                         pretty=True)))


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
    if key in KEEP_CDATA_SECTION:
        if isinstance(value, dict) and '#text' in value:
            value['#text'] = cdata(value['#text'])
        elif isinstance(value, list):
            for i, v in enumerate(value):
                _, value[i] = preprocessor(key, v)
        elif isinstance(value, str):
            value = cdata(value)
    return key, value


def weird_rockwell_escape_sequence(xml_string: str) -> str:
    """
    Replace all '<' characters that are not inside CDATA sections with '&lt;'.
    """
    def replacer(match):
        text = match.group(0)
        if text.startswith('<![CDATA['):
            return text  # leave CDATA untouched
        else:
            return text.replace('<', '&lt;')

    # Regex: match CDATA sections or text between them
    pattern = re.compile(r'<!\[CDATA\[.*?\]\]>|[^<]+|<', re.DOTALL)
    return ''.join(replacer(m) for m in pattern.finditer(xml_string))


def find_rslogix_installations():
    """
    Search Windows registry for installed RSLogix 5000 or Studio 5000 versions.
    Returns a list of dicts with 'name', 'version', and 'install_path'.
    """
    installations = []
    # Registry paths to check
    reg_paths = [
        r"SOFTWARE\Rockwell Software\RSLogix 5000",
        r"SOFTWARE\Rockwell Software\Studio 5000",
        r"SOFTWARE\WOW6432Node\Rockwell Software\RSLogix 5000",
        r"SOFTWARE\WOW6432Node\Rockwell Software\Studio 5000",
    ]
    # Try both HKEY_LOCAL_MACHINE and HKEY_CURRENT_USER
    hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]

    for hive in hives:
        for reg_path in reg_paths:
            try:
                with winreg.OpenKey(hive, reg_path) as key:
                    # Enumerate subkeys (each version)
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    install_path, _ = winreg.QueryValueEx(subkey, "InstallPath")
                                except FileNotFoundError:
                                    install_path = None
                                installations.append({
                                    "name": reg_path.split("\\")[-1],
                                    "version": subkey_name,
                                    "install_path": install_path
                                })
                            i += 1
                        except OSError:
                            break
            except FileNotFoundError:
                continue
    return installations
