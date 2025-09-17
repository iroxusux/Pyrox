"""EPlan PDF parsing services for extracting electrical schematic information.

This module provides functionality to parse EPlan-generated PDF files containing
electrical schematics for Controls Automation Systems and extract device information,
power structures, network configurations, and I/O mappings.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import zipfile
import tempfile
import os

import sqlite3
import xml.etree.ElementTree as ET
import json

from pyrox.models.abc import SupportsMetaData

from .byte import debug_bytes
from .xml import dict_from_xml_file

PACKAGE_NAME_RE: str = r"(?:PACKAGE )(.*)(?:DESCRIPTION: )(.*)"
SECTION_LETTER_RE: str = r"(?:SECTION\nLETTER:\n)(.*)"
SHEET_NUMBER_RE: str = r"(?:SHEET\nNUMBER:\n)(.*) (.*)(?:\nOF)"


@dataclass
class ELKProject:
    """Represents an EPLAN Electric P8 project."""
    project_name: str
    project_path: str
    devices: Dict[str, Any] = field(default_factory=dict)
    connections: List[Dict] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)
    sheet_details: List[Dict] = field(default_factory=list)
    bom_details: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ELKProject to dictionary format."""
        return {
            'project_name': self.project_name,
            'project_path': self.project_path,
            'devices': self.devices,
            'connections': self.connections,
            'properties': self.properties,
            'bom_details': self.bom_details,
            'sheet_details': self.sheet_details,
            'summary': {
                'total_devices': len(self.devices),
                'total_connections': len(self.connections),
                'total_pages': len(self.sheet_details),
                'total_properties': len(self.properties)
            }
        }


class EPJParser(SupportsMetaData):
    """Parser for EPLAN Electric P8 .elk files."""

    def __getitem__(self, key):
        return self.pxf_root.get(key, None)

    def __init__(
        self,
        meta_data: Optional[Union[str, dict]] = None
    ) -> None:
        super().__init__(meta_data)

    def __setitem__(self, key, value):
        self.pxf_root[key] = value

    @property
    def main_interest_attributes(self) -> dict:
        """Return the key from eplan root that looks like the most promising for project data.
        """
        return self['O14']

    @property
    def project_bom_list(self) -> list[dict]:
        """Get the project BOM dictionary."""
        return self.main_interest_attributes.get('O117', {})

    @property
    def project_design_source(self) -> Optional[str]:
        """Get the project design source if available."""
        return self.project_property_dict.get('@P10015', 'N/A')

    @property
    def project_design_source_address(self) -> Optional[str]:
        """Get the project design source address if available."""
        addr_line1 = self.project_property_dict.get('@P10016', 'N/A')
        addr_line2 = self.project_property_dict.get('@P10017', 'N/A')
        return f"{addr_line1}, {addr_line2}" if addr_line1 != 'N/A' or addr_line2 != 'N/A' else 'N/A'

    @property
    def project_device_list(self) -> dict:
        """Get the project devices dictionary."""
        return self.main_interest_attributes.get('O6', {})

    @property
    def project_factory_name(self) -> Optional[str]:
        """Get the project factory name if available."""
        return self.project_property_dict.get('@P10035', 'N/A')

    @property
    def project_factory_type(self) -> Optional[str]:
        """Get the project factory type if available."""
        return self.project_property_dict.get('@P10032', 'N/A')

    @property
    def project_job_number(self) -> Optional[str]:
        """Get the project job number if available."""
        return self.project_property_dict.get('@P10180', 'N/A')

    @property
    def project_property_dict(self) -> dict:
        """Get the project properties dictionary."""
        return self.main_interest_attributes.get('P11', {})

    @property
    def project_sheet_list(self) -> list[dict]:
        """Get the project sheets dictionary."""
        return self.main_interest_attributes.get('O4', {})

    @property
    def pxf_root(self) -> dict:
        """Get the root metadata dictionary for EPLAN PXF files."""
        return self.meta_data.get('EplanPxfRoot', {})

    @property
    def template_source(self) -> Optional[str]:
        """Get the template source file if available."""
        return self.project_property_dict.get('@P10011', 'N/A')

    def _gather_project_device_names(self) -> List[dict]:
        """Gather all device names from the project."""
        device_dicts: list[dict] = []
        devices = self.project_device_list
        if isinstance(devices, dict):
            devices = [devices]

        for device in devices:
            name = device.get('@A82', '')
            if name == '':
                continue  # Don't process nothing devices

            device_descriptor_dict = device.get('P11', {})
            device_descriptor_meta_string = device_descriptor_dict.get('@P1002', '')
            if device_descriptor_meta_string == '':
                continue  # Don't process devices without descriptor

            device_descriptor_string = device_descriptor_meta_string.split('@')[-1].strip()

            device_dicts.append(
                {
                    'name': name,
                    'data': device,
                    'descriptor': device_descriptor_string
                }
            )

        return device_dicts

    def _gather_project_bom_details(
        self,
        skip_zero_counts: bool = True,
    ) -> List[dict]:
        """Gather all BOM details from the project."""
        bom_dicts: list[dict] = []
        bom_items = self.project_bom_list
        if isinstance(bom_items, dict):
            bom_items = [bom_items]

        for item in bom_items:
            item_bom_meta: dict = item.get('P11', {})
            if not item_bom_meta:
                continue  # Don't process items without metadata

            part_number = item_bom_meta.get('@P22003', '')
            if part_number == '':
                continue  # Don't process items without part number

            description = item_bom_meta.get('@P22004', '').split('@')[-1].strip()
            quantity = item_bom_meta.get('@P2200', 0)
            manufacturer = item_bom_meta.get('@P22007', '')
            bom_dicts.append(
                {
                    'part_number': part_number,
                    'description': description,
                    'quantity': quantity,
                    'manufacturer': manufacturer,
                    'data': item
                }
            )

        return bom_dicts

    def _gather_project_sheet_details(self) -> List[dict]:
        """Gather all sheet details from the project."""
        sheet_dicts: list[dict] = []
        sheets = self.project_sheet_list
        if isinstance(sheets, dict):
            sheets = [sheets]

        for sheet in sheets:
            sheet_props = sheet.get('P11', {})
            sheet_number_dict = sheet.get('P49', {})

            sheet_name = sheet_props.get('@P11011', '').split('@')[-1].strip()
            sheet_number_major = sheet_number_dict.get('@P11012', '')
            sheet_number_minor = sheet_number_dict.get('@P11013', '')
            if sheet_number_major and sheet_number_minor:
                sheet_number = f"{sheet_number_major}.{sheet_number_minor}"
            else:
                sheet_number = sheet_number_major or sheet_number_minor or 'N/A'

            sheet_dicts.append(
                {
                    'name': sheet_name,
                    'number': sheet_number,
                    'data': sheet,
                }
            )

        return sheet_dicts

    def _gather_project_ip_addresses(self) -> List[str]:
        """Gather all IP addresses from the project."""
        ip_addresses: List[str] = []
        for device in self.project_device_list:
            ip_address = device.get('P11', {}).get('@P1009', '')
            if ip_address and ip_address not in ip_addresses:
                ip_addresses.append(ip_address)
        return ip_addresses

    def _parse_elk_project_file(
        self,
        file_path: str,
        project: Optional[ELKProject] = None
    ) -> None:
        """Parse the main project file to extract high-level project information."""
        file_name = os.path.basename(file_path)
        self.logger.info(f"Parsing project file: {file_name}")

        if file_name.lower().endswith(('.xml', 'eox')):
            self._process_xml_file(file_path, project, file_name)

    def parse_epj_file(
        self,
    ) -> Dict[str, Any]:
        """Parse an EPJ file (EPLAN project archive) and return contents as dictionary."""
        project = ELKProject(
            project_name=self.project_factory_name,
            project_path=None
        )

        project.devices = self._gather_project_device_names()
        project.bom_details = self._gather_project_bom_details()
        project.sheet_details = self._gather_project_sheet_details()

        # Return as dictionary
        result = project.to_dict()
        result['meta_data'] = self.meta_data  # Append meta data for debugging
        self._log_parsing_summary(result)
        return result

    def _log_parsing_summary(self, result: Dict[str, Any]) -> None:
        """Log summary of parsing results."""
        summary = result.get('summary', {})
        self.logger.info("Parsing completed:")
        self.logger.info(f"  - Devices: {summary.get('total_devices', 0)}")
        self.logger.info(f"  - Connections: {summary.get('total_connections', 0)}")
        self.logger.info(f"  - Pages: {summary.get('total_pages', 0)}")
        self.logger.info(f"  - Properties: {summary.get('total_properties', 0)}")

    def _process_binary_file(self, file_path: str, project: ELKProject, file_name: str) -> None:
        """Process binary or encoded files."""
        try:
            self.logger.info(f"Processing binary/encoded file: {file_name}")

            with open(file_path, 'rb') as f:
                # Read file info
                f.seek(0, 2)  # Seek to end
                file_size = f.tell()
                f.seek(0)  # Back to beginning

                # Read header for analysis
                header = f.read(min(1024, file_size))

            # Analyze file structure
            file_info = {
                'file_name': file_name,
                'file_size': file_size,
                'file_type': 'binary_or_encoded',
                'header_hex': header[:100].hex(),  # First 100 bytes as hex
            }

            # Try to detect file type from header
            if header.startswith(b'PK'):
                file_info['detected_type'] = 'ZIP/Archive'
            elif header.startswith(b'SQLite'):
                file_info['detected_type'] = 'SQLite Database'
            elif b'EPLAN' in header:
                file_info['detected_type'] = 'EPLAN Binary'
            else:
                file_info['detected_type'] = 'Unknown Binary'

            # Look for text patterns in the binary data
            try:
                # Try to find readable strings
                readable_parts = []
                text_part = header.decode('utf-8', errors='ignore')
                if text_part and len(text_part.strip()) > 10:
                    readable_parts.append(text_part[:200])

                if readable_parts:
                    file_info['readable_content'] = readable_parts

            except Exception as e:
                self.logger.debug(f"Could not extract readable content: {e}")

            # Try to add debug string info if possible
            file_info['debug_header_str'] = debug_bytes(header)

            if project:
                project.properties[f'binary_{file_name}'] = file_info

            # If it might be compressed or encoded, try to process it
            if file_info['detected_type'] == 'ZIP/Archive':
                try:
                    self._try_parse_as_archive(file_path, project)
                except Exception as e:
                    self.logger.debug(f"Could not parse {file_name} as archive: {e}")

        except Exception as e:
            self.logger.error(f"Failed to process binary file {file_name}: {e}")

    def _process_xml_file(self, file_path: str, project: ELKProject, file_name: str) -> None:
        """Process XML file from archive."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            self.logger.info(f"Processing XML file: {file_name}")

            # Store raw XML structure info
            xml_info = {
                'root_tag': root.tag,
                'attributes': root.attrib,
                'child_count': len(list(root)),
                'file_name': file_name
            }

            project.properties[f'xml_{file_name}'] = xml_info

            # Extract devices/functions
            devices = root.findall('.//device') + root.findall('.//function') + root.findall('.//*[@type="device"]')
            for i, device_elem in enumerate(devices):
                device_data = self._parse_xml_device(device_elem)
                if device_data:
                    device_key = f"{file_name}_{device_data.get('id', i)}"
                    project.devices[device_key] = device_data

            # Extract connections
            connections = root.findall('.//connection') + root.findall('.//wire')
            for conn_elem in connections:
                conn_data = self._parse_xml_connection(conn_elem)
                if conn_data:
                    conn_data['source_file'] = file_name
                    project.connections.append(conn_data)

            # Extract pages/sheets
            pages = root.findall('.//page') + root.findall('.//sheet')
            for page_elem in pages:
                page_data = self._parse_xml_page(page_elem)
                if page_data:
                    page_data['source_file'] = file_name
                    project.pages.append(page_data)

        except Exception as e:
            self.logger.error(f"Failed to process XML file {file_name}: {e}")
            self.logger.debug(f"File {file_name} is not valid XML.")
            self.logger.debug("Trying to read as binary file instead.")
            self._process_binary_file(file_path, project, file_name)

    def _process_database_file(self, file_path: str, project: ELKProject, file_name: str) -> None:
        """Process database file from archive."""
        try:
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()

            # Get table structure
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]

            project.properties[f'db_{file_name}_tables'] = tables
            self.logger.info(f"Database {file_name} contains tables: {tables}")

            # Process each table
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]

                    cursor.execute(f"SELECT * FROM {table} LIMIT 100")  # Limit for safety
                    rows = cursor.fetchall()

                    table_data = []
                    for row in rows:
                        table_data.append(dict(zip(columns, row)))

                    # Categorize data based on table name
                    if any(keyword in table.lower() for keyword in ['device', 'function', 'component']):
                        for i, row_data in enumerate(table_data):
                            device_key = f"{file_name}_{table}_{row_data.get('id', i)}"
                            project.devices[device_key] = row_data
                    elif any(keyword in table.lower() for keyword in ['connection', 'wire', 'cable']):
                        for row_data in table_data:
                            row_data['source_file'] = file_name
                            row_data['source_table'] = table
                            project.connections.append(row_data)
                    else:
                        # Store as properties for observation
                        project.properties[f'table_{file_name}_{table}'] = {
                            'columns': columns,
                            'row_count': len(table_data),
                            'sample_data': table_data[:5] if table_data else []
                        }

                except sqlite3.OperationalError as e:
                    self.logger.debug(f"Could not read table {table}: {e}")

            conn.close()

        except Exception as e:
            self.logger.debug(f"Failed to process database file {file_name}: {e}")

    def _process_json_file(self, file_path: str, project: ELKProject, file_name: str) -> None:
        """Process JSON file from archive."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            project.properties[f'json_{file_name}'] = {
                'keys': list(json_data.keys()) if isinstance(json_data, dict) else 'non_dict_data',
                'type': type(json_data).__name__
            }

            # If it's a dictionary, try to extract relevant data
            if isinstance(json_data, dict):
                if 'devices' in json_data:
                    for device_id, device_data in json_data['devices'].items():
                        project.devices[f"{file_name}_{device_id}"] = device_data

                if 'connections' in json_data:
                    for conn_data in json_data['connections']:
                        conn_data['source_file'] = file_name
                        project.connections.append(conn_data)

        except Exception as e:
            self.logger.debug(f"Failed to process JSON file {file_name}: {e}")

    def _parse_xml_device(self, device_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse device/function element from XML."""
        try:
            device_data = {
                'tag': device_elem.tag,
                'attributes': device_elem.attrib.copy(),
                'text': device_elem.text,
                'properties': {}
            }

            # Extract child elements as properties
            for child in device_elem:
                if child.text:
                    device_data['properties'][child.tag] = child.text
                if child.attrib:
                    device_data['properties'][f"{child.tag}_attributes"] = child.attrib

            return device_data

        except Exception as e:
            self.logger.debug(f"Failed to parse XML device: {e}")
            return None

    def _parse_xml_connection(self, conn_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse connection/wire element from XML."""
        try:
            conn_data = {
                'tag': conn_elem.tag,
                'attributes': conn_elem.attrib.copy(),
                'text': conn_elem.text,
                'properties': {}
            }

            # Extract child elements
            for child in conn_elem:
                if child.text:
                    conn_data['properties'][child.tag] = child.text
                if child.attrib:
                    conn_data['properties'][f"{child.tag}_attributes"] = child.attrib

            return conn_data

        except Exception as e:
            self.logger.debug(f"Failed to parse XML connection: {e}")
            return None

    def _parse_xml_page(self, page_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse page/sheet element from XML."""
        try:
            page_data = {
                'tag': page_elem.tag,
                'attributes': page_elem.attrib.copy(),
                'text': page_elem.text,
                'properties': {}
            }

            # Extract child elements
            for child in page_elem:
                if child.text:
                    page_data['properties'][child.tag] = child.text
                if child.attrib:
                    page_data['properties'][f"{child.tag}_attributes"] = child.attrib

            return page_data

        except Exception as e:
            self.logger.debug(f"Failed to parse XML page: {e}")
            return None

    def _extract_xml_properties(self, root: ET.Element) -> Dict[str, str]:
        """Extract properties from XML root."""
        properties = {}
        properties['root_tag'] = root.tag
        properties.update(root.attrib)

        # Look for project-level properties
        for child in root:
            if child.text and child.text.strip():
                properties[child.tag] = child.text.strip()

        return properties

    def _try_parse_as_archive(self, elk_path: str, project: ELKProject) -> bool:
        """Try to parse ELK file as ZIP archive (most common format)."""
        try:
            with zipfile.ZipFile(elk_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                self.logger.info(f"Archive contains {len(file_list)} files")

                # Log archive contents for observation
                project.properties['archive_contents'] = file_list

                # Extract and process relevant files
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_file.extractall(temp_dir)

                    # Look for project files
                    for file_name in file_list:
                        file_path = os.path.join(temp_dir, file_name)

                        if file_name.lower().endswith('.xml'):
                            self._process_xml_file(file_path, project, file_name)
                        elif file_name.lower().endswith(('.db', '.sqlite')):
                            self._process_database_file(file_path, project, file_name)
                        elif file_name.lower().endswith('.json'):
                            self._process_json_file(file_path, project, file_name)

                return True

        except zipfile.BadZipFile:
            self.logger.debug("File is not a valid ZIP archive")
        except Exception as e:
            self.logger.debug(f"Archive parsing failed: {e}")

        return False

    def _try_parse_as_database(self, elk_path: str, project: ELKProject) -> bool:
        """Try to parse ELK file as SQLite database."""
        try:
            conn = sqlite3.connect(elk_path)
            cursor = conn.cursor()

            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]

            if tables:
                self.logger.info(f"Detected database-based ELK file with tables: {tables}")

                # Look for common EPLAN table names
                device_tables = [t for t in tables if 'device' in t.lower() or 'function' in t.lower()]
                connection_tables = [t for t in tables if 'connection' in t.lower() or 'wire' in t.lower()]

                # Extract devices
                for table in device_tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()

                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]

                        for row in rows:
                            device_data = dict(zip(columns, row))
                            project.devices[device_data.get('id', len(project.devices))] = device_data

                    except sqlite3.OperationalError as e:
                        self.logger.debug(f"Could not read table {table}: {e}")

                # Extract connections
                for table in connection_tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()

                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in cursor.fetchall()]

                        for row in rows:
                            conn_data = dict(zip(columns, row))
                            project.connections.append(conn_data)

                    except sqlite3.OperationalError as e:
                        self.logger.debug(f"Could not read table {table}: {e}")

                conn.close()
                return len(project.devices) > 0 or len(project.connections) > 0

        except sqlite3.DatabaseError:
            self.logger.debug("File is not a SQLite database")
        except Exception as e:
            self.logger.debug(f"Database parsing failed: {e}")

        return False

    def _try_parse_as_binary(self, elk_path: str, project: ELKProject) -> bool:
        """Try to parse ELK file as binary format."""
        # This would be similar to your ZW1 binary parsing
        # but adapted for ELK format specifics
        self.logger.debug("Binary ELK parsing not implemented yet")
        return False

    def _try_parse_as_xml(self, elk_path: str, project: ELKProject) -> bool:
        """Try to parse ELK file as XML."""
        try:
            tree = ET.parse(elk_path)
            root = tree.getroot()

            # Look for EPLAN-specific XML structure
            if 'eplan' in root.tag.lower() or 'project' in root.tag.lower():
                self.logger.info("Detected XML-based ELK file")

                # Extract project information
                project.properties = self._extract_xml_properties(root)

                # Extract devices
                devices = root.findall('.//device') or root.findall('.//function')
                for device_elem in devices:
                    device_data = self._parse_xml_device(device_elem)
                    if device_data:
                        project.devices[device_data.get('id', len(project.devices))] = device_data

                # Extract connections
                connections = root.findall('.//connection') or root.findall('.//wire')
                for conn_elem in connections:
                    conn_data = self._parse_xml_connection(conn_elem)
                    if conn_data:
                        project.connections.append(conn_data)

                return len(project.devices) > 0 or len(project.connections) > 0

        except ET.ParseError:
            self.logger.debug("File is not valid XML")
        except Exception as e:
            self.logger.debug(f"XML parsing failed: {e}")

        return False


# Utility function for easy usage
def parse_epj_to_dict(epj_path: str) -> Dict[str, Any]:
    """Convenience function to parse an EPJ file and return dictionary."""
    parser = EPJParser(dict_from_xml_file(epj_path))
    return parser.parse_epj_file()
