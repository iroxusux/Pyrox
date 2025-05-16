from __future__ import annotations


from unittest.mock import MagicMock, patch
from typing import TypeVar
import unittest
import lxml
import lxml.etree as ET


from .plc import (
    AddOnInstruction,
    ConnectionParameters,
    Datatype,
    DatatypeMember,
    Routine,
    Controller,
    ControllerReport,
    ControllerReportItem,
    ControllerConfiguration,
    LogixElement,
    Module,
    PlcObject,
    Program,
    ProgramTag,
    Rung,
    SupportsMeta,
    SupportsClass,
    SupportsExternalAccess,
    SupportsRadix,
    Tag,
)

from .gm import (
    GmAddOnInstruction,
    GmDatatype,
    GmModule,
    GmPlcObject,
    GmProgram,
    GmRoutine,
    GmRung,
    GmTag,
    KDiag,
    KDiagProgramType,
    KDiagType,
    TextListElement,
)


from ...services.plc_services import xml_dict_from_file


T = TypeVar('T')


class TestControllerDictFromFile(unittest.TestCase):
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            xml_dict_from_file("non_existent_file.L5X")

    def test_invalid_file_extension(self):
        with self.assertRaises(ValueError):
            xml_dict_from_file("invalid_file.txt")

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    def test_parse_error(self, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parse.side_effect = ET.ParseError
        result = xml_dict_from_file("invalid_file.L5X")
        self.assertIsNone(result)

    @patch("os.path.exists")
    @patch("lxml.etree.parse")
    def test_unexpected_error(self, mock_parse, mock_exists):
        mock_exists.return_value = True
        mock_parse.side_effect = Exception("Unexpected error")
        result = xml_dict_from_file("unexpected_error.L5X")
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
        result = xml_dict_from_file("valid_file.L5X")
        self.assertEqual(result, {"root": {}})


class MockRoutine(Routine):
    def __init__(self, l5x_meta_data=None, controller=None, program=None):
        super().__init__()


class MockController(Controller):
    pass


class TestProgram(unittest.TestCase):
    @patch("pyrox.services.plc_services.xml_dict_from_file")
    def test_initialization_with_meta_data(self, mock_xml_dict_from_file):
        mock_xml_dict_from_file.return_value = {"Routines": {"Routine": {}}}
        controller = MockController()
        program = Program(name="TestProgram", l5x_meta_data={"Routines": {"Routine": {}}}, controller=controller)
        self.assertEqual(program.name, "TestProgram")
        self.assertEqual(len(program.routines), 1)

    def test_initialization_without_meta_data(self):
        controller = MockController()
        program = Program(name="TestProgram", controller=controller)
        self.assertEqual(program.name, "TestProgram")
        self.assertEqual(len(program.routines), 1)

    def test_test_edits_property(self):
        program = Program(l5x_meta_data={"@TestEdits": "TestEditsValue"})
        self.assertEqual(program.test_edits, "TestEditsValue")

    def test_main_routine_name_property(self):
        program = Program(l5x_meta_data={"@MainRoutineName": "MainRoutineNameValue"})
        self.assertEqual(program.main_routine_name, "MainRoutineNameValue")

    def test_disabled_property(self):
        program = Program(l5x_meta_data={"@Disabled": "DisabledValue"})
        self.assertEqual(program.disabled, "DisabledValue")

    def test_use_as_folder_property(self):
        program = Program(l5x_meta_data={"@UseAsFolder": "UseAsFolderValue"})
        self.assertEqual(program.use_as_folder, "UseAsFolderValue")

    def test_tags_property(self):
        program = Program(l5x_meta_data={"Tags": {"Tag": {"name": "Tag1"}}})
        self.assertEqual(program.tags, [{"name": "Tag1"}])

    def test_tags_property_empty(self):
        program = Program(l5x_meta_data={"Tags": None})
        self.assertEqual(program.tags, [])

    def test_routines_property(self):
        program = Program(l5x_meta_data={"Routines": {"Routine": {}}})
        self.assertEqual(len(program.routines), 1)

    def test_raw_routines_property(self):
        program = Program(l5x_meta_data={"Routines": {"Routine": {}}})
        self.assertEqual(len(program.raw_routines), 1)

    def test_validate_method(self):
        program = Program()
        report_item = program.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, program)


class TestPlcObject(unittest.TestCase):
    def setUp(self):
        self.controller = MockController()
        self.meta_data = {"@Name": "TestObject", "Description": "Test Description"}
        self.plc_object = PlcObject(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_initialization(self):
        self.assertEqual(self.plc_object.meta_data, self.meta_data)
        self.assertEqual(self.plc_object.controller, self.controller)

    def test_getitem(self):
        self.assertEqual(self.plc_object["@Name"], "TestObject")
        self.assertEqual(self.plc_object["Description"], "Test Description")
        self.assertIsNone(self.plc_object["NonExistentKey"])

    def test_setitem(self):
        self.plc_object["@Name"] = "NewName"
        self.assertEqual(self.plc_object["@Name"], "NewName")

    def test_name_property(self):
        self.assertEqual(self.plc_object.name, "TestObject")
        self.plc_object.name = "NewName"
        self.assertEqual(self.plc_object.name, "NewName")

    def test_name_property_invalid(self):
        with self.assertRaises(self.plc_object.InvalidNamingException):
            self.plc_object.name = "Invalid Name!"

    def test_description_property(self):
        self.assertEqual(self.plc_object.description, "Test Description")
        self.plc_object.description = "New Description"
        self.assertEqual(self.plc_object.description, "New Description")

    def test_config_property(self):
        self.assertIsInstance(self.plc_object.config, ControllerConfiguration)

    def test_validate_method(self):
        report_item = self.plc_object.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertFalse(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.plc_object)


class MockPlcObject(PlcObject):
    def __init__(self, l5x_meta_data=None, controller=None):
        super().__init__(l5x_meta_data, controller)


class MockSupportsMeta(SupportsMeta[str], MockPlcObject):
    def __init__(self, l5x_meta_data=None, controller=None):
        super().__init__(l5x_meta_data, controller)
        self._key = "test_key"

    @property
    def __key__(self):
        return self._key

    def __getitem__(self, key):
        return self._l5x_meta_data.get(key, None)

    def __setitem__(self, key, value):
        self._l5x_meta_data[key] = value


class TestSupportsMeta(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"test_key": "test_value"}
        self.controller = None
        self.supports_meta = MockSupportsMeta(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_initialization(self):
        self.assertEqual(self.supports_meta.meta_data, self.meta_data)
        self.assertEqual(self.supports_meta.controller, self.controller)

    def test_get_key(self):
        self.assertEqual(self.supports_meta.__key__, "test_key")

    def test_set_value(self):
        self.supports_meta.__set__("new_value")
        self.assertEqual(self.supports_meta["test_key"], "new_value")

    def test_set_invalid_value(self):
        with self.assertRaises(ValueError):
            self.supports_meta.__set__(123)

    def test_get_value(self):
        self.assertEqual(self.supports_meta.__get__(), "test_value")


class TestSupportsClass(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@Class": "TestClass"}
        self.supports_class = SupportsClass(l5x_meta_data=self.meta_data, controller=None)

    def test_key_property(self):
        self.assertEqual(self.supports_class.__key__, "@Class")

    def test_class_property(self):
        self.assertEqual(self.supports_class.class_, "TestClass")
        self.supports_class.class_ = "NewClass"
        self.assertEqual(self.supports_class.class_, "NewClass")


class TestSupportsExternalAccess(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@ExternalAccess": "ReadWrite"}
        self.supports_external_access = SupportsExternalAccess(l5x_meta_data=self.meta_data, controller=None)

    def test_key_property(self):
        self.assertEqual(self.supports_external_access.__key__, "@ExternalAccess")

    def test_external_access_property(self):
        self.assertEqual(self.supports_external_access.external_access, "ReadWrite")
        self.supports_external_access.external_access = "ReadOnly"
        self.assertEqual(self.supports_external_access.external_access, "ReadOnly")


class TestSupportsRadix(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@Radix": "Decimal"}
        self.supports_radix = SupportsRadix(l5x_meta_data=self.meta_data, controller=None)

    def test_key_property(self):
        self.assertEqual(self.supports_radix.__key__, "@Radix")

    def test_radix_property(self):
        self.assertEqual(self.supports_radix.radix, "Decimal")
        self.supports_radix.radix = "Hex"
        self.assertEqual(self.supports_radix.radix, "Hex")


class TestAddOnInstruction(unittest.TestCase):
    def setUp(self):
        self.meta_data = {
            "@Revision": "1.0",
            "@ExecutePrescan": "True",
            "@ExecutePostscan": "True",
            "@ExecuteEnableInFalse": "False",
            "@CreatedDate": "2023-01-01",
            "@CreatedBy": "User",
            "@EditedDate": "2023-01-02",
            "@EditedBy": "User",
            "@SoftwareRevision": "1.0",
            "RevisionNote": "Initial revision",
            "Parameters": {"Parameter": [{"name": "Param1"}]},
            "LocalTags": {"LocalTag": [{"name": "Tag1"}]},
            "Routines": {"Routine": [{"name": "Routine1"}]}
        }
        self.controller = MockController()
        self.add_on_instruction = AddOnInstruction(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_revision_property(self):
        self.assertEqual(self.add_on_instruction.revision, "1.0")

    def test_execute_prescan_property(self):
        self.assertEqual(self.add_on_instruction.execute_prescan, "True")

    def test_execute_postscan_property(self):
        self.assertEqual(self.add_on_instruction.execute_postscan, "True")

    def test_execute_enable_in_false_property(self):
        self.assertEqual(self.add_on_instruction.execute_enable_in_false, "False")

    def test_created_date_property(self):
        self.assertEqual(self.add_on_instruction.created_date, "2023-01-01")

    def test_created_by_property(self):
        self.assertEqual(self.add_on_instruction.created_by, "User")

    def test_edited_date_property(self):
        self.assertEqual(self.add_on_instruction.edited_date, "2023-01-02")

    def test_edited_by_property(self):
        self.assertEqual(self.add_on_instruction.edited_by, "User")

    def test_software_revision_property(self):
        self.assertEqual(self.add_on_instruction.software_revision, "1.0")

    def test_revision_note_property(self):
        self.assertEqual(self.add_on_instruction.revision_note, "Initial revision")

    def test_parameters_property(self):
        self.assertEqual(self.add_on_instruction.parameters, [{"name": "Param1"}])

    def test_local_tags_property(self):
        self.assertEqual(self.add_on_instruction.local_tags, [{"name": "Tag1"}])

    def test_routines_property(self):
        self.assertEqual(self.add_on_instruction.routines, [{"name": "Routine1"}])

    def test_validate_method(self):
        report_item = self.add_on_instruction.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.add_on_instruction)


class TestConnectionParameters(unittest.TestCase):
    def test_initialization(self):
        conn_params = ConnectionParameters(ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.ip_address, "192.168.1.1")
        self.assertEqual(conn_params.slot, 1)
        self.assertEqual(conn_params.rpi, 50)

    def test_invalid_ip_address(self):
        with self.assertRaises(ValueError):
            ConnectionParameters(ip_address="192.168.1", slot=1, rpi=50)

    def test_ip_address_property(self):
        conn_params = ConnectionParameters(ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.ip_address, "192.168.1.1")

    def test_slot_property(self):
        conn_params = ConnectionParameters(ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.slot, 1)

    def test_rpi_property(self):
        conn_params = ConnectionParameters(ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.rpi, 50)


class TestDatatypeMember(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@Dimension": "3", "@Hidden": "False"}
        self.datatype = Datatype(l5x_meta_data={}, controller=MockController())
        self.controller = MockController()
        self.datatype_member = DatatypeMember(l5x_meta_data=self.meta_data,
                                              datatype=self.datatype, controller=self.controller)

    def test_initialization(self):
        self.assertEqual(self.datatype_member.meta_data, self.meta_data)
        self.assertEqual(self.datatype_member.datatype, self.datatype)
        self.assertEqual(self.datatype_member.controller, self.controller)

    def test_dimension_property(self):
        self.assertEqual(self.datatype_member.dimension, "3")

    def test_hidden_property(self):
        self.assertEqual(self.datatype_member.hidden, "False")


class TestDatatype(unittest.TestCase):
    def setUp(self):
        self.meta_data = {
            "@Family": "TestFamily",
            "Members": {"Member": [{"@Name": "Member1"}, {"@Name": "Member2"}]}
        }
        self.controller = MockController()
        self.datatype = Datatype(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_initialization(self):
        self.assertEqual(self.datatype.meta_data, self.meta_data)
        self.assertEqual(self.datatype.controller, self.controller)
        self.assertEqual(len(self.datatype.members), 2)

    def test_family_property(self):
        self.assertEqual(self.datatype.family, "TestFamily")

    def test_members_property(self):
        self.assertEqual(len(self.datatype.members), 2)
        self.assertIsInstance(self.datatype.members[0], DatatypeMember)
        self.assertIsInstance(self.datatype.members[1], DatatypeMember)

    def test_raw_members_property(self):
        self.assertEqual(len(self.datatype.raw_members), 2)
        self.assertEqual(self.datatype.raw_members[0]["@Name"], "Member1")
        self.assertEqual(self.datatype.raw_members[1]["@Name"], "Member2")

    def test_validate_method(self):
        report_item = self.datatype.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.datatype)


class TestModule(unittest.TestCase):
    def setUp(self):
        self.meta_data = {
            "@CatalogNumber": "12345",
            "@Vendor": "VendorName",
            "@ProductType": "TypeA",
            "@ProductCode": "Code123",
            "@Major": "1",
            "@Minor": "0",
            "@ParentModule": "ParentModule1",
            "@ParentModPortId": "Port1",
            "@Inhibited": "False",
            "@MajorFault": "False",
            "EKey": {"Key": "Value"},
            "Ports": {"Port": [{"name": "Port1"}]},
            "Communications": {"Connections": {"Connection": [{"@Name": "Standard", "@Unicast": "true", "@RPI": "20000"}]}}  # noqa: E501
        }
        self.controller = MockController()
        self.module = Module(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_catalog_number_property(self):
        self.assertEqual(self.module.catalog_number, "12345")

    def test_vendor_property(self):
        self.assertEqual(self.module.vendor, "VendorName")

    def test_product_type_property(self):
        self.assertEqual(self.module.product_type, "TypeA")

    def test_product_code_property(self):
        self.assertEqual(self.module.product_code, "Code123")

    def test_major_property(self):
        self.assertEqual(self.module.major, "1")

    def test_minor_property(self):
        self.assertEqual(self.module.minor, "0")

    def test_parent_module_property(self):
        self.assertEqual(self.module.parent_module, "ParentModule1")

    def test_parent_mod_port_id_property(self):
        self.assertEqual(self.module.parent_mod_port_id, "Port1")

    def test_inhibited_property(self):
        self.assertEqual(self.module.inhibited, "False")

    def test_major_fault_property(self):
        self.assertEqual(self.module.major_fault, "False")

    def test_ekey_property(self):
        self.assertEqual(self.module.ekey, {"Key": "Value"})

    def test_ports_property(self):
        self.assertEqual(self.module.ports, [{"name": "Port1"}])

    def test_communications_property(self):
        self.assertEqual(self.module.communications, {"Connections": {"Connection": [
                         {"@Name": "Standard", "@Unicast": "true", "@RPI": "20000"}]}})

    def test_validate_method(self):
        report_item = self.module.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.module)


class MockProgram(Program):
    pass


class TestProgramTag(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@Name": "TestTag"}
        self.controller = MockController()
        self.program = MockProgram()
        self.program_tag = ProgramTag(l5x_meta_data=self.meta_data, controller=self.controller, program=self.program)

    def test_initialization(self):
        self.assertEqual(self.program_tag.meta_data, self.meta_data)
        self.assertEqual(self.program_tag.controller, self.controller)
        self.assertEqual(self.program_tag.program, self.program)


class TestRoutine(unittest.TestCase):
    @patch("pyrox.services.plc_services.xml_dict_from_file")
    def setUp(self, mock_xml_dict_from_file):
        mock_xml_dict_from_file.return_value = {"RLLContent": {
            "Rung": [{"@Number": "1", "@Type": "TypeA", "Comment": "Test Comment", "Text": "Test Text"}]}}
        self.meta_data = {"RLLContent": {
            "Rung": [{"@Number": "1", "@Type": "TypeA", "Comment": "Test Comment", "Text": "Test Text"}]}}
        self.controller = MockController()
        self.program = MockProgram()
        self.routine = Routine(name="TestRoutine", l5x_meta_data=self.meta_data,
                               controller=self.controller, program=self.program)

    def test_initialization(self):
        self.assertEqual(self.routine.meta_data, self.meta_data)
        self.assertEqual(self.routine.controller, self.controller)
        self.assertEqual(self.routine.program, self.program)
        self.assertEqual(len(self.routine.rungs), 1)

    def test_rungs_property(self):
        self.assertEqual(len(self.routine.rungs), 1)
        self.assertIsInstance(self.routine.rungs[0], Rung)

    def test_raw_rungs_property(self):
        self.assertEqual(len(self.routine.raw_rungs), 1)
        self.assertEqual(self.routine.raw_rungs[0]["@Number"], "1")


class TestRung(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@Number": "1", "@Type": "TypeA", "Comment": "Test Comment", "Text": "Test Text"}
        self.controller = MockController()
        self.routine = MockRoutine()
        self.rung = Rung(l5x_meta_data=self.meta_data, controller=self.controller, routine=self.routine)

    def test_initialization(self):
        self.assertEqual(self.rung.meta_data, self.meta_data)
        self.assertEqual(self.rung.controller, self.controller)
        self.assertEqual(self.rung.routine, self.routine)

    def test_number_property(self):
        self.assertEqual(self.rung.number, "1")

    def test_type_property(self):
        self.assertEqual(self.rung.type, "TypeA")

    def test_comment_property(self):
        self.assertEqual(self.rung.comment, "Test Comment")

    def test_text_property(self):
        self.assertEqual(self.rung.text, "Test Text")

    def test_instructions_property(self):
        self.assertEqual(self.rung.instructions, [])


class TestTag(unittest.TestCase):
    def setUp(self):
        self.meta_data = {"@TagType": "Base", "@DataType": "DINT",
                          "@Constant": "False", "@OpcUaAccess": "ReadWrite", "Data": {"Value": "123"}}
        self.controller = MockController()
        self.tag = Tag(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_initialization(self):
        self.assertEqual(self.tag.meta_data, self.meta_data)
        self.assertEqual(self.tag.controller, self.controller)

    def test_tag_type_property(self):
        self.assertEqual(self.tag.tag_type, "Base")

    def test_datatype_property(self):
        self.assertEqual(self.tag.datatype, "DINT")

    def test_constant_property(self):
        self.assertEqual(self.tag.constant, "False")

    def test_opc_ua_access_property(self):
        self.assertEqual(self.tag.opc_ua_access, "ReadWrite")

    def test_data_property(self):
        self.assertEqual(self.tag.data, [{"Value": "123"}])

    def test_validate_method(self):
        report_item = self.tag.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.tag)


class TestController(unittest.TestCase):

    def setUp(self):
        self.root_meta_data = {'RSLogix5000Content': {'Controller': {'@CommPath': 'path', '@MajorRev': '1', '@MinorRev': '0', '@Name': 'TestController', 'Modules': {'Module': [{'@Name': 'Local', 'Ports': {       # noqa: E501
            'Port': [{'@Type': 'ICP', '@Address': '1'}]}}]}, 'Programs': {'Program': []}, 'Tags': {'Tag': []}, 'AddOnInstructionDefinitions': {'AddOnInstructionDefinition': []}, 'DataTypes': {'DataType': []}}}}  # noqa: E501
        self.config = ControllerConfiguration()
        self.controller = Controller(root_meta_data=self.root_meta_data, config=self.config)

    def test_init(self):
        self.assertEqual(self.controller._root_meta_data, self.root_meta_data)
        self.assertEqual(self.controller._file_location, '')
        self.assertEqual(self.controller._ip_address, '')
        self.assertEqual(self.controller._slot, 0)
        self.assertEqual(self.controller._config, self.config)

    def test_properties(self):
        self.controller._root_meta_data = {'RSLogix5000Content': {'Controller': {'@CommPath': 'path', '@MajorRev': '1', '@MinorRev': '0', '@Name': 'TestController', 'Modules': {'Module': [{'@Name': 'Local', 'Ports': {  # noqa: E501
            'Port': [{'@Type': 'ICP', '@Address': '1'}]}}]}, 'Programs': {'Program': []}, 'Tags': {'Tag': []}, 'AddOnInstructionDefinitions': {'AddOnInstructionDefinition': []}, 'DataTypes': {'DataType': []}}}}         # noqa: E501

        self.assertEqual(self.controller.comm_path, 'path')
        self.assertEqual(self.controller.major_revision, 1)
        self.assertEqual(self.controller.minor_revision, 0)
        self.assertEqual(self.controller.name, 'TestController')
        self.assertEqual(self.controller.slot, 1)
        self.assertEqual(self.controller.plc_module['@Name'], 'Local')
        self.assertEqual(self.controller.plc_module_icp_port['@Address'], '1')
        self.assertEqual(self.controller.plc_module_ports[0]['@Type'], 'ICP')
        self.assertEqual(self.controller.raw_programs, [])
        self.assertEqual(self.controller.raw_tags, [])
        self.assertEqual(self.controller.raw_aois, [])
        self.assertEqual(self.controller.raw_datatypes, [])
        self.assertEqual(self.controller.raw_modules[0]['@Name'], 'Local')

    def test_assign_address(self):
        with self.assertRaises(ValueError):
            self.controller._assign_address('invalid_address')

        self.controller._assign_address('192.168.1.1')
        self.assertEqual(self.controller.ip_address, '192.168.1.1')

    def test_add_program(self):
        program = Program(name='TestProgram', controller=self.controller)
        self.controller.add_program(program)
        self.assertIn(program, self.controller.programs)

        program_dict = {'@Name': 'TestProgram'}
        self.controller.add_program(program_dict)
        self.assertEqual(self.controller.programs[-1].name, 'TestProgram')

        program_name = 'TestProgram'
        self.controller.add_program(program_name)
        self.assertEqual(self.controller.programs[-1].name, 'TestProgram')

        with self.assertRaises(TypeError):
            self.controller.add_program(123)

    def test_find_diagnostic_rungs(self):
        mock_rung = MagicMock()
        mock_rung.comment = '<@DIAG>'
        mock_rung.instructions = ['JSR(zZ999_Diagnostics)']
        mock_routine = MagicMock()
        mock_routine.rungs = [mock_rung]
        mock_program = MagicMock()
        mock_program.routines = [mock_routine]
        self.controller._programs = [mock_program]

        diagnostic_rungs = self.controller.find_diagnostic_rungs()
        self.assertEqual(diagnostic_rungs, [mock_rung])

    def test_find_redundant_otes(self):
        mock_rung = MagicMock()
        mock_rung.instructions = ['OTE(tag1)', 'OTE(tag2)']
        mock_routine = MagicMock()
        mock_routine.rungs = [mock_rung]
        mock_program = MagicMock()
        mock_program.routines = [mock_routine]
        self.controller._programs = [mock_program]

        redundant_otes = self.controller.find_redundant_otes()
        self.assertTrue(len(redundant_otes) == 0)

    def test_rename_asset(self):
        self.controller.raw_tags = {'Tag': [{'@Name': 'old_name'}]}
        self.controller.rename_asset(LogixElement.TAG, 'old_name', 'new_name')
        self.assertEqual(self.controller.raw_tags[0]['@Name'], 'new_name')

        self.controller.l5x_meta_data = {'@Name': 'old_name'}
        self.controller.rename_asset(LogixElement.ALL, 'old_name', 'new_name')
        self.assertEqual(self.controller.l5x_meta_data['@Name'], 'new_name')

    def test_validate(self):
        report = self.controller.validate()
        self.assertIsInstance(report, ControllerReport)


class TestTextListElement(unittest.TestCase):

    def setUp(self):
        self.text = "Diagnostic text with number <kAlarm[123] This is an example alarm!>"
        self.rung = MagicMock(spec=GmRung)
        self.element = TextListElement(text=self.text, rung=self.rung)

    def test_init(self):
        self.assertEqual(self.element.text, "<kAlarm[123] This is an example alarm!>")
        self.assertEqual(self.element.number, 123)
        self.assertIsInstance(self.element.rung, GmRung)

    def test_eq(self):
        other = TextListElement(text=self.text, rung=self.rung)
        self.assertEqual(self.element, other)

    def test_hash(self):
        self.assertEqual(hash(self.element), hash((self.element.text, self.element.number)))

    def test_repr(self):
        self.assertEqual(repr(
            self.element), f'text={self.element.text}, text_list_id={self.element.text_list_id}number={self.element.number}, rung={self.element.rung}')  # noqa: E501

    def test_str(self):
        self.assertEqual(str(self.element), self.element.text)

    def test_get_diag_number(self):
        with self.assertRaises(ValueError):
            TextListElement(text="Invalid text", rung=self.rung)

    def test_get_diag_text(self):
        with self.assertRaises(ValueError):
            TextListElement(text="Invalid text", rung=self.rung)

    def test_get_tl_id(self):
        self.assertIsNone(self.element._get_tl_id())


class TestKDiag(unittest.TestCase):

    def setUp(self):
        self.text = "Diagnostic text with number <kAlarm[123] This is an example alarm!>"
        self.rung = MagicMock(spec=GmRung)
        self.diag_type = KDiagType.ALARM
        self.parent_offset = 10
        self.kdiag = KDiag(diag_type=self.diag_type, text=self.text, parent_offset=self.parent_offset, rung=self.rung)

    def test_init(self):
        self.assertEqual(self.kdiag.text, "<kAlarm[123] This is an example alarm!>")
        self.assertEqual(self.kdiag.number, 123)
        self.assertEqual(self.kdiag.diag_type, KDiagType.ALARM)
        self.assertEqual(self.kdiag.parent_offset, 10)
        self.assertIsInstance(self.kdiag.rung, GmRung)

    def test_eq(self):
        other = KDiag(diag_type=self.diag_type, text=self.text, parent_offset=self.parent_offset, rung=self.rung)
        self.assertEqual(self.kdiag, other)

    def test_hash(self):
        self.assertEqual(hash(self.kdiag), hash((self.kdiag.text, self.kdiag.diag_type.value,
                         self.kdiag.col_location, self.kdiag.number, self.kdiag.parent_offset)))

    def test_repr(self):
        self.assertEqual(repr(
            self.kdiag), f'KDiag(text={self.kdiag.text}, diag_type={self.kdiag.diag_type}, col_location={self.kdiag.col_location}, number={self.kdiag.number}, parent_offset={self.kdiag.parent_offset}), rung={self.kdiag.rung}')  # noqa: E501

    def test_global_number(self):
        self.assertEqual(self.kdiag.global_number, 133)

    def test_get_col_location(self):
        self.assertIsNone(self.kdiag._get_col_location())


class TestGmPlcObject(unittest.TestCase):

    def setUp(self):
        self.obj = GmPlcObject()
        self.obj.name = "za_Action"
        self.obj._controller = None

    def test_config(self):
        config = self.obj.config
        self.assertIsInstance(config, ControllerConfiguration)
        self.assertEqual(config.aoi_type, GmAddOnInstruction)
        self.assertEqual(config.datatype_type, GmDatatype)
        self.assertEqual(config.module_type, GmModule)
        self.assertEqual(config.program_type, GmProgram)
        self.assertEqual(config.routine_type, GmRoutine)
        self.assertEqual(config.rung_type, GmRung)
        self.assertEqual(config.tag_type, GmTag)

    def test_is_gm_owned(self):
        self.assertTrue(self.obj.is_gm_owned)

    def test_is_user_owned(self):
        self.obj.name = "user_Action"
        self.assertTrue(self.obj.is_user_owned)


class TestGmAddOnInstruction(unittest.TestCase):

    def setUp(self):
        self.obj = GmAddOnInstruction()
        self.obj.name = "za_Action"

    def test_is_gm_owned(self):
        self.assertTrue(self.obj.is_gm_owned)


class TestGmDatatype(unittest.TestCase):

    def setUp(self):
        self.obj = GmDatatype()
        self.obj.name = "za_Action"

    def test_is_gm_owned(self):
        self.assertTrue(self.obj.is_gm_owned)


class TestGmModule(unittest.TestCase):

    def setUp(self):
        self.obj = GmModule()
        self.obj.name = "za_Action"

    def test_is_gm_owned(self):
        self.assertTrue(self.obj.is_gm_owned)


class TestGmRung(unittest.TestCase):

    def setUp(self):
        self.obj = GmRung()
        self.obj.name = "za_Action"
        self.obj.comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"

    def test_is_gm_owned(self):
        self.assertTrue(self.obj.is_gm_owned)

    def test_has_kdiag(self):
        self.assertTrue(self.obj.has_kdiag)

    def test_kdiags(self):
        self.obj.routine = MagicMock()
        self.obj.routine.program.parameter_offset = 10
        kdiags = self.obj.kdiags
        self.assertEqual(len(kdiags), 1)
        self.assertIsInstance(kdiags[0], KDiag)
        self.assertEqual(kdiags[0].diag_type, KDiagType.ALARM)

    def test_text_list_items(self):
        self.obj.comment = "<TL[1]: This is a text list item>"
        text_list_items = self.obj.text_list_items
        self.assertEqual(len(text_list_items), 1)
        self.assertIsInstance(text_list_items[0], TextListElement)


class TestGmRoutine(unittest.TestCase):

    def setUp(self):
        self.routine = GmRoutine()
        self.routine._program = MagicMock()
        self.routine.rungs[0].comment = '<@DIAG> <Alarm[69]: This is a diagnostic comment!>'

    def test_kdiags(self):
        kdiags = self.routine.kdiag_rungs
        self.assertEqual(len(kdiags), 1)
        self.assertIsInstance(kdiags[0], KDiag)

    def test_program(self):
        self.assertIsInstance(self.routine.program, MagicMock)

    def test_rungs(self):
        self.assertEqual(len(self.routine.rungs), 1)
        self.assertIsInstance(self.routine.rungs[0], GmRung)

    def test_text_list_items(self):
        text_list_items = self.routine.text_list_items
        self.assertEqual(len(text_list_items), 1)
        self.assertIsInstance(text_list_items[0], TextListElement)


class TestGmTag(unittest.TestCase):

    def setUp(self):
        self.tag = GmTag()
        self.tag.name = "za_Action"

    def test_is_gm_owned(self):
        self.assertTrue(self.tag.is_gm_owned)


class TestGmProgram(unittest.TestCase):

    def setUp(self):
        self.program = GmProgram()
        self.program.name = "TestProgram"

    def test_is_gm_owned(self):
        self.program.routines[0].name = 'zSomeRoutine'
        self.assertTrue(self.program.is_gm_owned)

    def test_is_user_owned(self):
        self.program.routines[0].name = 'uSomeRoutine'
        self.assertTrue(self.program.is_user_owned)

    def test_diag_name(self):
        self.program.routines[0].name = 'B001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.assertEqual(self.program.diag_name, "IFD5075")

    def test_diag_setup(self):
        self.program.routines[0].name = 'B001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines[0].rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        diag_setup = self.program.diag_setup
        self.assertEqual(diag_setup['program_name'], self.program.name)
        self.assertEqual(diag_setup['diag_name'], "IFD5075")
        self.assertEqual(diag_setup['msg_offset'], 0)
        self.assertEqual(diag_setup['hmi_tag'], 'TBD')
        self.assertEqual(diag_setup['program_type'], KDiagProgramType.NA)
        self.assertEqual(diag_setup['tag_alias_refs'], 'TBD')

    def test_kdiags(self):
        self.program.routines[0].name = 'B001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines[0].rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        kdiags = self.program.kdiags
        self.assertEqual(len(kdiags), 1)
        self.assertIsInstance(kdiags[0], KDiag)

    def test_parameter_offset(self):
        self.assertEqual(self.program.parameter_offset, 0)

    def test_parameter_routine(self):
        self.program.routines[0].name = 'B001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.assertIsInstance(self.program.parameter_routine, GmRoutine)

    def test_program_type(self):
        self.assertEqual(self.program.program_type, KDiagProgramType.NA)

    def test_routines(self):
        self.assertEqual(len(self.program.routines), 1)
        self.assertIsInstance(self.program.routines[0], GmRoutine)

    def test_text_list_items(self):
        self.program.routines[0].name = 'B001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines[0].rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        text_list_items = self.program.text_list_items
        self.assertEqual(len(text_list_items), 1)
        self.assertIsInstance(text_list_items[0], TextListElement)

    def test_gm_routines(self):
        self.program.routines[0].name = 'zB001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines[0].rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        gm_routines = self.program.gm_routines
        self.assertEqual(len(gm_routines), 1)
        self.assertIsInstance(gm_routines[0], GmRoutine)

    def test_user_routines(self):
        self.program.routines[0].name = 'uB001_Parameters'
        self.program.routines[0].rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines[0].rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        user_routines = self.program.user_routines
        self.assertEqual(len(user_routines), 1)
        self.assertIsInstance(user_routines[0], GmRoutine)


if __name__ == '__main__':
    unittest.main()
