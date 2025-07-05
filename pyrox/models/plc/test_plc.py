from __future__ import annotations


from typing import DefaultDict, TypeVar
import unittest
from unittest.mock import MagicMock


from ..abc.list import HashList


from .plc import (
    ConnectionParameters,
    DatatypeMember,
    Controller,
    ControllerReportItem,
    ControllerConfiguration,
    LogixInstruction,
    LogixInstructionType,
    NamedPlcObject,
    PlcObject,
    Program,
    ContainsRoutines,
    ContainsTags
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


T = TypeVar('T')
UNITTEST_PLC_FILE = r'docs\controls\unittest.L5X'


class TestPlcObject(unittest.TestCase):
    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {"@Name": "TestObject",
                          "Description": "Test Description"}
        self.plc_object = PlcObject(meta_data=self.meta_data, controller=self.controller)

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

    def test_config_property(self):
        self.assertEqual(self.plc_object.config, self.controller.config)

    def test_get_all_properties(self):
        # PlcObject has three properties: config, controller, meta_data
        props = self.plc_object.get_all_properties()
        self.assertIsInstance(props, dict)
        # Check that all property names are present
        self.assertIn('config', props)
        self.assertIn('controller', props)
        self.assertIn('meta_data', props)
        # Check that the values are correct
        self.assertEqual(props['config'], self.plc_object.config)
        self.assertEqual(props['controller'], self.plc_object.controller)
        self.assertEqual(props['meta_data'], self.plc_object.meta_data)

    def test_validate(self):
        # Should return a ControllerReportItem with pass_fail True and no notes for valid object
        report = self.plc_object.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(report.pass_fail)
        self.assertIn('Validating PlcObject object', report.test_description)
        self.assertEqual(report.test_notes, [])

        # Test with missing config, controller, and meta_data
        obj = PlcObject(meta_data=None, controller=None)
        report = obj.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertFalse(report.pass_fail)
        self.assertNotIn('No controller configuration found!', report.test_notes)
        self.assertIn('No controller found!', report.test_notes)
        self.assertIn('No meta data found!', report.test_notes)


class TestNamedPlcObject(unittest.TestCase):
    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {"@Name": "TestNamed", "Description": "Test Description"}
        self.named_obj = NamedPlcObject(meta_data=self.meta_data, controller=self.controller)

    def test_name_property(self):
        # Test getter
        self.assertEqual(self.named_obj.name, "TestNamed")
        # Test setter with valid string
        self.named_obj.name = "NewName"
        self.assertEqual(self.named_obj.name, "NewName")
        # Test setter with invalid string (simulate is_valid_string returning False)
        self.named_obj.is_valid_string = MagicMock(return_value=False)
        with self.assertRaises(self.named_obj.InvalidNamingException):
            self.named_obj.name = ""

    def test_description_property(self):
        # Test getter
        self.assertEqual(self.named_obj.description, "Test Description")
        # Test setter
        self.named_obj.description = "Updated description"
        self.assertEqual(self.named_obj.description, "Updated description")

    def test_repr_and_str(self):
        self.assertEqual(repr(self.named_obj), self.named_obj.name)
        self.assertEqual(str(self.named_obj), self.named_obj.name)

    def test_validate(self):
        # Should pass when both name and description are present
        report = self.named_obj.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(report.pass_fail)
        self.assertNotIn('No name found!', report.test_notes)
        self.assertNotIn('No description found!', report.test_notes)

        # Should fail if name is None
        self.named_obj._meta_data["@Name"] = None
        report = self.named_obj.validate()
        self.assertFalse(report.pass_fail)
        self.assertIn('No name found!', report.test_notes)

        # Should fail if description is None
        self.named_obj._meta_data["@Name"] = "TestNamed"
        self.named_obj._meta_data["Description"] = None
        report = self.named_obj.validate()
        self.assertFalse(report.pass_fail)
        self.assertIn('No description found!', report.test_notes)


class TestLogixOperand(unittest.TestCase):

    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('LogixOperand')
        self.routine = self.program.routines.get('main')

    def test_aliased_parents(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.aliased_parents, ['gFirstOperand'])
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.aliased_parents, ['SecondOperand'])
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.aliased_parents, ['SomeStruct.a', 'SomeStruct'])
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.aliased_parents, ['gStruct.a', 'gStruct'])
        operand = self.routine.rungs[4].instructions[0].operands[0]
        self.assertEqual(operand.aliased_parents, ['gStruct.c', 'gStruct'])
        operand = self.routine.rungs[5].instructions[0].operands[0]
        self.assertEqual(operand.aliased_parents, ['LocalProgramTagOnly'])
        operand = self.routine.rungs[8].instructions[0].operands[0]
        self.assertEqual(operand.aliased_parents, ['gStruct.Child.Age.0', 'gStruct.Child.Age', 'gStruct.Child', 'gStruct'])

    def test_arg_position(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.arg_position, 0)
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.arg_position, 1)

    def test_as_aliased(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'gFirstOperand')
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.as_aliased, 'SecondOperand')
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'SomeStruct.a')
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'gStruct.a')
        operand = self.routine.rungs[4].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'gStruct.c')
        operand = self.routine.rungs[5].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'LocalProgramTagOnly')
        operand = self.routine.rungs[8].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'gStruct.Child.Age.0')
        operand = self.routine.rungs[10].instructions[0].operands[0]
        self.assertEqual(operand.as_aliased, 'gStruct.Child.Age.0')

    def test_as_qualified(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.as_qualified, 'gFirstOperand')
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.as_qualified, 'SecondOperand')
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.as_qualified, 'SomeStruct.a')
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.as_qualified, 'gStruct.a')
        operand = self.routine.rungs[4].instructions[0].operands[0]
        self.assertEqual(operand.as_qualified, 'gStruct.c')
        operand = self.routine.rungs[5].instructions[0].operands[0]
        self.assertEqual(operand.as_qualified, 'Program:LogixOperand.LocalProgramTagOnly')

    def test_base_name(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.base_name, 'FirstOperand')
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.base_name, 'SecondOperand')
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.base_name, 'SomeStruct')
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.base_name, 'pStruct')

    def test_base_tag(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        base_tag = self.controller.tags.get('gFirstOperand')
        self.assertIsNotNone(base_tag)
        self.assertIsNotNone(operand.base_tag)
        self.assertEqual(operand.base_tag, base_tag)

        operand = self.routine.rungs[1].instructions[0].operands[1]
        base_tag = self.controller.tags.get('SecondOperand')
        self.assertIsNotNone(base_tag)
        self.assertIsNotNone(operand.base_tag)
        self.assertEqual(operand.base_tag, base_tag)

        operand = self.routine.rungs[3].instructions[1].operands[0]
        base_tag = self.controller.tags.get('gStruct')
        self.assertIsNotNone(base_tag)
        self.assertIsNotNone(operand.base_tag)
        self.assertEqual(operand.base_tag, base_tag)

        operand = self.routine.rungs[4].instructions[1].operands[0]
        base_tag = self.controller.tags.get('gStruct')
        self.assertIsNotNone(base_tag)
        self.assertIsNotNone(operand.base_tag)
        self.assertEqual(operand.base_tag, base_tag)

    def test_container(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.container, self.program)
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.container, self.program)
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.container, self.program)
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.container, self.program)
        operand = self.routine.rungs[4].instructions[0].operands[0]
        self.assertEqual(operand.container, self.program)
        operand = self.routine.rungs[5].instructions[0].operands[0]
        self.assertEqual(operand.container, self.program)

    def test_instruction(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.instruction, self.routine.rungs[0].instructions[0])
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.instruction, self.routine.rungs[1].instructions[0])
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.instruction, self.routine.rungs[2].instructions[0])

    def test_instruction_type(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.instruction_type, LogixInstructionType.OUTPUT)
        operand = self.routine.rungs[1].instructions[0].operands[0]
        self.assertEqual(operand.instruction_type, LogixInstructionType.INPUT)
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.instruction_type, LogixInstructionType.OUTPUT)
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.instruction_type, LogixInstructionType.INPUT)
        operand = self.routine.rungs[2].instructions[1].operands[0]
        self.assertEqual(operand.instruction_type, LogixInstructionType.OUTPUT)

    def test_first_tag(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        first_tag = operand.container.tags.get('FirstOperand')
        self.assertIsNotNone(first_tag)
        self.assertIsNotNone(operand.first_tag)
        self.assertEqual(operand.first_tag, first_tag)

        operand = self.routine.rungs[1].instructions[0].operands[1]
        first_tag = self.controller.tags.get('SecondOperand')
        self.assertIsNotNone(first_tag)
        self.assertIsNotNone(operand.first_tag)
        self.assertEqual(operand.first_tag, first_tag)

        operand = self.routine.rungs[2].instructions[0].operands[0]
        first_tag = self.controller.tags.get('SomeStruct')
        self.assertIsNotNone(first_tag)
        self.assertIsNotNone(operand.first_tag)
        self.assertEqual(operand.first_tag, first_tag)

        operand = self.routine.rungs[3].instructions[1].operands[0]
        first_tag = operand.container.tags.get('pStruct')
        self.assertIsNotNone(first_tag)
        self.assertIsNotNone(operand.first_tag)
        self.assertEqual(operand.first_tag, first_tag)

        operand = self.routine.rungs[4].instructions[1].operands[0]
        first_tag = operand.container.tags.get('DeeperAliasing')
        self.assertIsNotNone(first_tag)
        self.assertIsNotNone(operand.first_tag)
        self.assertEqual(operand.first_tag, first_tag)

    def test_parents(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.parents, ['FirstOperand'])
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.parents, ['SecondOperand'])
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.parents, ['SomeStruct.a', 'SomeStruct'])
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.parents, ['pStruct.a', 'pStruct'])

    def test_qualified_parents(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.qualified_parents, ['gFirstOperand'])
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.qualified_parents, ['SecondOperand'])
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.qualified_parents, ['SomeStruct.a', 'SomeStruct'])
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.qualified_parents, ['gStruct.a', 'gStruct'])

    def test_trailing_name(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.trailing_name, '')
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.trailing_name, '')
        operand = self.routine.rungs[2].instructions[0].operands[0]
        self.assertEqual(operand.trailing_name, '.a')
        operand = self.routine.rungs[3].instructions[0].operands[0]
        self.assertEqual(operand.trailing_name, '.a')
        operand = self.routine.rungs[8].instructions[0].operands[0]
        self.assertEqual(operand.trailing_name, '.Child.Age.0')
        operand = self.routine.rungs[9].instructions[0].operands[0]
        self.assertEqual(operand.trailing_name, '.Child.Name.DATA[0].0')

    def test_repr(self):
        operand = self.routine.rungs[0].instructions[0].operands[0]
        self.assertEqual(operand.meta_data, 'FirstOperand')
        operand = self.routine.rungs[1].instructions[0].operands[1]
        self.assertEqual(operand.meta_data, 'SecondOperand')


class TestLogixInstruction(unittest.TestCase):
    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('MainProgram')
        self.routine = self.program.routines.get('main')
        self.rung = self.routine.rungs[0]
        self.instruction = self.rung.instructions[0]

    def test_repr(self):
        self.assertEqual(self.instruction.meta_data, 'OTL(AlwaysOn)')

    def test_element(self):
        self.assertEqual(self.instruction.instruction_name, 'OTL')

    def test_operands(self):
        self.assertTrue(len(self.instruction.operands) == 1)
        self.assertEqual(self.instruction.operands[0].base_name, 'AlwaysOn')

    def test_container(self):
        self.assertEqual(self.instruction.container, self.program)

    def test_rung(self):
        self.assertEqual(self.instruction.rung, self.rung)

    def test_type(self):
        self.assertEqual(self.instruction.type, LogixInstructionType.OUTPUT)
        input_meta_data = 'XIC(JustABit)'
        input_instruction = LogixInstruction(meta_data=input_meta_data,
                                             controller=self.controller,
                                             rung=self.rung)
        self.assertEqual(input_instruction.type, LogixInstructionType.INPUT)


class TestRoutineContainer(unittest.TestCase):

    def setUp(self):
        self.mock_controller = Controller()
        self.mock_routine_type = MagicMock()
        self.mock_routine_instance = MagicMock()
        self.mock_routine_instance.instructions = ['instr1', 'instr2']

        self.meta_data = DefaultDict(None)
        self.meta_data['Routines'] = {
            'Routine': [{'@Name': 'Routine1'}, {'@Name': 'Routine2'}]
        }

        self.container = ContainsRoutines(meta_data=self.meta_data, controller=self.mock_controller)

    def test_raw_routines_multiple(self):
        expected = [{'@Name': 'Routine1'}, {'@Name': 'Routine2'}]
        self.assertEqual(self.container.raw_routines, expected)

    def test_raw_routines_single(self):
        self.container['Routines'] = {'Routine': {'Name': 'SingleRoutine'}}
        expected = [{'Name': 'SingleRoutine'}]
        self.assertEqual(self.container.raw_routines, expected)

    def test_raw_routines_empty(self):
        self.container['Routines'] = None
        self.assertEqual(self.container.raw_routines, [])

    def test_routines(self):
        routines = self.container.routines
        self.assertEqual(len(routines), 2)

    def test_instructions(self):
        instructions = self.container.instructions
        self.assertEqual(instructions, [])


class TestTagContainer(unittest.TestCase):

    def setUp(self):
        self.mock_controller = MagicMock()
        self.mock_tag_type = MagicMock()
        self.mock_tag_instance = MagicMock()

        self.meta_data = DefaultDict(None)
        self.meta_data['Tags'] = {
            'Tag': [{'Name': 'Tag1'}, {'Name': 'Tag2'}]
        }

        self.container = ContainsTags(meta_data=self.meta_data, controller=self.mock_controller)

    def test_raw_tags_multiple(self):
        expected = [{'Name': 'Tag1'}, {'Name': 'Tag2'}]
        self.assertEqual(self.container.raw_tags, expected)

    def test_raw_tags_single(self):
        self.container['Tags'] = {'Tag': {'Name': 'SingleTag'}}
        expected = [{'Name': 'SingleTag'}]
        self.assertEqual(self.container.raw_tags, expected)

    def test_raw_tags_empty(self):
        self.container['Tags'] = None
        self.assertEqual(self.container.raw_tags, [])

    def test_tags(self):
        tags = self.container.tags
        self.assertEqual(len(tags), 1)


class TestAddOnInstruction(unittest.TestCase):
    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.aoi = self.controller.aois.get('unittest_aoi')
        self.assertIsNotNone(self.aoi)

    def test_revision_property(self):
        self.assertEqual(self.aoi.revision, "1.0")

    def test_execute_prescan_property(self):
        self.assertEqual(self.aoi.execute_prescan, "false")

    def test_execute_postscan_property(self):
        self.assertEqual(self.aoi.execute_postscan, "false")

    def test_execute_enable_in_false_property(self):
        self.assertEqual(
            self.aoi.execute_enable_in_false, "false")

    def test_created_date_property(self):
        self.assertIsNotNone(self.aoi.created_date)

    def test_created_by_property(self):
        self.assertIsNotNone(self.aoi.created_by)

    def test_edited_date_property(self):
        self.assertIsNotNone(self.aoi.edited_date)

    def test_edited_by_property(self):
        self.assertIsNotNone(self.aoi.edited_by)

    def test_software_revision_property(self):
        self.assertEqual(self.aoi.software_revision, "v34.03")

    def test_revision_note_property(self):
        self.assertEqual(self.aoi.revision_note,
                         "initial release")

    def test_parameters_property(self):
        self.assertIsNotNone(self.aoi.parameters)

    def test_local_tags_property(self):
        self.assertIsNotNone(self.aoi.local_tags)


class TestConnectionParameters(unittest.TestCase):
    def test_initialization(self):
        conn_params = ConnectionParameters(
            ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.ip_address, "192.168.1.1")
        self.assertEqual(conn_params.slot, 1)
        self.assertEqual(conn_params.rpi, 50)

    def test_invalid_ip_address(self):
        with self.assertRaises(ValueError):
            ConnectionParameters(ip_address="192.168.1", slot=1, rpi=50)

    def test_ip_address_property(self):
        conn_params = ConnectionParameters(
            ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.ip_address, "192.168.1.1")

    def test_slot_property(self):
        conn_params = ConnectionParameters(
            ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.slot, 1)

    def test_rpi_property(self):
        conn_params = ConnectionParameters(
            ip_address="192.168.1.1", slot=1, rpi=50)
        self.assertEqual(conn_params.rpi, 50)


class TestDatatypeMember(unittest.TestCase):
    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.datatype = self.controller.datatypes.get('za_Parent')
        self.datatype_member = self.datatype.members[0]
        self.assertIsNotNone(self.datatype)
        self.assertIsNotNone(self.datatype_member)

    def test_dimension_property(self):
        self.assertEqual(self.datatype_member.dimension, "0")

    def test_hidden_property(self):
        self.assertEqual(self.datatype_member.hidden, "true")


class TestDatatype(unittest.TestCase):
    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.datatype = self.controller.datatypes.get('za_Parent')

    def test_initialization(self):
        self.assertTrue(len(self.datatype.members) > 1)

    def test_family_property(self):
        self.assertEqual(self.datatype.family, "NoFamily")

    def test_members_property(self):
        self.assertTrue(len(self.datatype.members) > 1)
        self.assertIsInstance(self.datatype.members[0], DatatypeMember)
        self.assertIsInstance(self.datatype.members[1], DatatypeMember)
        self.assertIsInstance(self.datatype.members[2], DatatypeMember)
        self.assertIsInstance(self.datatype.members[3], DatatypeMember)

    def test_raw_members_property(self):
        self.assertTrue(len(self.datatype.raw_members) > 1)

    def test_validate_method(self):
        report_item = self.datatype.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.datatype)


class TestModule(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.module = self.controller.modules.get('Local')

    def test_catalog_number_property(self):
        self.assertEqual(self.module.catalog_number, "1756-L81ES")

    def test_vendor_property(self):
        self.assertEqual(self.module.vendor, "1")

    def test_product_type_property(self):
        self.assertEqual(self.module.product_type, "14")

    def test_product_code_property(self):
        self.assertEqual(self.module.product_code, "211")

    def test_major_property(self):
        self.assertEqual(self.module.major, "34")

    def test_minor_property(self):
        self.assertEqual(self.module.minor, "11")

    def test_parent_module_property(self):
        self.assertEqual(self.module.parent_module, "Local")

    def test_parent_mod_port_id_property(self):
        self.assertEqual(self.module.parent_mod_port_id, "1")

    def test_inhibited_property(self):
        self.assertEqual(self.module.inhibited, "false")

    def test_major_fault_property(self):
        self.assertEqual(self.module.major_fault, "true")

    def test_ekey_property(self):
        self.assertEqual(self.module.ekey, {'@State': 'Disabled'})

    def test_ports_property(self):
        self.assertEqual(self.module.ports, [{'@Address': '0',
                                              '@Id': '1',
                                              '@SafetyNetwork': '16#0000_4c24_03e6_e7fc',
                                              '@Type': 'ICP',
                                              '@Upstream': 'false',
                                              'Bus': {'@Size': '4'}},
                                             {'@Id': '2',
                                              '@SafetyNetwork': '16#0000_4c24_03e6_e7fd',
                                              '@Type': 'Ethernet',
                                              '@Upstream': 'false',
                                              'Bus': None}])

    def test_communications_property(self):
        self.assertEqual(self.module.communications, None)

    def test_validate_method(self):
        report_item = self.module.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.module)


class TestProgram(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('MainProgram')

    def test_test_edits_property(self):
        self.assertEqual(self.program.test_edits, "false")

    def test_main_routine_name_property(self):
        self.assertEqual(self.program.main_routine_name, "main")

    def test_disabled_property(self):
        self.assertEqual(self.program.disabled, "false")

    def test_use_as_folder_property(self):
        self.assertEqual(self.program.use_as_folder, "false")

    def test_tags_property(self):
        self.assertIsInstance(self.program.raw_tags, list)
        self.assertIsInstance(self.program.tags, HashList)

    def test_routines_property(self):
        self.assertIsInstance(self.program.raw_routines, list)
        self.assertIsInstance(self.program.routines, HashList)

    def test_validate_method(self):
        program = Program()
        report_item = program.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertFalse(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, program)


class TestRoutine(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('MainProgram')
        self.routine = self.program.routines.get('main')

    def test_rungs_property(self):
        self.assertIsInstance(self.routine.raw_rungs, list)
        self.assertIsInstance(self.routine.rungs, list)


class TestRung(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('MainProgram')
        self.routine = self.program.routines.get('main')
        self.rung = self.routine.rungs[0]

    def test_number_property(self):
        self.assertEqual(self.rung.number, "0")

    def test_type_property(self):
        self.assertEqual(self.rung.type, "N")

    def test_comment_property(self):
        self.assertIsNotNone(self.rung.comment)

    def test_text_property(self):
        self.assertIsNotNone(self.rung.text)

    def test_instructions_property(self):
        self.assertIsInstance(self.rung.instructions, list)


class TestTag(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.tag = self.controller.tags.get('AlwaysOn')

    def test_initialization(self):
        self.assertEqual(self.tag.controller, self.controller)

    def test_tag_type_property(self):
        self.assertEqual(self.tag.tag_type, "Base")

    def test_datatype_property(self):
        self.assertEqual(self.tag.datatype, "BOOL")

    def test_constant_property(self):
        self.assertEqual(self.tag.constant, "false")

    def test_opc_ua_access_property(self):
        self.assertEqual(self.tag.opc_ua_access, None)

    def test_external_access_property(self):
        self.assertEqual(self.tag.external_access, "Read/Write")

    def test_data_property(self):
        self.assertIsInstance(self.tag.data, list)

    def test_validate_method(self):
        report_item = self.tag.validate()
        self.assertIsInstance(report_item, ControllerReportItem)
        self.assertTrue(report_item.pass_fail)
        self.assertEqual(report_item.plc_object, self.tag)


class TestController(unittest.TestCase):

    def setUp(self):
        self.controller: Controller = Controller.from_file(UNITTEST_PLC_FILE)

    def test_init(self):
        self.assertIsNotNone(self.controller._root_meta_data)
        self.assertEqual(self.controller._file_location, '')
        self.assertEqual(self.controller._slot, 0)
        self.assertIsNotNone(self.controller._config)

    def test_properties(self):

        self.assertEqual(self.controller.comm_path, 'AB_ETHIP-1\\120.15.35.60')
        self.assertEqual(self.controller.major_revision, 34)
        self.assertEqual(self.controller.minor_revision, 11)
        self.assertEqual(self.controller.name, 'unittest')
        self.assertEqual(self.controller.slot, 0)
        self.assertEqual(self.controller.plc_module['@Name'], 'Local')
        self.assertIsInstance(self.controller.raw_programs, list)
        self.assertIsInstance(self.controller.raw_tags, list)
        self.assertIsInstance(self.controller.raw_aois, list)
        self.assertIsInstance(self.controller.raw_datatypes, list)
        self.assertIsInstance(self.controller.raw_modules, list)
        self.assertIsInstance(self.controller.programs, HashList)
        self.assertIsInstance(self.controller.tags, HashList)
        self.assertIsInstance(self.controller.aois, HashList)
        self.assertIsInstance(self.controller.datatypes, HashList)
        self.assertIsInstance(self.controller.modules, HashList)

    def test_find_unpaired_controller_inputs(self):
        unpaired_inputs = self.controller.find_unpaired_controller_inputs()
        self.assertTrue(len(unpaired_inputs) != 0)

    def test_find_redundant_otes(self):
        redundant_otes = self.controller.find_redundant_otes()
        self.assertTrue(len(redundant_otes) != 0)

    def test_validate(self):
        report = self.controller.verify()

        self.assertIsInstance(report, dict)


class TestTextListElement(unittest.TestCase):

    def setUp(self):
        self.text = "Diagnostic text with number <kAlarm[123] This is an example alarm!>"
        self.rung = MagicMock(spec=GmRung)
        self.element = TextListElement(text=self.text, rung=self.rung)

    def test_init(self):
        self.assertEqual(self.element.text,
                         "<kAlarm[123] This is an example alarm!>")
        self.assertEqual(self.element.number, 123)
        self.assertIsInstance(self.element.rung, GmRung)

    def test_eq(self):
        other = TextListElement(text=self.text, rung=self.rung)
        self.assertEqual(self.element, other)

    def test_hash(self):
        self.assertEqual(hash(self.element), hash(
            (self.element.text, self.element.number)))

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
        self.kdiag = KDiag(diag_type=self.diag_type, text=self.text,
                           parent_offset=self.parent_offset, rung=self.rung)

    def test_init(self):
        self.assertEqual(
            self.kdiag.text, "<kAlarm[123] This is an example alarm!>")
        self.assertEqual(self.kdiag.number, 123)
        self.assertEqual(self.kdiag.diag_type, KDiagType.ALARM)
        self.assertEqual(self.kdiag.parent_offset, 10)
        self.assertIsInstance(self.kdiag.rung, GmRung)

    def test_eq(self):
        other = KDiag(diag_type=self.diag_type, text=self.text,
                      parent_offset=self.parent_offset, rung=self.rung)
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
        self.obj = GmPlcObject("za_Action")
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
        self.obj.text = "XIC(TestText) OTE(TestText)"
        self.obj.comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"

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
        self.program.routines.by_index(0).name = 'zSomeRoutine'
        self.assertTrue(self.program.is_gm_owned)

    def test_is_user_owned(self):
        self.program.routines.by_index(0).name = 'uSomeRoutine'
        self.assertTrue(self.program.is_user_owned)

    def test_diag_name(self):
        self.program.routines.by_index(0).name = 'B001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.assertEqual(self.program.diag_name, "IFD5075")

    def test_diag_setup(self):
        self.program.routines.by_index(0).name = 'B001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines.by_index(0).rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        diag_setup = self.program.diag_setup
        self.assertEqual(diag_setup['program_name'], self.program.name)
        self.assertEqual(diag_setup['diag_name'], "IFD5075")
        self.assertEqual(diag_setup['msg_offset'], 0)
        self.assertEqual(diag_setup['hmi_tag'], 'TBD')
        self.assertEqual(diag_setup['program_type'], KDiagProgramType.NA)
        self.assertEqual(diag_setup['tag_alias_refs'], 'TBD')

    def test_kdiags(self):
        self.program.routines.by_index(0).name = 'B001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines.by_index(0).rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        kdiags = self.program.kdiags
        self.assertEqual(len(kdiags), 1)
        self.assertIsInstance(kdiags[0], KDiag)

    def test_parameter_offset(self):
        self.assertEqual(self.program.parameter_offset, 0)

    def test_parameter_routine(self):
        self.program.routines.by_index(0).name = 'B001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.assertIsInstance(self.program.parameter_routine, GmRoutine)

    def test_program_type(self):
        self.assertEqual(self.program.program_type, KDiagProgramType.NA)

    def test_routines(self):
        self.assertEqual(len(self.program.routines), 1)
        self.assertIsInstance(self.program.routines.by_index(0), GmRoutine)

    def test_text_list_items(self):
        self.program.routines.by_index(0).name = 'B001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines.by_index(0).rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        text_list_items = self.program.text_list_items
        self.assertEqual(len(text_list_items), 1)
        self.assertIsInstance(text_list_items[0], TextListElement)

    def test_gm_routines(self):
        self.program.routines.by_index(0).name = 'zB001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines.by_index(0).rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        gm_routines = self.program.gm_routines
        self.assertEqual(len(gm_routines), 1)
        self.assertIsInstance(gm_routines[0], GmRoutine)

    def test_user_routines(self):
        self.program.routines.by_index(0).name = 'uB001_Parameters'
        self.program.routines.by_index(0).rungs[0].text = "MOV(12,HMI.Diag.Pgm.Name.LEN)[MOV(kAscii.I,HMI.Diag.Pgm.Name.DATA[0]),MOV(kAscii.F,HMI.Diag.Pgm.Name.DATA[1]),MOV(kAscii.D,HMI.Diag.Pgm.Name.DATA[2]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[3]),MOV(kAscii.n0,HMI.Diag.Pgm.Name.DATA[4]),MOV(kAscii.n7,HMI.Diag.Pgm.Name.DATA[5]),MOV(kAscii.n5,HMI.Diag.Pgm.Name.DATA[6])];"  # noqa: E501
        self.program.routines.by_index(0).rungs[0].comment = "<@DIAG> <Alarm[69]: This is a diagnostic comment!>"
        user_routines = self.program.user_routines
        self.assertEqual(len(user_routines), 1)
        self.assertIsInstance(user_routines[0], GmRoutine)


if __name__ == '__main__':
    unittest.main()
