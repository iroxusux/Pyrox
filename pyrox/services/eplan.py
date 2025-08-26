"""EPlan PDF parsing services for extracting electrical schematic information.

This module provides functionality to parse EPlan-generated PDF files containing
electrical schematics for Controls Automation Systems and extract device information,
power structures, network configurations, and I/O mappings.
"""

from __future__ import annotations
import importlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

try:
    import PyPDF2
    import pdfplumber
    import fitz  # PyMuPDF
except ImportError as e:
    raise ImportError(
        "Required PDF libraries not installed. "
        "Install with: pip install PyPDF2 pdfplumber PyMuPDF"
    ) from e

from pyrox.models.abc.meta import Loggable
from pyrox.services import fuzzy


PACKAGE_NAME_RE: str = r"(?:PACKAGE )(.*)(?:DESCRIPTION: )(.*)"
SECTION_LETTER_RE: str = r"(?:SECTION\nLETTER:\n)(.*)"
SHEET_NUMBER_RE: str = r"(?:SHEET\nNUMBER:\n)(.*) (.*)(?:\nOF)"


@dataclass
class DeviceContact:
    """Represents a contact point on a device."""
    terminal: str
    signal_name: str = ""
    wire_number: str = ""
    device_reference: str = ""
    page_reference: str = ""
    contact_type: str = ""  # NO, NC, COM, etc.


@dataclass
class IODevice:
    """Represents an I/O device in the system."""
    tag: str
    device_type: str = ""
    manufacturer: str = ""
    part_number: str = ""
    description: str = ""
    location: str = ""
    cabinet: str = ""
    rack: str = ""
    slot: str = ""
    channel: str = ""
    ip_address: str = ""
    contacts: List[DeviceContact] = field(default_factory=list)
    power_supply: str = ""
    communication_module: str = ""


@dataclass
class PowerStructure:
    """Represents power distribution structure."""
    voltage_level: str
    phase: str = ""  # L1, L2, L3, N, PE
    current_rating: str = ""
    protection_device: str = ""
    distribution_panel: str = ""
    circuit_breaker: str = ""
    connected_devices: List[str] = field(default_factory=list)


@dataclass
class NetworkDevice:
    """Represents a network device."""
    tag: str
    device_type: str = ""
    ip_address: str = ""
    subnet_mask: str = ""
    gateway: str = ""
    mac_address: str = ""
    vlan: str = ""
    switch_port: str = ""
    cable_number: str = ""


@dataclass
class EplanDrawingSet:
    """Contains all parsed information from EPlan drawing set."""
    project_name: str = ""
    drawing_sections: Dict[List[dict]] = field(default_factory=dict)
    drawing_numbers: List[str] = field(default_factory=list)
    devices: Dict[str, IODevice] = field(default_factory=dict)
    power_structure: Dict[str, PowerStructure] = field(default_factory=dict)
    network_devices: Dict[str, NetworkDevice] = field(default_factory=dict)
    ethernet_topology: Dict[str, List[str]] = field(default_factory=dict)
    io_mapping: Dict[str, str] = field(default_factory=dict)
    cable_schedule: Dict[str, Dict] = field(default_factory=dict)
    panel_layout: Dict[str, List[str]] = field(default_factory=dict)


class EplanPDFParser(Loggable):
    """Parser for EPlan-generated PDF electrical schematics."""

    def __init__(self):
        super().__init__()
        self.drawing_set = EplanDrawingSet()
        self._device_patterns = self._compile_device_patterns()
        self._ip_patterns = self._compile_ip_patterns()
        self._power_patterns = self._compile_power_patterns()

    def _compile_device_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for device identification."""
        patterns = {
            # Common device tag patterns
            'device_tag': re.compile(r'([A-Z]{1,4}\d{1,4}[A-Z]?)', re.IGNORECASE),
            'plc_tag': re.compile(r'(CPU|PLC|PAC)[-_]?(\d+)', re.IGNORECASE),
            'hmi_tag': re.compile(r'(HMI|PV|VT)[-_]?(\d+)', re.IGNORECASE),
            'io_module': re.compile(r'(AI|AO|DI|DO|RTD|TC)[-_]?(\d+)', re.IGNORECASE),
            'motor_starter': re.compile(r'(MS|MCC)[-_]?(\d+)', re.IGNORECASE),
            'valve': re.compile(r'(XV|PV|TV|FV|LV)[-_]?(\d+)', re.IGNORECASE),
            'sensor': re.compile(r'(PT|TT|FT|LT|XT)[-_]?(\d+)', re.IGNORECASE),
            'switch': re.compile(r'(SW|LS|PS|TS|FS)[-_]?(\d+)', re.IGNORECASE),
            # Device specifications
            'allen_bradley': re.compile(r'(1756|1769|1734|1794|5069)[-\s](\w+)', re.IGNORECASE),
            'siemens': re.compile(r'(6ES7|6GK7|6AV7)[-\w]*', re.IGNORECASE),
            'schneider': re.compile(r'(TM\d+|LMC\d+|BMX\w+)', re.IGNORECASE),
        }
        return patterns

    def _compile_ip_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for IP address and network information."""
        patterns = {
            'ip_address': re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            'subnet_mask': re.compile(
                r'\b(?:(?:255|254|252|248|240|224|192|128|0)\.){3}'
                r'(?:255|254|252|248|240|224|192|128|0)\b'
            ),
            'mac_address': re.compile(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'),
            'ethernet_port': re.compile(r'(?:ETH|EN)[-_]?(\d+)', re.IGNORECASE),
            'vlan': re.compile(r'VLAN[-_\s]*:?\s*(\d+)', re.IGNORECASE),
        }
        return patterns

    def _compile_power_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for power distribution information."""
        patterns = {
            'voltage': re.compile(r'(\d+(?:\.\d+)?)\s*(?:V|VAC|VDC)', re.IGNORECASE),
            'current': re.compile(r'(\d+(?:\.\d+)?)\s*(?:A|AMP)', re.IGNORECASE),
            'power': re.compile(r'(\d+(?:\.\d+)?)\s*(?:W|KW|HP)', re.IGNORECASE),
            'phase': re.compile(r'\b(L[123]|N|PE|GND)\b', re.IGNORECASE),
            'circuit_breaker': re.compile(r'(CB|MCB|MCCB)[-_]?(\d+)', re.IGNORECASE),
            'fuse': re.compile(r'(F|FU)[-_]?(\d+)', re.IGNORECASE),
            'contactor': re.compile(r'(K|KM)[-_]?(\d+)', re.IGNORECASE),
        }
        return patterns

    def _parse_single_pdf(self, pdf_file: str) -> None:
        """Parse a single PDF file for electrical schematic information."""
        self.logger.info(f"Parsing PDF: {pdf_file}")

        # Extract text using multiple methods for better accuracy
        text_data = self._extract_text_multiple_methods(
            pdf_file,
            use_pdf_plumber=True  # Default method
        )

        self._extract_project_info(text_data)
        self._extract_devices(text_data)
        self._extract_network_info(text_data)
        self._extract_power_info(text_data)
        self._extract_io_mapping(text_data)
        self._extract_cable_schedule(text_data)

    def _extract_text_pdf_plumber(
        self,
        pdf_file: str,
    ) -> list[dict]:
        """Extraction method #1: pdfplumber (best for tables and structured data).
        """
        data = []
        try:
            with pdfplumber.open(pdf_file) as pdf:
                self.logger.info(f"Extracting text from {pdf_file} using pdfplumber...")
                for page_num, page in enumerate(pdf.pages):
                    self.logger.debug(f"Processing page {page_num + 1}...")
                    text = page.extract_text()
                    if text:
                        data.append({
                            'page': page_num + 1,
                            'text': text,
                            'tables': page.extract_tables()
                        })
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed: {e}")
        return data

    def _extract_text_pdf_mupdf(
        self,
        pdf_file: str,
    ) -> list[dict]:
        """Extraction method #2: PyMuPDF (fitz) - good for complex layouts."""
        data = []
        try:
            self.logger.info(f"Extracting text from {pdf_file} using PyMuPDF...")
            doc = fitz.open(pdf_file)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                if text:
                    data.append({
                        'page': page_num + 1,
                        'text': text,
                        'blocks': page.get_text("dict")
                    })
            doc.close()
        except Exception as e:
            self.logger.warning(f"PyMuPDF extraction failed: {e}")
        return data

    def _extract_text_pdf_pypdf2(
        self,
        pdf_file: str,
    ) -> list[dict]:
        """Extraction method #3: PyPDF2 (fallback for basic text extraction)."""
        data = []
        try:
            with open(pdf_file, 'rb') as file:
                self.logger.info(f"Extracting text from {pdf_file} using PyPDF2...")
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        data.append({
                            'page': page_num + 1,
                            'text': text
                        })
        except Exception as e:
            self.logger.warning(f"PyPDF2 extraction failed: {e}")
        return data

    def _extract_text_multiple_methods(
        self,
        pdf_file: str,
        use_pdf_plumber: bool = True,
        use_pdf_mupdf: bool = False,
        use_pdf_pypdf2: bool = False,
    ) -> Dict[str, List[str]]:
        """Extract text using multiple PDF parsing methods for better accuracy."""
        text_data = {}
        if use_pdf_plumber:
            text_data['pdfplumber'] = self._extract_text_pdf_plumber(pdf_file)
        if use_pdf_mupdf:
            text_data['pymupdf'] = self._extract_text_pdf_mupdf(pdf_file)
        if use_pdf_pypdf2:
            text_data['pypdf2'] = self._extract_text_pdf_pypdf2(pdf_file)

        return text_data

    def _extract_page_section_letter(
        self,
        page_data: dict,
    ) -> Optional[str]:
        """Extract section letter from page data."""
        data = self._extract_pattern_from_page(
            page_data=page_data,
            pattern=SECTION_LETTER_RE
        )
        if data is not None and len(data) > 0 and data[0] is not None:
            return data[0][0]

    def _extract_page_section_number(
        self,
        page_data: dict,
    ) -> Optional[str]:
        """Extract section number from page data."""
        data = self._extract_pattern_from_page(
            page_data=page_data,
            pattern=SHEET_NUMBER_RE
        )
        if data is not None and len(data) > 0 and data[0] is not None:
            return data[0][0]

    def _extract_page_sections(
        self,
        text_data: List[dict],
    ) -> None:
        """Extract each page section out of the supplied text data.
        """
        if not text_data:
            raise ValueError("No text data provided for page extraction.")

        self.logger.debug("Extracting page sections from text data...")

        # Iterate through each page's text data
        for page_data in text_data:
            if not isinstance(page_data, dict):
                continue

            section_letter = self._extract_page_section_letter(page_data)
            section_number = self._extract_page_section_number(page_data)

            if not section_letter or not section_number:
                raise ValueError(
                    f"Missing section letter or number in page data: {page_data}"
                )

            if section_letter not in self.drawing_set.drawing_sections:
                self.drawing_set.drawing_sections[section_letter] = []

            if section_number in self.drawing_set.drawing_sections[section_letter]:
                self.logger.warning(
                    f"Duplicate section number '{section_number}' in section '{section_letter}'. "
                    "Skipping this page."
                )
                continue

            self.drawing_set.drawing_sections[section_letter].append({
                section_number: page_data
            })

    def _extract_pattern_from_page(
        self,
        page_data: dict,
        pattern: str
    ) -> Optional[List[Tuple[str, ...]]]:
        """Extract a pattern from the page data."""
        if not isinstance(page_data, dict):
            raise ValueError("Invalid page data format provided.")

        tables = page_data.get('tables', [])
        if not tables:
            self.logger.warning("No tables found in page data for pattern extraction.")
            return None

        text = self._flatten_table_to_text(tables)
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches

        importlib.reload(fuzzy)
        # Attempt fuzzy matching if no exact matches found
        fuzzy_match = fuzzy.fuzzy_pattern_match(text, pattern)
        if fuzzy_match is not None:
            return [fuzzy_match]

        # Attempt fuzzy regex search
        fuzzy_matches = fuzzy.fuzzy_regex_search(text, pattern)
        if fuzzy_matches is not None and len(fuzzy_matches) > 0:
            return fuzzy_matches

        self.logger.warning(f"No matches found for pattern: {pattern}")
        return None

    def _extract_project_info_pdf_plumber(
        self,
        text_data: List[dict]
    ) -> None:
        """Extract project information from the PDF using pdfplumber."""
        if not text_data:
            raise ValueError("No text data provided for project extraction.")

        self.logger.debug("Extracting project information from pdfplumber text data...")
        self._extract_page_sections(text_data)

        # Iterate through each page's text data
        for page_data in text_data:
            if not isinstance(page_data, dict):
                continue

            page_num = page_data.get('page', 'Unknown')
            self.logger.debug(f"Processing page {page_num} for project info...")

            # First, try to extract from the full page text
            page_text = page_data.get('text', '')
            if page_text is None:
                self.logger.warning(f"No text found on page {page_num}, skipping...")
                continue

            # search package for package name
            package_info = self._search_page_tables(
                page_data.get('tables', []),
                PACKAGE_NAME_RE
            )

            if not package_info:
                raise ValueError(f"No package information found on page {page_num}")
            self.drawing_set.project_name = ''.join([' '.join(x) for x in package_info]).replace('\n', '')
            break

        # Log summary
        self.logger.info("Project extraction summary:")
        self.logger.info(f"  - Total sections found: {len(self.drawing_set.drawing_sections)}")
        for section in self.drawing_set.drawing_sections:
            self.logger.info(f"    - Section '{section}' with {len(self.drawing_set.drawing_sections[section])} pages")
        self.logger.info(f"  - Final project name: '{self.drawing_set.project_name}'")

    def _extract_project_info(
        self,
        text_data: Dict
    ) -> None:
        """Extract project information from the PDF.
        """
        plumber = text_data.get('pdfplumber', [])
        mupdf = text_data.get('pymupdf', [])
        pypdf2 = text_data.get('pypdf2', [])

        if plumber:
            return self._extract_project_info_pdf_plumber(plumber)
        elif mupdf:
            raise NotImplementedError("MuPDF extraction not implemented yet.")
        elif pypdf2:
            raise NotImplementedError("PyPDF2 extraction not implemented yet.")
        else:
            raise ValueError("No valid text extraction methods provided.")

    def _extract_devices(self, text_data: Dict) -> None:
        """Extract device information from the PDF text."""

        all_text = self._combine_text_data(text_data)

        # Find all potential device tags
        device_matches = self._device_patterns['device_tag'].findall(all_text)

        for device_tag in set(device_matches):
            if len(device_tag) < 2:  # Skip single characters
                continue

            device = IODevice(tag=device_tag)

            # Try to find device information near the tag
            device_context = self._extract_device_context(all_text, device_tag)

            # Determine device type
            device.device_type = self._determine_device_type(device_tag, device_context)

            # Extract manufacturer and part number
            device.manufacturer, device.part_number = self._extract_device_specs(device_context)

            # Extract location information
            device.cabinet, device.rack, device.slot = self._extract_location_info(device_context)

            # Extract IP address if network device
            device.ip_address = self._extract_device_ip(device_context)

            self.drawing_set.devices[device_tag] = device

    def _extract_device_context(self, text: str, device_tag: str) -> str:
        """Extract text context around a device tag."""
        lines = text.split('\n')
        context_lines = []

        for i, line in enumerate(lines):
            if device_tag in line:
                # Get surrounding lines for context
                start = max(0, i - 3)
                end = min(len(lines), i + 4)
                context_lines.extend(lines[start:end])

        return '\n'.join(context_lines)

    def _determine_device_type(self, tag: str, context: str) -> str:
        """Determine device type based on tag and context."""
        # Check tag prefix patterns
        if re.match(r'^(CPU|PLC|PAC)', tag, re.IGNORECASE):
            return "PLC"
        elif re.match(r'^(HMI|PV|VT)', tag, re.IGNORECASE):
            return "HMI"
        elif re.match(r'^(AI|AO|DI|DO)', tag, re.IGNORECASE):
            return "I/O Module"
        elif re.match(r'^(MS|MCC)', tag, re.IGNORECASE):
            return "Motor Starter"
        elif re.match(r'^(XV|PV|TV)', tag, re.IGNORECASE):
            return "Valve"
        elif re.match(r'^(PT|TT|FT)', tag, re.IGNORECASE):
            return "Transmitter"
        elif re.match(r'^(SW|LS|PS)', tag, re.IGNORECASE):
            return "Switch"

        # Check context for device type keywords
        context_lower = context.lower()
        if any(word in context_lower for word in ['cpu', 'processor', 'controller']):
            return "PLC"
        elif any(word in context_lower for word in ['hmi', 'display', 'operator']):
            return "HMI"
        elif any(word in context_lower for word in ['input', 'output', 'module']):
            return "I/O Module"
        elif any(word in context_lower for word in ['motor', 'starter']):
            return "Motor Starter"
        elif any(word in context_lower for word in ['valve', 'actuator']):
            return "Valve"
        elif any(word in context_lower for word in ['switch', 'ethernet']):
            return "Network Switch"

        return "Unknown"

    def _extract_device_specs(self, context: str) -> Tuple[str, str]:
        """Extract manufacturer and part number from context."""
        manufacturer = ""
        part_number = ""

        # Check for Allen-Bradley
        ab_match = self._device_patterns['allen_bradley'].search(context)
        if ab_match:
            manufacturer = "Allen-Bradley"
            part_number = f"{ab_match.group(1)}-{ab_match.group(2)}"

        # Check for Siemens
        siemens_match = self._device_patterns['siemens'].search(context)
        if siemens_match:
            manufacturer = "Siemens"
            part_number = siemens_match.group(0)  # Get the full match

        # Check for Schneider
        schneider_match = self._device_patterns['schneider'].search(context)
        if schneider_match:
            manufacturer = "Schneider Electric"
            part_number = schneider_match.group(0)

        return manufacturer, part_number

    def _extract_location_info(self, context: str) -> Tuple[str, str, str]:
        """Extract cabinet, rack, and slot information."""
        cabinet = ""
        rack = ""
        slot = ""

        # Look for cabinet/panel information
        cabinet_pattern = re.compile(r'(?:CABINET|PANEL|ENCLOSURE)\s*[:]\s*([A-Z0-9-]+)', re.IGNORECASE)
        cabinet_match = cabinet_pattern.search(context)
        if cabinet_match:
            cabinet = cabinet_match.group(1)

        # Look for rack information
        rack_pattern = re.compile(r'RACK\s*[:]\s*(\d+)', re.IGNORECASE)
        rack_match = rack_pattern.search(context)
        if rack_match:
            rack = rack_match.group(1)

        # Look for slot information
        slot_pattern = re.compile(r'SLOT\s*[:]\s*(\d+)', re.IGNORECASE)
        slot_match = slot_pattern.search(context)
        if slot_match:
            slot = slot_match.group(1)

        return cabinet, rack, slot

    def _extract_device_ip(self, context: str) -> str:
        """Extract IP address for network devices."""
        ip_match = self._ip_patterns['ip_address'].search(context)
        return ip_match.group(0) if ip_match else ""

    def _extract_network_info(self, text_data: Dict) -> None:
        """Extract network topology and device information."""
        all_text = self._combine_text_data(text_data)

        # Find all IP addresses
        ip_addresses = self._ip_patterns['ip_address'].findall(all_text)

        for ip in set(ip_addresses):
            # Find context around IP address
            ip_context = self._extract_ip_context(all_text, ip)

            # Try to find associated device tag
            device_tag = self._find_device_for_ip(ip_context)

            if device_tag:
                network_device = NetworkDevice(
                    tag=device_tag,
                    ip_address=ip
                )

                # Extract additional network information
                network_device.subnet_mask = self._extract_subnet_mask(ip_context)
                network_device.mac_address = self._extract_mac_address(ip_context)
                network_device.vlan = self._extract_vlan(ip_context)

                self.drawing_set.network_devices[device_tag] = network_device

    def _extract_ip_context(self, text: str, ip: str) -> str:
        """Extract context around an IP address."""
        lines = text.split('\n')
        context_lines = []

        for i, line in enumerate(lines):
            if ip in line:
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context_lines.extend(lines[start:end])

        return '\n'.join(context_lines)

    def _extract_cable_schedule(self, text_data: Dict) -> None:
        """Extract cable schedule information."""
        all_text = self._combine_text_data(text_data)

        # Look for cable patterns
        cable_pattern = re.compile(r'CABLE\s*([A-Z0-9-]+)', re.IGNORECASE)
        cable_matches = cable_pattern.findall(all_text)

        for cable_num in set(cable_matches):
            cable_context = self._extract_cable_context(all_text, cable_num)

            cable_info = {
                'number': cable_num,
                'from': self._extract_cable_from(cable_context),
                'to': self._extract_cable_to(cable_context),
                'type': self._extract_cable_type(cable_context),
                'length': self._extract_cable_length(cable_context)
            }

            self.drawing_set.cable_schedule[cable_num] = cable_info

    def _extract_cable_context(self, text: str, cable_num: str) -> str:
        """Extract context around cable number."""
        pattern = re.compile(rf'CABLE\s*{re.escape(cable_num)}', re.IGNORECASE)
        lines = text.split('\n')
        context_lines = []

        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                context_lines.extend(lines[start:end])

        return '\n'.join(context_lines)

    def _extract_cable_from(self, context: str) -> str:
        """Extract cable 'from' location."""
        from_pattern = re.compile(r'FROM\s*[:]\s*([A-Z0-9-]+)', re.IGNORECASE)
        match = from_pattern.search(context)
        return match.group(1) if match else ""

    def _extract_cable_to(self, context: str) -> str:
        """Extract cable 'to' location."""
        to_pattern = re.compile(r'TO\s*[:]\s*([A-Z0-9-]+)', re.IGNORECASE)
        match = to_pattern.search(context)
        return match.group(1) if match else ""

    def _extract_cable_type(self, context: str) -> str:
        """Extract cable type."""
        type_pattern = re.compile(r'TYPE\s*[:]\s*([A-Z0-9/\-\s]+)', re.IGNORECASE)
        match = type_pattern.search(context)
        return match.group(1).strip() if match else ""

    def _extract_cable_length(self, context: str) -> str:
        """Extract cable length."""
        length_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:FT|FEET|M|METER)', re.IGNORECASE)
        match = length_pattern.search(context)
        return match.group(0) if match else ""

    def _extract_subnet_mask(self, context: str) -> str:
        """Extract subnet mask from context."""
        mask_match = self._ip_patterns['subnet_mask'].search(context)
        return mask_match.group(0) if mask_match else ""

    def _extract_mac_address(self, context: str) -> str:
        """Extract MAC address from context."""
        mac_match = self._ip_patterns['mac_address'].search(context)
        return mac_match.group(0) if mac_match else ""

    def _extract_vlan(self, context: str) -> str:
        """Extract VLAN information from context."""
        vlan_match = self._ip_patterns['vlan'].search(context)
        return vlan_match.group(1) if vlan_match else ""

    def _extract_power_info(self, text_data: Dict) -> None:
        """Extract power distribution information."""
        all_text = self._combine_text_data(text_data)

        # Find voltage levels
        voltage_matches = self._power_patterns['voltage'].findall(all_text)

        for voltage in set(voltage_matches):
            power_struct = PowerStructure(voltage_level=f"{voltage}V")

            # Find context around voltage
            voltage_context = self._extract_voltage_context(all_text, voltage)

            # Extract phase information
            phase_matches = self._power_patterns['phase'].findall(voltage_context)
            if phase_matches:
                power_struct.phase = ', '.join(set(phase_matches))

            # Extract protection devices
            cb_match = self._power_patterns['circuit_breaker'].search(voltage_context)
            if cb_match:
                power_struct.protection_device = f"{cb_match.group(1)}-{cb_match.group(2)}"

            self.drawing_set.power_structure[f"{voltage}V"] = power_struct

    def _extract_voltage_context(self, text: str, voltage: str) -> str:
        """Extract context around voltage specification."""
        pattern = re.compile(rf'\b{re.escape(voltage)}\s*(?:V|VAC|VDC)', re.IGNORECASE)
        lines = text.split('\n')
        context_lines = []

        for i, line in enumerate(lines):
            if pattern.search(line):
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context_lines.extend(lines[start:end])

        return '\n'.join(context_lines)

    def _extract_io_mapping(self, text_data: Dict) -> None:
        """Extract I/O mapping information."""
        # Look for I/O tables in extracted tables
        for method_data in text_data.values():
            for page_data in method_data:
                if isinstance(page_data, dict) and 'tables' in page_data:
                    for table in page_data.get('tables', []):
                        if table and self._is_io_table(table):
                            self._parse_io_table(table)

    def _find_device_for_ip(self, context: str) -> str:
        """Find device tag associated with an IP address."""
        device_match = self._device_patterns['device_tag'].search(context)
        return device_match.group(0) if device_match else ""

    def _flatten_table_to_text(
        self,
        table: List[List[str]],
    ) -> str:
        """Flatten a table into a single text string."""
        if not table:
            return ""

        flattened = []
        for row in table:
            if not row:
                continue
            for cell in row:
                if not cell:
                    continue
                for sub_cell in cell:
                    if not sub_cell:
                        continue
                    sub_cell = sub_cell.strip()
                    if sub_cell:
                        flattened.append(sub_cell)

        return ' '.join(flattened)

    def _is_io_table(self, table: List[List[str]]) -> bool:
        """Determine if a table contains I/O mapping information."""
        if not table or len(table) < 2:
            return False

        header_row = [cell.lower() if cell else "" for cell in table[0]]
        io_keywords = ['tag', 'address', 'description', 'type', 'module', 'channel']

        return any(keyword in ' '.join(header_row) for keyword in io_keywords)

    def _parse_io_table(self, table: List[List[str]]) -> None:
        """Parse I/O mapping table."""
        if not table:
            return

        headers = [cell.lower().strip() if cell else "" for cell in table[0]]

        for row in table[1:]:
            if not row or not any(row):
                continue

            # Map row data to headers
            row_data = {}
            for i, cell in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_data[headers[i]] = cell.strip() if cell else ""

            # Extract tag and address mapping
            tag = row_data.get('tag', '') or row_data.get('device', '')
            address = row_data.get('address', '') or row_data.get('location', '')

            if tag and address:
                self.drawing_set.io_mapping[tag] = address

    def _search_page_tables(
        self,
        page_tables: List[List[str]],
        search_pattern: re.Pattern
    ) -> List[str]:
        """Search for a pattern in the page tables and return matches."""
        if not page_tables:
            self.logger.warning("Empty page tables provided for search.")
            return []
        if not search_pattern:
            self.logger.warning("No search pattern provided.")
            return []
        matches = []
        for table in page_tables:
            for row in table:
                for cell in row:
                    if not cell:
                        continue
                    val = re.findall(search_pattern, cell, re.DOTALL | re.IGNORECASE)
                    if not val:
                        continue
                    matches.extend(val)
        return matches

    def _search_page_text(
        self,
        page_text: str,
        search_pattern: re.Pattern
    ) -> List[str]:
        """Search for a pattern in the page text and return matches."""
        if not page_text:
            self.logger.warning("Empty page text provided for search.")
            return []
        if not search_pattern:
            self.logger.warning("No search pattern provided.")
            return []
        matches = re.findall(search_pattern, page_text, re.DOTALL | re.IGNORECASE)
        return matches

    def _combine_text_data(self, text_data: Dict) -> str:
        """Combine text from all extraction methods."""
        combined_text = []

        for method_name, method_data in text_data.items():
            for page_data in method_data:
                if isinstance(page_data, dict):
                    combined_text.append(page_data.get('text', ''))
                else:
                    combined_text.append(str(page_data))

        return '\n'.join(combined_text)

    def _post_process_data(self) -> None:
        """Post-process extracted data for consistency and relationships."""
        # Link network devices to main devices
        for net_device in self.drawing_set.network_devices.values():
            if net_device.tag in self.drawing_set.devices:
                self.drawing_set.devices[net_device.tag].ip_address = net_device.ip_address

        # Remove duplicate drawing numbers
        self.drawing_set.drawing_numbers = list(set(self.drawing_set.drawing_numbers))

    def export_to_dict(self) -> Dict:
        """Export parsed data to dictionary format."""
        return {
            'project_name': self.drawing_set.project_name,
            'drawing_numbers': self.drawing_set.drawing_numbers,
            'devices': {tag: device.__dict__ for tag, device in self.drawing_set.devices.items()},
            'power_structure': {key: ps.__dict__ for key, ps in self.drawing_set.power_structure.items()},
            'network_devices': {tag: net.__dict__ for tag, net in self.drawing_set.network_devices.items()},
            'ethernet_topology': self.drawing_set.ethernet_topology,
            'io_mapping': self.drawing_set.io_mapping,
            'cable_schedule': self.drawing_set.cable_schedule,
            'panel_layout': self.drawing_set.panel_layout
        }

    def export_to_file(self, output_file: str, format_type: str = 'json') -> None:
        """Export parsed data to file.

        Args:
            output_file: Output file path
            format_type: Output format ('json', 'yaml', 'csv')
        """
        data = self.export_to_dict()

        if format_type.lower() == 'json':
            import json
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
        elif format_type.lower() == 'yaml':
            try:
                import yaml
                with open(output_file, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML required for YAML export: pip install PyYAML")
        elif format_type.lower() == 'csv':
            # Export devices to CSV
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Tag', 'Type', 'Manufacturer', 'Part Number', 'IP Address', 'Location'])
                for device in data['devices'].values():
                    writer.writerow([
                        device.get('tag', ''),
                        device.get('device_type', ''),
                        device.get('manufacturer', ''),
                        device.get('part_number', ''),
                        device.get('ip_address', ''),
                        f"{device.get('cabinet', '')}-{device.get('rack', '')}-{device.get('slot', '')}"
                    ])

    def parse_pdf_set(self, pdf_files: Union[str, List[str]]) -> EplanDrawingSet:
        """Parse a set of EPlan PDF files.

        Args:
            pdf_files: Single PDF file path or list of PDF file paths

        Returns:
            EplanDrawingSet: Parsed drawing set information
        """
        if isinstance(pdf_files, str):
            pdf_files = [pdf_files]

        for pdf_file in pdf_files:
            if not os.path.exists(pdf_file):
                self.logger.warning(f"PDF file not found: {pdf_file}")
                continue
            self._parse_single_pdf(pdf_file)

        self._post_process_data()
        return self.drawing_set


def parse_eplan_pdfs(pdf_files: Union[str, List[str]],
                     output_file: Optional[str] = None) -> EplanDrawingSet:
    """Convenience function to parse EPlan PDF files.

    Args:
        pdf_files: Single PDF file path or list of PDF file paths
        output_file: Optional output file to save parsed data

    Returns:
        EplanDrawingSet: Parsed drawing set information

    Example:
        >>> # Parse single PDF
        >>> drawing_set = parse_eplan_pdfs('electrical_schematic.pdf')
        >>> 
        >>> # Parse multiple PDFs
        >>> pdfs = ['sheet1.pdf', 'sheet2.pdf', 'sheet3.pdf']
        >>> drawing_set = parse_eplan_pdfs(pdfs, 'parsed_data.json')
        >>> 
        >>> # Access parsed data
        >>> print(f"Found {len(drawing_set.devices)} devices")
        >>> for tag, device in drawing_set.devices.items():
        >>>     print(f"{tag}: {device.device_type} - {device.ip_address}")
    """
    parser = EplanPDFParser()
    drawing_set = parser.parse_pdf_set(pdf_files)

    if output_file:
        file_ext = Path(output_file).suffix.lower()
        if file_ext == '.json':
            parser.export_to_file(output_file, 'json')
        elif file_ext in ['.yaml', '.yml']:
            parser.export_to_file(output_file, 'yaml')
        elif file_ext == '.csv':
            parser.export_to_file(output_file, 'csv')
        else:
            parser.export_to_file(output_file, 'json')

    return drawing_set
