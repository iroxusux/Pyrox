"""testing module for services
    """
from pyrox.services.eplan import (
    EplanPDFParser,
    EplanDrawingSet,
    IODevice,
    DeviceContact,
    PowerStructure,
    NetworkDevice,
    parse_eplan_pdfs
)
import json
from unittest.mock import Mock, patch
import tempfile
import os
import sys
from .plc_services import (
    cdata,
    l5x_dict_from_file,
    dict_to_xml_file,
    get_rung_text,
    get_xml_string_from_file,
    preprocessor,
    find_rslogix_installations
)


import unittest
import lxml
import lxml.etree as ET
import pandas as pd

from pyrox.services.xml import parse_xml


DUPS_TEST_FILE = r'docs\controls\_test_duplicate_coils.L5X'
GM_TEST_FILE = r'docs\controls\_test_gm.L5X'
ROOT_TEST_FILE = r'docs\controls\root.L5X'


class TestCData(unittest.TestCase):
    def test_cdata(self):
        result = cdata("test")
        self.assertEqual(result, "<![CDATA[test]]>")


class TestL5XDictFromFile(unittest.TestCase):
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            l5x_dict_from_file("non_existent_file.L5X")

    def test_invalid_file_extension(self):
        with self.assertRaises(ValueError):
            l5x_dict_from_file("invalid_file.txt")

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    def test_parse_error(self, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parse.side_effect = lxml.etree.ParseError
        result = l5x_dict_from_file("invalid_file.L5X")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    def test_unexpected_error(self, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parse.side_effect = Exception("Unexpected error")
        result = l5x_dict_from_file("unexpected_error.L5X")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    @patch("lxml.etree.XMLParser")
    @patch("xmltodict.parse")
    def test_successful_parse(self, mock_xmltodict_parse, mock_parser, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parser.return_value = lxml.etree.XMLParser(strip_cdata=False)
        mock_parse.return_value.getroot.return_value = lxml.etree.Element("root")
        mock_parse.return_value.getroot.return_value.text = "<root></root>"
        mock_xmltodict_parse.return_value = {"root": {}}
        result = l5x_dict_from_file("valid_file.L5X")
        self.assertEqual(result, {"root": {}})

    def test_all_base_files(self):
        from ..models.plc import BASE_FILES
        for file in BASE_FILES:
            with self.subTest(file=file):
                result = l5x_dict_from_file(file)
                self.assertIsInstance(result, dict)
                self.assertTrue(len(result) > 0, f"File {file} should not be empty.")


class TestDictToControllerFile(unittest.TestCase):
    @patch("pyrox.services.plc_services.save_file")
    @patch("xmltodict.unparse")
    def test_dict_to_controller_file(self, mock_unparse, mock_save_file):
        controller = {"root": {}}
        file_location = "controller.L5X"
        dict_to_xml_file(controller, file_location)
        mock_unparse.assert_called_once_with(controller, preprocessor=preprocessor, pretty=True)
        mock_save_file.assert_called_once()


class TestGetRungText(unittest.TestCase):
    def test_get_rung_text_with_text(self):
        rung = ET.Element("Rung")
        text_element = ET.SubElement(rung, "Text")
        text_element.text = "Test text"
        result = get_rung_text(rung)
        self.assertEqual(result, "Test text")

    def test_get_rung_text_with_comment(self):
        rung = ET.Element("Rung")
        comment_element = ET.SubElement(rung, "Comment")
        comment_element.text = "Test comment"
        result = get_rung_text(rung)
        self.assertEqual(result, "Test comment")

    def test_get_rung_text_no_description(self):
        rung = ET.Element("Rung")
        result = get_rung_text(rung)
        self.assertEqual(result, "No description available")


class TestGetXmlStringFromFile(unittest.TestCase):
    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    @patch("lxml.etree.XMLParser")
    def test_get_xml_string_from_file(self, mock_parser, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parser.return_value = lxml.etree.XMLParser(strip_cdata=False)
        mock_parse.return_value.getroot.return_value = lxml.etree.Element("root")
        mock_parse.return_value.getroot.return_value.text = "<root></root>"
        result = get_xml_string_from_file("valid_file.L5X")
        self.assertEqual(result, "<root>&lt;root&gt;&lt;/root&gt;</root>")


class TestPreprocessor(unittest.TestCase):
    def test_preprocessor_with_cdata(self):
        key = "Comment"
        value = "Test comment"
        result_key, result_value = preprocessor(key, value)
        self.assertEqual(result_key, key)
        self.assertEqual(result_value, "<![CDATA[Test comment]]>")


class TestFindAndInstantiateClass(unittest.TestCase):
    def test_find_and_instantiate_class(self):
        from .class_services import find_and_instantiate_class
        from pyrox.models import ApplicationTask

        my_objects = find_and_instantiate_class(directory_path=r"pyrox\\tasks\\builtin",
                                                class_name="ApplicationTask",
                                                as_subclass=True,
                                                ignoring_classes=["ApplicationTask", "AppTask"],
                                                parent_class=ApplicationTask,
                                                application=None)
        self.assertIsNotNone(my_objects)
        self.assertTrue(len(my_objects) >= 3)
        self.assertTrue(hasattr(my_objects[0], "application"))


class TestParseXML(unittest.TestCase):
    @patch('pyrox.services.xml.pd.read_excel')
    def test_parse_xml_returns_keys(self, mock_read_excel):
        # Mocked data to simulate pd.read_excel output
        mock_data = {
            'Sheet1': pd.DataFrame({'A': [1, 2]}),
            'Sheet2': pd.DataFrame({'B': [3, 4]})
        }
        mock_read_excel.return_value = mock_data

        file_location = 'dummy/path/to/file.xlsx'
        result = parse_xml(file_location)

        # Should return dict_keys of the mock_data
        self.assertEqual(set(result), set(mock_data.keys()))
        mock_read_excel.assert_called_once_with(file_location, sheet_name=None)


class TestFindRSLogixInstallations(unittest.TestCase):
    def test_returns_list(self):
        # Should always return a list, even if empty
        result = find_rslogix_installations()
        self.assertIsInstance(result, list)

    def test_dict_structure(self):
        # If any installations found, they should have expected keys
        result = find_rslogix_installations()
        for item in result:
            self.assertIsInstance(item, dict)
            self.assertIn("name", item)
            self.assertIn("version", item)
            self.assertIn("install_path", item)

    def test_no_crash_on_missing_registry(self):
        # Should not raise even if registry keys are missing
        try:
            find_rslogix_installations()
        except Exception as e:
            self.fail(f"find_rslogix_installations raised an exception: {e}")

    def test_mock_registry(self):
        # Only run this test on Windows
        if sys.platform != "win32":
            self.skipTest("Registry tests only run on Windows")
        # You could use unittest.mock to patch winreg.OpenKey and EnumKey for more thorough testing


class TestDeviceContact(unittest.TestCase):
    """Test DeviceContact dataclass."""

    def test_device_contact_creation(self):
        """Test creating a DeviceContact."""
        contact = DeviceContact(
            terminal="TB1-1",
            signal_name="START_CMD",
            wire_number="W001",
            device_reference="MS001",
            contact_type="NO"
        )

        self.assertEqual(contact.terminal, "TB1-1")
        self.assertEqual(contact.signal_name, "START_CMD")
        self.assertEqual(contact.wire_number, "W001")
        self.assertEqual(contact.device_reference, "MS001")
        self.assertEqual(contact.contact_type, "NO")

    def test_device_contact_defaults(self):
        """Test DeviceContact with default values."""
        contact = DeviceContact(terminal="TB1-2")

        self.assertEqual(contact.terminal, "TB1-2")
        self.assertEqual(contact.signal_name, "")
        self.assertEqual(contact.wire_number, "")
        self.assertEqual(contact.device_reference, "")
        self.assertEqual(contact.contact_type, "")


class TestIODevice(unittest.TestCase):
    """Test IODevice dataclass."""

    def test_io_device_creation(self):
        """Test creating an IODevice."""
        device = IODevice(
            tag="AI001",
            device_type="Analog Input",
            manufacturer="Allen-Bradley",
            part_number="1756-IF8",
            ip_address="192.168.1.100"
        )

        self.assertEqual(device.tag, "AI001")
        self.assertEqual(device.device_type, "Analog Input")
        self.assertEqual(device.manufacturer, "Allen-Bradley")
        self.assertEqual(device.part_number, "1756-IF8")
        self.assertEqual(device.ip_address, "192.168.1.100")
        self.assertEqual(device.contacts, [])

    def test_io_device_with_contacts(self):
        """Test IODevice with contacts."""
        contact1 = DeviceContact(terminal="1", signal_name="CH1")
        contact2 = DeviceContact(terminal="2", signal_name="CH2")

        device = IODevice(
            tag="DI001",
            contacts=[contact1, contact2]
        )

        self.assertEqual(len(device.contacts), 2)
        self.assertEqual(device.contacts[0].terminal, "1")
        self.assertEqual(device.contacts[1].terminal, "2")


class TestPowerStructure(unittest.TestCase):
    """Test PowerStructure dataclass."""

    def test_power_structure_creation(self):
        """Test creating a PowerStructure."""
        power = PowerStructure(
            voltage_level="480V",
            phase="L1, L2, L3",
            current_rating="30A",
            protection_device="CB001"
        )

        self.assertEqual(power.voltage_level, "480V")
        self.assertEqual(power.phase, "L1, L2, L3")
        self.assertEqual(power.current_rating, "30A")
        self.assertEqual(power.protection_device, "CB001")
        self.assertEqual(power.connected_devices, [])


class TestNetworkDevice(unittest.TestCase):
    """Test NetworkDevice dataclass."""

    def test_network_device_creation(self):
        """Test creating a NetworkDevice."""
        net_device = NetworkDevice(
            tag="SW001",
            device_type="Ethernet Switch",
            ip_address="192.168.1.10",
            subnet_mask="255.255.255.0"
        )

        self.assertEqual(net_device.tag, "SW001")
        self.assertEqual(net_device.device_type, "Ethernet Switch")
        self.assertEqual(net_device.ip_address, "192.168.1.10")
        self.assertEqual(net_device.subnet_mask, "255.255.255.0")


class TestEplanDrawingSet(unittest.TestCase):
    """Test EplanDrawingSet dataclass."""

    def test_drawing_set_creation(self):
        """Test creating an EplanDrawingSet."""
        drawing_set = EplanDrawingSet(project_name="GM Test Project")

        self.assertEqual(drawing_set.project_name, "GM Test Project")
        self.assertEqual(drawing_set.drawing_numbers, [])
        self.assertEqual(drawing_set.devices, {})
        self.assertEqual(drawing_set.power_structure, {})
        self.assertEqual(drawing_set.network_devices, {})


class TestEplanPDFParser(unittest.TestCase):
    """Test EplanPDFParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = EplanPDFParser()

    def test_parser_initialization(self):
        """Test parser initialization."""
        self.assertIsInstance(self.parser.drawing_set, EplanDrawingSet)
        self.assertIn('device_tag', self.parser._device_patterns)
        self.assertIn('ip_address', self.parser._ip_patterns)
        self.assertIn('voltage', self.parser._power_patterns)

    def test_compile_device_patterns(self):
        """Test device pattern compilation."""
        patterns = self.parser._compile_device_patterns()

        # Test device tag pattern
        device_pattern = patterns['device_tag']
        self.assertTrue(device_pattern.search("AI001"))
        self.assertTrue(device_pattern.search("MS123"))
        self.assertTrue(device_pattern.search("PLC1"))

        # Test Allen-Bradley pattern
        ab_pattern = patterns['allen_bradley']
        self.assertTrue(ab_pattern.search("1756-IF8"))
        self.assertTrue(ab_pattern.search("1769 OF2"))

    def test_compile_ip_patterns(self):
        """Test IP pattern compilation."""
        patterns = self.parser._compile_ip_patterns()

        # Test IP address pattern
        ip_pattern = patterns['ip_address']
        self.assertTrue(ip_pattern.search("192.168.1.100"))
        self.assertTrue(ip_pattern.search("10.0.0.1"))
        self.assertFalse(ip_pattern.search("999.999.999.999"))

        # Test subnet mask pattern
        subnet_pattern = patterns['subnet_mask']
        self.assertTrue(subnet_pattern.search("255.255.255.0"))
        self.assertTrue(subnet_pattern.search("255.255.252.0"))

    def test_compile_power_patterns(self):
        """Test power pattern compilation."""
        patterns = self.parser._compile_power_patterns()

        # Test voltage pattern
        voltage_pattern = patterns['voltage']
        self.assertTrue(voltage_pattern.search("480V"))
        self.assertTrue(voltage_pattern.search("24 VDC"))
        self.assertTrue(voltage_pattern.search("120VAC"))

        # Test phase pattern
        phase_pattern = patterns['phase']
        self.assertTrue(phase_pattern.search("L1"))
        self.assertTrue(phase_pattern.search("PE"))
        self.assertTrue(phase_pattern.search("GND"))

    def test_determine_device_type(self):
        """Test device type determination."""
        # Test by tag prefix
        self.assertEqual(self.parser._determine_device_type("CPU001", ""), "PLC")
        self.assertEqual(self.parser._determine_device_type("HMI001", ""), "HMI")
        self.assertEqual(self.parser._determine_device_type("AI001", ""), "I/O Module")
        self.assertEqual(self.parser._determine_device_type("MS001", ""), "Motor Starter")

        # Test by context
        context = "This is a controller module CPU processor"
        self.assertEqual(self.parser._determine_device_type("DEV001", context), "PLC")

        context = "HMI operator display panel"
        self.assertEqual(self.parser._determine_device_type("DEV002", context), "HMI")

    def test_extract_device_specs(self):
        """Test device specification extraction."""
        # Test Allen-Bradley
        context = "Device: 1756-IF8 Analog Input Module"
        manufacturer, part_number = self.parser._extract_device_specs(context)
        self.assertEqual(manufacturer, "Allen-Bradley")
        self.assertEqual(part_number, "1756-IF8")

        # Test Siemens
        context = "Module 6ES7-134-4GB01-0AB0"
        manufacturer, part_number = self.parser._extract_device_specs(context)
        self.assertEqual(manufacturer, "Siemens")
        self.assertEqual(part_number, "6ES7-134-4GB01-0AB0")

        # Test no match
        context = "Unknown device specification"
        manufacturer, part_number = self.parser._extract_device_specs(context)
        self.assertEqual(manufacturer, "")
        self.assertEqual(part_number, "")

    def test_extract_location_info(self):
        """Test location information extraction."""
        context = "CABINET: MCC001 RACK: 1 SLOT: 5"
        cabinet, rack, slot = self.parser._extract_location_info(context)

        self.assertEqual(cabinet, "MCC001")
        self.assertEqual(rack, "1")
        self.assertEqual(slot, "5")

    def test_extract_device_ip(self):
        """Test device IP extraction."""
        context = "Device IP Address: 192.168.1.100"
        ip = self.parser._extract_device_ip(context)
        self.assertEqual(ip, "192.168.1.100")

        context = "No IP address here"
        ip = self.parser._extract_device_ip(context)
        self.assertEqual(ip, "")

    def test_find_device_for_ip(self):
        """Test finding device tag for IP address."""
        context = "PLC001 IP: 192.168.1.100"
        device_tag = self.parser._find_device_for_ip(context)
        self.assertEqual(device_tag, "PLC001")

    def test_extract_subnet_mask(self):
        """Test subnet mask extraction."""
        context = "Subnet Mask: 255.255.255.0"
        mask = self.parser._extract_subnet_mask(context)
        self.assertEqual(mask, "255.255.255.0")

    def test_extract_mac_address(self):
        """Test MAC address extraction."""
        context = "MAC: 00:1A:2B:3C:4D:5E"
        mac = self.parser._extract_mac_address(context)
        self.assertEqual(mac, "00:1A:2B:3C:4D:5E")

    def test_extract_vlan(self):
        """Test VLAN extraction."""
        context = "VLAN: 100"
        vlan = self.parser._extract_vlan(context)
        self.assertEqual(vlan, "100")

    def test_is_io_table(self):
        """Test I/O table identification."""
        # Valid I/O table
        io_table = [
            ["Tag", "Address", "Description", "Type"],
            ["AI001", "1:I.Data[0]", "Temperature", "Analog Input"],
            ["DI001", "2:I.Data[0]", "Start Button", "Digital Input"]
        ]
        self.assertTrue(self.parser._is_io_table(io_table))

        # Invalid table
        invalid_table = [
            ["Name", "Value", "Notes"],
            ["Test", "123", "Sample"]
        ]
        self.assertFalse(self.parser._is_io_table(invalid_table))

        # Empty table
        self.assertFalse(self.parser._is_io_table([]))

    def test_extract_cable_from(self):
        """Test cable 'from' extraction."""
        context = "FROM: PLC001 TO: HMI001"
        from_location = self.parser._extract_cable_from(context)
        self.assertEqual(from_location, "PLC001")

    def test_extract_cable_to(self):
        """Test cable 'to' extraction."""
        context = "FROM: PLC001 TO: HMI001"
        to_location = self.parser._extract_cable_to(context)
        self.assertEqual(to_location, "HMI001")

    def test_extract_cable_type(self):
        """Test cable type extraction."""
        context = "TYPE: CAT6 Ethernet Cable"
        cable_type = self.parser._extract_cable_type(context)
        self.assertEqual(cable_type, "CAT6 Ethernet Cable")

    def test_extract_cable_length(self):
        """Test cable length extraction."""
        context = "Length: 50 FT"
        length = self.parser._extract_cable_length(context)
        self.assertEqual(length, "50 FT")

    def test_combine_text_data(self):
        """Test combining text data from multiple sources."""
        text_data = {
            'pdfplumber': [
                {'text': 'Page 1 content', 'page': 1},
                {'text': 'Page 2 content', 'page': 2}
            ],
            'pymupdf': [
                {'text': 'PyMuPDF Page 1', 'page': 1}
            ]
        }

        combined = self.parser._combine_text_data(text_data)
        self.assertIn('Page 1 content', combined)
        self.assertIn('Page 2 content', combined)
        self.assertIn('PyMuPDF Page 1', combined)

    def test_export_to_dict(self):
        """Test exporting to dictionary format."""
        # Add test data
        device = IODevice(tag="TEST001", device_type="Test Device")
        self.parser.drawing_set.devices["TEST001"] = device
        self.parser.drawing_set.project_name = "Test Project"

        result = self.parser.export_to_dict()

        self.assertEqual(result['project_name'], "Test Project")
        self.assertIn('TEST001', result['devices'])
        self.assertEqual(result['devices']['TEST001']['tag'], "TEST001")

    @patch('os.path.exists')
    def test_parse_pdf_set_file_not_found(self, mock_exists):
        """Test parsing when PDF file doesn't exist."""
        mock_exists.return_value = False
        result = self.parser.parse_pdf_set("nonexistent.pdf")
        self.assertIsInstance(result, EplanDrawingSet)

    @patch('pyrox.services.eplan.EplanPDFParser._extract_text_multiple_methods')
    @patch('os.path.exists')
    def test_parse_single_pdf_success(self, mock_exists, mock_extract):
        """Test successful single PDF parsing."""
        mock_exists.return_value = True
        mock_extract.return_value = {
            'pdfplumber': [{'text': 'TEST PROJECT PLC001 192.168.1.100', 'page': 1}],
            'pymupdf': [],
            'pypdf2': []
        }

        self.parser._parse_single_pdf("test.pdf")
        self.assertIsNotNone(self.parser.drawing_set)

    def test_post_process_data(self):
        """Test post-processing of extracted data."""
        # Set up test data
        device = IODevice(tag="NET001")
        net_device = NetworkDevice(tag="NET001", ip_address="192.168.1.50")

        self.parser.drawing_set.devices["NET001"] = device
        self.parser.drawing_set.network_devices["NET001"] = net_device
        self.parser.drawing_set.drawing_numbers = ["DWG001", "DWG001", "DWG002"]

        self.parser._post_process_data()

        # Verify IP address was linked
        self.assertEqual(self.parser.drawing_set.devices["NET001"].ip_address, "192.168.1.50")

        # Verify duplicates were removed
        self.assertEqual(len(self.parser.drawing_set.drawing_numbers), 2)
        self.assertIn("DWG001", self.parser.drawing_set.drawing_numbers)
        self.assertIn("DWG002", self.parser.drawing_set.drawing_numbers)


class TestEplanPDFParserIntegration(unittest.TestCase):
    """Integration tests for EPlan PDF parsing with mocked PDF libraries."""

    @patch('pyrox.services.eplan.pdfplumber')
    @patch('pyrox.services.eplan.fitz')
    @patch('pyrox.services.eplan.PyPDF2')
    @patch('os.path.exists')
    def test_extract_text_multiple_methods(self, mock_exists, mock_pypdf2, mock_fitz, mock_pdfplumber):
        """Test text extraction using multiple methods."""
        mock_exists.return_value = True

        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content from pdfplumber"
        mock_page.extract_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        # Mock PyMuPDF
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_page_fitz = Mock()
        mock_page_fitz.get_text.return_value = "Test content from PyMuPDF"
        mock_page_fitz.get_text.return_value = {"blocks": []}
        mock_fitz.open.return_value = mock_doc

        # Mock PyPDF2
        mock_reader = Mock()
        mock_page_pypdf2 = Mock()
        mock_page_pypdf2.extract_text.return_value = "Test content from PyPDF2"
        mock_reader.pages = [mock_page_pypdf2]
        mock_pypdf2.PdfReader.return_value = mock_reader

        parser = EplanPDFParser()
        result = parser._extract_text_multiple_methods("test.pdf")

        self.assertIn('pdfplumber', result)
        self.assertIn('pymupdf', result)
        self.assertIn('pypdf2', result)

        # Verify content was extracted
        self.assertTrue(len(result['pdfplumber']) > 0)

    def test_export_to_file_json(self):
        """Test exporting to JSON file."""
        parser = EplanPDFParser()
        parser.drawing_set.project_name = "Test Export"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            parser.export_to_file(temp_file, 'json')

            # Verify file was created and contains correct data
            with open(temp_file, 'r') as f:
                data = json.load(f)
                self.assertEqual(data['project_name'], "Test Export")

        finally:
            os.unlink(temp_file)

    def test_export_to_file_csv(self):
        """Test exporting to CSV file."""
        parser = EplanPDFParser()
        device = IODevice(
            tag="TEST001",
            device_type="Test Device",
            manufacturer="Test Mfg",
            part_number="TEST-123",
            ip_address="192.168.1.1"
        )
        parser.drawing_set.devices["TEST001"] = device

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_file = f.name

        try:
            parser.export_to_file(temp_file, 'csv')

            # Verify CSV file was created
            self.assertTrue(os.path.exists(temp_file))

            with open(temp_file, 'r') as f:
                content = f.read()
                self.assertIn('TEST001', content)
                self.assertIn('Test Device', content)

        finally:
            os.unlink(temp_file)


class TestConvenienceFunction(unittest.TestCase):
    """Test the convenience function parse_eplan_pdfs."""

    @patch('pyrox.services.eplan.EplanPDFParser')
    def test_parse_eplan_pdfs_single_file(self, mock_parser_class):
        """Test parsing single PDF file."""
        mock_parser = Mock()
        mock_drawing_set = EplanDrawingSet(project_name="Test")
        mock_parser.parse_pdf_set.return_value = mock_drawing_set
        mock_parser_class.return_value = mock_parser

        result = parse_eplan_pdfs("test.pdf")

        mock_parser.parse_pdf_set.assert_called_once_with("test.pdf")
        self.assertEqual(result.project_name, "Test")

    @patch('pyrox.services.eplan.EplanPDFParser')
    def test_parse_eplan_pdfs_multiple_files(self, mock_parser_class):
        """Test parsing multiple PDF files."""
        mock_parser = Mock()
        mock_drawing_set = EplanDrawingSet(project_name="Multi Test")
        mock_parser.parse_pdf_set.return_value = mock_drawing_set
        mock_parser_class.return_value = mock_parser

        pdf_files = ["test1.pdf", "test2.pdf", "test3.pdf"]
        result = parse_eplan_pdfs(pdf_files)

        mock_parser.parse_pdf_set.assert_called_once_with(pdf_files)
        self.assertEqual(result.project_name, "Multi Test")

    @patch('pyrox.services.eplan.EplanPDFParser')
    def test_parse_eplan_pdfs_with_output_file(self, mock_parser_class):
        """Test parsing with output file export."""
        mock_parser = Mock()
        mock_drawing_set = EplanDrawingSet(project_name="Export Test")
        mock_parser.parse_pdf_set.return_value = mock_drawing_set
        mock_parser_class.return_value = mock_parser

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_file = f.name

        try:
            _ = parse_eplan_pdfs("test.pdf", output_file)

            mock_parser.export_to_file.assert_called_once_with(output_file, 'json')

        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""

    def test_missing_pdf_libraries(self):
        """Test handling of missing PDF libraries."""
        # This test would need to be run in an environment without the PDF libraries
        # For now, we'll just verify the import structure is correct
        self.assertTrue(hasattr(EplanPDFParser, '_extract_text_multiple_methods'))

    @patch('os.path.exists')
    def test_nonexistent_file_handling(self, mock_exists):
        """Test handling of nonexistent files."""
        mock_exists.return_value = False

        parser = EplanPDFParser()
        result = parser.parse_pdf_set("nonexistent.pdf")
        self.assertIsInstance(result, EplanDrawingSet)

    def test_regex_pattern_compilation(self):
        """Test that all regex patterns compile without errors."""
        parser = EplanPDFParser()

        # Test device patterns
        for pattern_name, pattern in parser._device_patterns.items():
            self.assertIsNotNone(pattern)

        # Test IP patterns
        for pattern_name, pattern in parser._ip_patterns.items():
            self.assertIsNotNone(pattern)

        # Test power patterns
        for pattern_name, pattern in parser._power_patterns.items():
            self.assertIsNotNone(pattern)


if __name__ == "__main__":
    unittest.main()
