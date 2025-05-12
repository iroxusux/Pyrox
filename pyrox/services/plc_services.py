""" plc_services
    Create and manage PLC specific l5x (xml) modules/services, etc.
    """
from collections import defaultdict
import re
from typing import Optional
import xml.etree.ElementTree as ET


import xmltodict
import lxml.etree
from xml.sax.saxutils import unescape


from ..services.file import save_file
from ..types.plc import Controller


OTE_OPERAND_RE_PATTERN = r"(?:OTE\()(.*)(?:\))"
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


def controller_dict_from_file(file_location: str) -> Optional[dict]:
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
    try:
        xml_str: str = get_xml_string_from_file(file_location)
        if not xml_str:
            return None
        xml_str = xml_str.replace("<![CDATA[]]>", "<![CDATA[//]]>")
        return xmltodict.parse(xml_str)
    except KeyError:
        return None


def dict_to_controller_file(controller: dict,
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


def find_diagnostic_rungs(ctrl: Controller):

    diagnostic_rungs = []

    for program in ctrl.programs:
        for routine in program.routines:
            for rung in routine.rungs:
                if rung.comment is not None and '<@DIAG>' in rung.comment:
                    diagnostic_rungs.append(rung)
                else:
                    for instruction in rung.instructions:
                        if 'JSR' in instruction and 'zZ999_Diagnostics' in instruction:
                            diagnostic_rungs.append(rung)
                            break

    return diagnostic_rungs


def find_redundant_otes(ctrl: Controller,
                        include_all_coils=False):
    """Find redundant OTE instructions in the L5X file"""
    # Dictionary to store OTE operands and their locations
    ote_operands = defaultdict(list)

    # Find all routines in the program
    routines = []

    # Look for Controller/Programs/Program/Routines/Routine
    for program in ctrl.programs:
        for routine in program.routines:
            routines.append((program.name, routine.name, routine))

    # Process each routine
    for program_name, routine_name, routine in routines:

        # Process each rung
        for rung_idx, rung in enumerate(routine.rungs, 1):
            # Find OTE instructions
            ote_elements = [x for x in rung.instructions if 'OTE(' in x]

            # Process each OTE instruction
            for ote in ote_elements:
                # Get the operand (tag name)
                operand = re.findall(OTE_OPERAND_RE_PATTERN, ote)[0]

                if operand:
                    # Store the location information
                    location = {
                        'program': program_name,
                        'routine': routine_name,
                        'rung': rung_idx,
                        'operand': operand
                    }
                    ote_operands[operand].append(location)

    # Filter out operands that are used in only one OTE instruction
    redundant_otes = {operand: locations for operand, locations in ote_operands.items() if len(locations) > 1}

    if include_all_coils is False:
        return redundant_otes
    if include_all_coils is True:
        return (redundant_otes, ote_operands)


def get_xml_string_from_file(file_path):
    try:
        parser = lxml.etree.XMLParser(strip_cdata=False)
        tree = lxml.etree.parse(file_path, parser)
        root = tree.getroot()
        return lxml.etree.tostring(root, encoding='utf-8').decode("utf-8")
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except ET.ParseError:
        print(f"Error: Invalid XML format in {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
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
