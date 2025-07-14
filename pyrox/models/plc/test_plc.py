from __future__ import annotations


import unittest
from unittest.mock import MagicMock


from ..abc.list import HashList


from .plc import (
    AddOnInstruction,
    ConnectionCommand,
    ConnectionCommandType,
    ConnectionParameters,
    ContainsRoutines,
    ContainsTags,
    Controller,
    ControllerReportItem,
    ControllerModificationSchema,
    Datatype,
    DatatypeMember,
    LogixAssetType,
    LogixInstruction,
    LogixOperand,
    LogixTagScope,
    Module,
    NamedPlcObject,
    PlcObject,
    Program,
    Routine,
    Rung,
    Tag,
)

UNITTEST_PLC_FILE = r'docs\controls\unittest.L5X'


UNITTEST_PLC_FILE = r'docs\controls\unittest.L5X'


class TestPlcObject(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {"@Name": "TestObject", "Description": "Test Description"}
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

    def test_controller_property(self):
        self.assertEqual(self.plc_object.controller, self.controller)

    def test_meta_data_property(self):
        self.assertEqual(self.plc_object.meta_data, self.meta_data)
        new_meta = {"@Name": "Other", "Description": "Other Desc"}
        self.plc_object.meta_data = new_meta
        self.assertEqual(self.plc_object.meta_data, new_meta)
        self.plc_object.meta_data = "string_meta"
        self.assertEqual(self.plc_object.meta_data, "string_meta")
        with self.assertRaises(TypeError):
            self.plc_object.meta_data = 123

    def test_repr_and_str(self):
        self.assertEqual(repr(self.plc_object), str(self.plc_object.meta_data))
        self.assertEqual(str(self.plc_object), str(self.plc_object.meta_data))

    def test_dict_key_order_property(self):
        self.assertEqual(self.plc_object.dict_key_order, [])

    def test_on_compiled_property(self):
        self.assertIsInstance(self.plc_object.on_compiled, list)

    def test_compile_calls_on_compiled(self):
        called = []
        self.plc_object._compile_from_meta_data = lambda: self.assertTrue(True)
        self.plc_object._on_compiled.append(lambda: called.append(True))
        self.plc_object.compile()
        self.assertIn(True, called)

    def test_init_dict_order(self):
        class TestObject(PlcObject):
            @property
            def dict_key_order(self):
                return ["A", "B", "C"]
        obj = TestObject(meta_data={"A": 1, "B": 2}, controller=self.controller)
        obj._init_dict_order()
        self.assertIn("C", obj.meta_data)

    def test_validate(self):
        report = self.plc_object.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(report.pass_fail)
        self.assertIn('Validating PlcObject object', report.test_description)
        self.assertEqual(report.test_notes, [])

        # Test with missing config, controller, and meta_data
        obj = PlcObject()
        report = obj.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertFalse(report.pass_fail)

    def test_compile_from_meta_data_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.plc_object._compile_from_meta_data()


class TestNamedPlcObject(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
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
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('MainProgram')
        self.routine = self.program.routines.get('main')
        self.rung = self.routine.rungs[0]
        self.instruction = self.rung.instructions[0]
        self.operand = self.instruction.operands[0]

    def test_aliased_parents(self):
        aliased = self.operand.aliased_parents
        self.assertIsInstance(aliased, list)
        self.assertTrue(len(aliased) >= 1)
        self.assertTrue(all(isinstance(x, str) for x in aliased))

    def test_arg_position(self):
        self.assertIsInstance(self.operand.arg_position, int)
        self.assertGreaterEqual(self.operand.arg_position, 0)

    def test_as_aliased(self):
        aliased = self.operand.as_aliased
        self.assertIsInstance(aliased, str)
        self.assertTrue(len(aliased) > 0)

    def test_as_qualified(self):
        qualified = self.operand.as_qualified
        self.assertIsInstance(qualified, str)
        self.assertTrue(len(qualified) > 0)

    def test_base_name(self):
        base_name = self.operand.base_name
        self.assertIsInstance(base_name, str)
        self.assertTrue(len(base_name) > 0)

    def test_base_tag(self):
        base_tag = self.operand.base_tag
        # base_tag may be None if not found, but if present, should be a Tag
        if base_tag is not None:
            from .plc import Tag
            self.assertIsInstance(base_tag, Tag)

    def test_container(self):
        container = self.operand.container
        from .plc import ContainsRoutines
        self.assertIsInstance(container, ContainsRoutines)

    def test_instruction(self):
        self.assertIs(self.operand.instruction, self.instruction)

    def test_instruction_type(self):
        instr_type = self.operand.instruction_type
        from .plc import LogixInstructionType
        self.assertIn(instr_type, [LogixInstructionType.INPUT, LogixInstructionType.OUTPUT, LogixInstructionType.UNKOWN])

    def test_first_tag(self):
        first_tag = self.operand.first_tag
        # first_tag may be None if not found, but if present, should be a Tag
        if first_tag is not None:
            from .plc import Tag
            self.assertIsInstance(first_tag, Tag)

    def test_parents(self):
        parents = self.operand.parents
        self.assertIsInstance(parents, list)
        self.assertTrue(all(isinstance(x, str) for x in parents))

    def test_qualified_parents(self):
        qualified_parents = self.operand.qualified_parents
        self.assertIsInstance(qualified_parents, list)
        self.assertTrue(all(isinstance(x, str) for x in qualified_parents))

    def test_trailing_name(self):
        trailing = self.operand.trailing_name
        self.assertIsInstance(trailing, str)

    def test_as_report_dict(self):
        report = self.operand.as_report_dict()
        self.assertIsInstance(report, dict)
        self.assertIn('base operand', report)
        self.assertIn('aliased operand', report)
        self.assertIn('qualified operand', report)
        self.assertIn('arg_position', report)
        self.assertIn('instruction', report)
        self.assertIn('instruction_type', report)
        self.assertIn('program', report)
        self.assertIn('routine', report)
        self.assertIn('rung', report)

    def test_validate(self):
        report = self.operand.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(isinstance(report.pass_fail, bool))
        self.assertIsInstance(report.test_notes, list)


class TestLogixInstruction(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.program = self.controller.programs.get('MainProgram')
        self.routine = self.program.routines.get('main')
        self.rung = self.routine.rungs[0]
        self.instruction = self.rung.instructions[0]

    def test_aliased_meta_data(self):
        aliased = self.instruction.aliased_meta_data
        self.assertIsInstance(aliased, str)
        self.assertTrue(len(aliased) > 0)

    def test_container(self):
        container = self.instruction.container
        from .plc import Program, AddOnInstruction
        self.assertTrue(isinstance(container, Program) or isinstance(container, AddOnInstruction))

    def test_instruction_name(self):
        name = self.instruction.instruction_name
        self.assertIsInstance(name, str)
        self.assertTrue(len(name) > 0)

    def test_operands(self):
        operands = self.instruction.operands
        self.assertIsInstance(operands, list)
        self.assertTrue(all(isinstance(x, LogixOperand) for x in operands))

    def test_qualified_meta_data(self):
        qualified = self.instruction.qualified_meta_data
        self.assertIsInstance(qualified, str)
        self.assertTrue(len(qualified) > 0)

    def test_routine(self):
        routine = self.instruction.routine
        from .plc import Routine
        self.assertIsInstance(routine, Routine)

    def test_rung(self):
        rung = self.instruction.rung
        from .plc import Rung
        self.assertIsInstance(rung, Rung)

    def test_type(self):
        instr_type = self.instruction.type
        from .plc import LogixInstructionType
        self.assertIn(instr_type, [LogixInstructionType.INPUT, LogixInstructionType.OUTPUT])

    def test_as_report_dict(self):
        report = self.instruction.as_report_dict()
        self.assertIsInstance(report, dict)
        self.assertIn('instruction', report)
        self.assertIn('program', report)
        self.assertIn('routine', report)
        self.assertIn('rung', report)

    def test_validate(self):
        report = self.instruction.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(isinstance(report.pass_fail, bool))
        self.assertIsInstance(report.test_notes, list)


class TestContainsTags(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {"Tags": {"Tag": [{"@Name": "Tag1"}, {"@Name": "Tag2"}]}}
        self.obj = ContainsTags(meta_data=self.meta_data, controller=self.controller)

    def test_raw_tags_property(self):
        raw_tags = self.obj.raw_tags
        self.assertIsInstance(raw_tags, list)
        self.assertTrue(all(isinstance(tag, dict) for tag in raw_tags))

    def test_tags_property(self):
        tags = self.obj.tags
        from ..abc.list import HashList
        self.assertIsInstance(tags, HashList)
        self.assertTrue(all(hasattr(tag, 'name') for tag in tags))

    def test_add_tag(self):
        tag = Tag(meta_data={"@Name": "Tag3"}, controller=self.controller)
        self.obj.add_tag(tag)
        self.assertIn(tag.name, [t.name for t in self.obj.tags])

    def test_remove_tag(self):
        tag = Tag(meta_data={"@Name": "Tag1"}, controller=self.controller)
        self.obj.add_tag(tag)
        self.obj.remove_tag(tag)
        self.assertNotIn(tag.name, [t.name for t in self.obj.tags])

    def test_remove_tag_by_name(self):
        tag = Tag(meta_data={"@Name": "Tag2"}, controller=self.controller)
        self.obj.add_tag(tag)
        self.obj.remove_tag("Tag2")
        self.assertNotIn("Tag2", [t.name for t in self.obj.tags])

    def test_remove_tag_invalid_type(self):
        with self.assertRaises(TypeError):
            self.obj.remove_tag(123)

    def test_add_tag_invalid_type(self):
        with self.assertRaises(TypeError):
            self.obj.add_tag("not_a_tag")

    def test_remove_tag_not_found(self):
        tag = Tag(meta_data={"@Name": "NonExistent"}, controller=self.controller)
        with self.assertRaises(ValueError):
            self.obj.remove_tag(tag)


class TestContainsRoutines(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "Routines": {
                "Routine": [
                    {"@Name": "Routine1"},
                    {"@Name": "Routine2"}
                ]
            }
        }
        self.obj = ContainsRoutines(meta_data=self.meta_data, controller=self.controller)

    def test_routines_property(self):
        routines = self.obj.routines
        from ..abc.list import HashList
        self.assertIsInstance(routines, HashList)
        self.assertTrue(all(hasattr(routine, 'name') for routine in routines))

    def test_raw_routines_property(self):
        raw_routines = self.obj.raw_routines
        self.assertIsInstance(raw_routines, list)
        self.assertTrue(all(isinstance(routine, dict) for routine in raw_routines))

    def test_add_routine(self):
        routine = Routine(meta_data={"@Name": "Routine3"}, controller=self.controller, program=self.obj)
        self.obj.add_routine(routine)
        self.assertIn(routine.name, [r.name for r in self.obj.routines])

    def test_remove_routine(self):
        routine = Routine(meta_data={"@Name": "Routine1"}, controller=self.controller, program=self.obj)
        self.obj.add_routine(routine)
        self.obj.remove_routine(routine)
        self.assertNotIn(routine.name, [r.name for r in self.obj.routines])

    def test_remove_routine_invalid_type(self):
        with self.assertRaises(TypeError):
            self.obj.remove_routine("not_a_routine")

    def test_remove_routine_not_found(self):
        routine = Routine(meta_data={"@Name": "NonExistent"}, controller=self.controller, program=self.obj)
        with self.assertRaises(ValueError):
            self.obj.remove_routine(routine)

    def test_add_routine_invalid_type(self):
        with self.assertRaises(TypeError):
            self.obj.add_routine("not_a_routine")

    def test_instructions_property(self):
        instructions = self.obj.instructions
        self.assertIsInstance(instructions, list)

    def test_input_instructions_property(self):
        input_instructions = self.obj.input_instructions
        self.assertIsInstance(input_instructions, list)

    def test_output_instructions_property(self):
        output_instructions = self.obj.output_instructions
        self.assertIsInstance(output_instructions, list)


class TestAddOnInstruction(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Name": "AOI_Test",
            "@Revision": "1.0",
            "@ExecutePrescan": "true",
            "@ExecutePostscan": "false",
            "@ExecuteEnableInFalse": "true",
            "@CreatedDate": "2025-07-14",
            "@CreatedBy": "UnitTest",
            "@EditedDate": "2025-07-14",
            "@EditedBy": "UnitTest",
            "@SoftwareRevision": "33.11",
            "@RevisionExtension": "ext",
            "Description": "Test AOI",
            "RevisionNote": "Initial",
            "Parameters": {"Parameter": []},
            "LocalTags": {"LocalTag": []},
            "Routines": {"Routine": []}
        }
        self.aoi = AddOnInstruction(meta_data=self.meta_data, controller=self.controller)

    def test_dict_key_order(self):
        keys = self.aoi.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Name', keys)
        self.assertIn('Routines', keys)

    def test_revision_property(self):
        self.assertEqual(self.aoi.revision, "1.0")
        self.aoi.revision = "2.0"
        self.assertEqual(self.aoi.revision, "2.0")
        with self.assertRaises(self.aoi.InvalidNamingException):
            self.aoi.revision = "invalid revision!"

    def test_execute_prescan_property(self):
        self.assertEqual(self.aoi.execute_prescan, "true")
        self.aoi.execute_prescan = False
        self.assertEqual(self.aoi.execute_prescan, "false")
        with self.assertRaises(self.aoi.InvalidNamingException):
            self.aoi.execute_prescan = "not_bool"

    def test_execute_postscan_property(self):
        self.assertEqual(self.aoi.execute_postscan, "false")
        self.aoi.execute_postscan = True
        self.assertEqual(self.aoi.execute_postscan, "true")
        with self.assertRaises(self.aoi.InvalidNamingException):
            self.aoi.execute_postscan = "not_bool"

    def test_execute_enable_in_false_property(self):
        self.assertEqual(self.aoi.execute_enable_in_false, "true")
        self.aoi.execute_enable_in_false = False
        self.assertEqual(self.aoi.execute_enable_in_false, "false")
        with self.assertRaises(self.aoi.InvalidNamingException):
            self.aoi.execute_enable_in_false = "not_bool"

    def test_created_and_edited_properties(self):
        self.assertEqual(self.aoi.created_date, "2025-07-14")
        self.assertEqual(self.aoi.created_by, "UnitTest")
        self.assertEqual(self.aoi.edited_date, "2025-07-14")
        self.assertEqual(self.aoi.edited_by, "UnitTest")

    def test_software_revision_property(self):
        self.assertEqual(self.aoi.software_revision, "33.11")
        self.aoi.software_revision = "34.0"
        self.assertEqual(self.aoi.software_revision, "34.0")
        with self.assertRaises(self.aoi.InvalidNamingException):
            self.aoi.software_revision = "abc"

    def test_revision_extension_property(self):
        self.assertEqual(self.aoi.revision_extension, "ext")
        self.aoi.revision_extension = "<invalid>"
        self.assertEqual(self.aoi.revision_extension, "&lt;invalid>")

    def test_revision_note_property(self):
        self.assertEqual(self.aoi.revision_note, "Initial")
        self.aoi.revision_note = "Updated"
        self.assertEqual(self.aoi.revision_note, "Updated")
        with self.assertRaises(ValueError):
            self.aoi.revision_note = 123

    def test_parameters_property(self):
        self.assertIsInstance(self.aoi.parameters, list)

    def test_local_tags_property(self):
        self.assertIsInstance(self.aoi.local_tags, list)

    def test_raw_tags_property(self):
        self.assertIsInstance(self.aoi.raw_tags, list)

    def test_validate(self):
        report = self.aoi.validate()
        self.assertIsInstance(report, ControllerReportItem)


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


class TestConnectionCommand(unittest.TestCase):
    def setUp(self):
        def dummy_cb(response): return response
        self.cmd = ConnectionCommand(
            type=ConnectionCommandType.READ,
            tag_name="TestTag",
            tag_value=123,
            data_type=1,
            response_cb=dummy_cb
        )

    def test_type_property(self):
        self.assertEqual(self.cmd.type, ConnectionCommandType.READ)

    def test_tag_name_property(self):
        self.assertEqual(self.cmd.tag_name, "TestTag")

    def test_tag_value_property(self):
        self.assertEqual(self.cmd.tag_value, 123)

    def test_data_type_property(self):
        self.assertEqual(self.cmd.data_type, 1)

    def test_response_cb_property(self):
        self.assertTrue(callable(self.cmd.response_cb))
        self.assertEqual(self.cmd.response_cb("ok"), "ok")


class TestDatatypeMember(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.parent_datatype = Datatype(meta_data={"@Name": "TestType"}, controller=self.controller)
        self.meta_data = {
            "@Name": "Member1",
            "@DataType": "BOOL",
            "@Dimension": "1",
            "@Hidden": "false"
        }
        self.member = DatatypeMember(
            l5x_meta_data=self.meta_data,
            parent_datatype=self.parent_datatype,
            controller=self.controller
        )

    def test_datatype_property(self):
        self.assertEqual(self.member.datatype, "BOOL")

    def test_dimension_property(self):
        self.assertEqual(self.member.dimension, "1")

    def test_hidden_property(self):
        self.assertEqual(self.member.hidden, "false")

    def test_is_atomic_property(self):
        self.assertTrue(self.member.is_atomic)

    def test_parent_datatype_property(self):
        self.assertIs(self.member.parent_datatype, self.parent_datatype)


class TestDatatype(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Name": "MyDatatype",
            "@Family": "User",
            "@Class": "Structure",
            "Description": "Test datatype",
            "Members": {
                "Member": [
                    {"@Name": "AtomicMember", "@DataType": "BOOL", "@Dimension": "1", "@Hidden": "false"},
                    {"@Name": "OtherMember", "@DataType": "INT", "@Dimension": "1", "@Hidden": "false"}
                ]
            }
        }
        self.datatype = Datatype(meta_data=self.meta_data, controller=self.controller)

    def test_dict_key_order(self):
        keys = self.datatype.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Name', keys)
        self.assertIn('Members', keys)

    def test_family_property(self):
        self.assertEqual(self.datatype.family, "User")

    def test_is_atomic_property(self):
        # Should be False for custom datatype
        self.assertFalse(self.datatype.is_atomic)
        # Should be True for atomic datatype
        atomic = Datatype(meta_data={"@Name": "BOOL"}, controller=self.controller)
        self.assertTrue(atomic.is_atomic)

    def test_members_property(self):
        members = self.datatype.members
        self.assertIsInstance(members, list)
        self.assertTrue(all(isinstance(m, DatatypeMember) for m in members))

    def test_raw_members_property(self):
        raw_members = self.datatype.raw_members
        self.assertIsInstance(raw_members, list)
        self.assertTrue(all(isinstance(m, dict) for m in raw_members))

    def test_endpoint_operands(self):
        endpoints = self.datatype.endpoint_operands
        self.assertIsInstance(endpoints, list)
        self.assertTrue(all(isinstance(e, str) for e in endpoints))

    def test_validate(self):
        report = self.datatype.validate()
        self.assertIsInstance(report, ControllerReportItem)


class TestModule(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Name": "Local",
            "@CatalogNumber": "1756-L83E",
            "@Vendor": "1",
            "@ProductType": "14",
            "@ProductCode": "83",
            "@Major": "33",
            "@Minor": "11",
            "@ParentModule": "",
            "@ParentModPortId": "",
            "@Inhibited": "false",
            "@MajorFault": "false",
            "Description": "Test module",
            "EKey": {},
            "Ports": {"Port": []},
            "Communications": {"Connections": {"Connection": [{"@InputCxnPoint": "input", "@OutputCxnPoint": "output"}]}, "@PrimCxnInputSize": "128", "@PrimCxnOutputSize": "128"}  # noqa: E501
        }
        self.module = Module(l5x_meta_data=self.meta_data, controller=self.controller)

    def test_dict_key_order(self):
        keys = self.module.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Name', keys)
        self.assertIn('Communications', keys)

    def test_catalog_number_property(self):
        self.assertEqual(self.module.catalog_number, "1756-L83E")
        self.module.catalog_number = "1756-L85E"
        self.assertEqual(self.module.catalog_number, "1756-L85E")

    def test_vendor_property(self):
        self.assertEqual(self.module.vendor, "1")
        self.module.vendor = "2"
        self.assertEqual(self.module.vendor, "2")
        with self.assertRaises(ValueError):
            self.module.vendor = "not_an_int"

    def test_product_type_property(self):
        self.assertEqual(self.module.product_type, "14")
        self.module.product_type = "15"
        self.assertEqual(self.module.product_type, "15")
        with self.assertRaises(ValueError):
            self.module.product_type = "not_an_int"

    def test_product_code_property(self):
        self.assertEqual(self.module.product_code, "83")
        self.module.product_code = "84"
        self.assertEqual(self.module.product_code, "84")
        with self.assertRaises(ValueError):
            self.module.product_code = "not_an_int"

    def test_major_property(self):
        self.assertEqual(self.module.major, "33")
        self.module.major = "34"
        self.assertEqual(self.module.major, "34")
        with self.assertRaises(ValueError):
            self.module.major = "not_an_int"

    def test_minor_property(self):
        self.assertEqual(self.module.minor, "11")
        self.module.minor = "12"
        self.assertEqual(self.module.minor, "12")
        with self.assertRaises(ValueError):
            self.module.minor = "not_an_int"

    def test_inhibited_property(self):
        self.assertEqual(self.module.inhibited, "false")
        self.module.inhibited = True
        self.assertEqual(self.module.inhibited, "true")
        with self.assertRaises(self.module.InvalidNamingException):
            self.module.inhibited = "not_bool"

    def test_major_fault_property(self):
        self.assertEqual(self.module.major_fault, "false")
        self.module.major_fault = True
        self.assertEqual(self.module.major_fault, "true")
        with self.assertRaises(self.module.InvalidNamingException):
            self.module.major_fault = "not_bool"

    def test_ports_property(self):
        self.assertIsInstance(self.module.ports, list)

    def test_communications_property(self):
        self.assertIsInstance(self.module.communications, dict)

    def test_connections_property(self):
        self.assertIsInstance(self.module.connections, list)

    def test_input_connection_point_property(self):
        self.assertEqual(self.module.input_connection_point, "input")

    def test_output_connection_point_property(self):
        self.assertEqual(self.module.output_connection_point, "output")

    def test_input_connection_size_property(self):
        self.assertEqual(self.module.input_connection_size, "128")

    def test_output_connection_size_property(self):
        self.assertEqual(self.module.output_connection_size, "128")

    def test_type_property(self):
        self.assertIn(self.module.type_, ["Unknown", "IntrospectiveModule"])

    def test_validate(self):
        report = self.module.validate()
        self.assertIsInstance(report, ControllerReportItem)


class TestProgram(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Name": "TestProgram",
            "@TestEdits": "false",
            "@MainRoutineName": "MainRoutine",
            "@Disabled": "false",
            "@Class": "Standard",
            "@UseAsFolder": "false",
            "Description": "Test program",
            "Tags": {"Tag": []},
            "Routines": {"Routine": [{"@Name": "MainRoutine"}]}
        }
        self.program = Program(meta_data=self.meta_data, controller=self.controller)

    def test_dict_key_order(self):
        keys = self.program.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Name', keys)
        self.assertIn('Routines', keys)

    def test_disabled_property(self):
        self.assertEqual(self.program.disabled, "false")

    def test_main_routine_name_property(self):
        self.assertEqual(self.program.main_routine_name, "MainRoutine")

    def test_main_routine_property(self):
        routine = self.program.main_routine
        # Should be None if not found, or a Routine instance
        from ..plc import Routine
        self.assertTrue(routine is None or isinstance(routine, Routine))

    def test_test_edits_property(self):
        self.assertEqual(self.program.test_edits, "false")

    def test_use_as_folder_property(self):
        self.assertEqual(self.program.use_as_folder, "false")

    def test_validate(self):
        report = self.program.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(isinstance(report.pass_fail, bool))
        self.assertIsInstance(report.test_notes, list)


class TestRoutine(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Name": "Routine1",
            "@Type": "RLL",
            "Description": "Test routine",
            "RLLContent": {"Rung": [{"@Number": "0", "@Type": "RLL", "Comment": "Test rung", "Text": "XIC(Tag1) OTE(Tag2)"}]}
        }
        self.program = Program(meta_data={"@Name": "TestProgram"}, controller=self.controller)
        self.routine = Routine(meta_data=self.meta_data, controller=self.controller, program=self.program)

    def test_dict_key_order(self):
        keys = self.routine.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Name', keys)
        self.assertIn('RLLContent', keys)

    def test_program_property(self):
        self.assertIs(self.routine.program, self.program)

    def test_rungs_property(self):
        rungs = self.routine.rungs
        self.assertIsInstance(rungs, list)
        self.assertTrue(all(isinstance(r, Rung) for r in rungs))

    def test_raw_rungs_property(self):
        raw_rungs = self.routine.raw_rungs
        self.assertIsInstance(raw_rungs, list)
        self.assertTrue(all(isinstance(r, dict) for r in raw_rungs))

    def test_instructions_property(self):
        instructions = self.routine.instructions
        self.assertIsInstance(instructions, list)
        self.assertTrue(all(isinstance(i, LogixInstruction) for i in instructions))

    def test_input_instructions_property(self):
        input_instructions = self.routine.input_instructions
        self.assertIsInstance(input_instructions, list)

    def test_output_instructions_property(self):
        output_instructions = self.routine.output_instructions
        self.assertIsInstance(output_instructions, list)

    def test_add_rung(self):
        rung = Rung(meta_data={"@Number": "1", "@Type": "RLL", "Comment": "Added rung",
                    "Text": "XIC(Tag3) OTE(Tag4)"}, controller=self.controller, routine=self.routine)
        self.routine.add_rung(rung)
        self.assertIn(rung, self.routine.rungs)

    def test_remove_rung(self):
        rung = self.routine.rungs[0]
        self.routine.remove_rung(rung)
        self.assertNotIn(rung, self.routine.rungs)

    def test_clear_rungs(self):
        self.routine.clear_rungs()
        self.assertEqual(len(self.routine.rungs), 0)

    def test_validate(self):
        report = self.routine.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(isinstance(report.pass_fail, bool))
        self.assertIsInstance(report.test_notes, list)


class TestRung(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Number": "0",
            "@Type": "RLL",
            "Comment": "Test rung",
            "Text": "XIC(Tag1) OTE(Tag2)"
        }
        self.routine = Routine(meta_data={"@Name": "Routine1"}, controller=self.controller)
        self.rung = Rung(meta_data=self.meta_data, controller=self.controller, routine=self.routine)

    def test_dict_key_order(self):
        keys = self.rung.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Number', keys)
        self.assertIn('Text', keys)

    def test_comment_property(self):
        self.assertEqual(self.rung.comment, "Test rung")
        self.rung.comment = "Updated comment"
        self.assertEqual(self.rung.comment, "Updated comment")

    def test_number_property(self):
        self.assertEqual(self.rung.number, "0")
        self.rung.number = 5
        self.assertEqual(self.rung.number, "5")
        with self.assertRaises(ValueError):
            self.rung.number = None

    def test_routine_property(self):
        self.assertIs(self.rung.routine, self.routine)
        new_routine = Routine(meta_data={"@Name": "Routine2"}, controller=self.controller)
        self.rung.routine = new_routine
        self.assertIs(self.rung.routine, new_routine)

    def test_text_property(self):
        self.assertEqual(self.rung.text, "XIC(Tag1) OTE(Tag2)")
        self.rung.text = "XIC(Tag3) OTE(Tag4)"
        self.assertEqual(self.rung.text, "XIC(Tag3) OTE(Tag4)")

    def test_type_property(self):
        self.assertEqual(self.rung.type, "RLL")

    def test_instructions_property(self):
        instructions = self.rung.instructions
        self.assertIsInstance(instructions, list)
        self.assertTrue(all(isinstance(i, LogixInstruction) for i in instructions))

    def test_input_instructions_property(self):
        input_instructions = self.rung.input_instructions
        self.assertIsInstance(input_instructions, list)

    def test_output_instructions_property(self):
        output_instructions = self.rung.output_instructions
        self.assertIsInstance(output_instructions, list)

    def test_eq_and_repr(self):
        rung2 = Rung(meta_data=self.meta_data, controller=self.controller, routine=self.routine)
        self.assertTrue(self.rung == rung2)
        self.assertIsInstance(repr(self.rung), str)
        self.assertIsInstance(str(self.rung), str)

    def test_validate(self):
        report = self.rung.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(isinstance(report.pass_fail, bool))
        self.assertIsInstance(report.test_notes, list)


class TestTag(unittest.TestCase):
    def setUp(self):
        self.controller = Controller.from_file(UNITTEST_PLC_FILE)
        self.meta_data = {
            "@Name": "TestTag",
            "@Class": "Standard",
            "@TagType": "Base",
            "@DataType": "BOOL",
            "@Dimensions": "1",
            "@Radix": "Decimal",
            "@AliasFor": "",
            "@Constant": "false",
            "@ExternalAccess": "Read/Write",
            "Description": "Test tag",
            "Data": []
        }
        self.tag = Tag(meta_data=self.meta_data, controller=self.controller)

    def test_dict_key_order(self):
        keys = self.tag.dict_key_order
        self.assertIsInstance(keys, list)
        self.assertIn('@Name', keys)
        self.assertIn('Data', keys)

    def test_class_property(self):
        self.assertEqual(self.tag.class_, "Standard")
        self.tag.class_ = "Safety"
        self.assertEqual(self.tag.class_, "Safety")
        with self.assertRaises(ValueError):
            self.tag.class_ = "InvalidClass"

    def test_tag_type_property(self):
        self.assertEqual(self.tag.tag_type, "Base")
        self.tag.tag_type = "Structure"
        self.assertEqual(self.tag.tag_type, "Structure")
        with self.assertRaises(ValueError):
            self.tag.tag_type = "InvalidType"

    def test_datatype_property(self):
        self.assertEqual(self.tag.datatype, "BOOL")
        self.tag.datatype = "INT"
        self.assertEqual(self.tag.datatype, "INT")
        with self.assertRaises(ValueError):
            self.tag.datatype = ""

    def test_dimensions_property(self):
        self.assertEqual(self.tag.dimensions, "1")
        self.tag.dimensions = 2
        self.assertEqual(self.tag.dimensions, "2")
        with self.assertRaises(ValueError):
            self.tag.dimensions = -1

    def test_constant_property(self):
        self.assertEqual(self.tag.constant, "false")
        self.tag.constant = True
        self.assertEqual(self.tag.constant, "true")
        with self.assertRaises(self.tag.InvalidNamingException):
            self.tag.constant = "not_bool"

    def test_external_access_property(self):
        self.assertEqual(self.tag.external_access, "Read/Write")
        self.tag.external_access = "ReadOnly"
        self.assertEqual(self.tag.external_access, "ReadOnly")
        with self.assertRaises(ValueError):
            self.tag.external_access = "InvalidAccess"

    def test_alias_for_property(self):
        self.assertEqual(self.tag.alias_for, "")

    def test_alias_for_base_name_property(self):
        self.assertIsInstance(self.tag.alias_for_base_name, (str, type(None)))

    def test_endpoint_operands_property(self):
        endpoints = self.tag.endpoint_operands
        self.assertIsInstance(endpoints, list)

    def test_data_property(self):
        self.assertIsInstance(self.tag.data, list)

    def test_decorated_data_property(self):
        decorated = self.tag.decorated_data
        self.assertTrue(decorated is None or isinstance(decorated, dict))

    def test_l5k_data_property(self):
        l5k = self.tag.l5k_data
        self.assertTrue(l5k is None or isinstance(l5k, dict))

    def test_scope_property(self):
        scope = self.tag.scope
        self.assertIn(scope, [LogixTagScope.CONTROLLER, LogixTagScope.PROGRAM])

    def test_validate(self):
        report = self.tag.validate()
        self.assertIsInstance(report, ControllerReportItem)


class TestController(unittest.TestCase):
    def setUp(self):
        self.meta_data = {
            "RSLogix5000Content": {
                "Controller": {
                    "@Name": "TestController",
                    "@MajorRev": "33",
                    "@MinorRev": "11",
                    "Description": "Test controller",
                    "AddOnInstructionDefinitions": {"AddOnInstructionDefinition": []},
                    "DataTypes": {"DataType": []},
                    "Modules": {"Module": [{"@Name": "Local"}]},
                    "Programs": {"Program": []},
                    "Tags": {"Tag": []}
                }
            }
        }
        self.controller = Controller(meta_data=self.meta_data)

    def test_name_and_description(self):
        self.assertEqual(self.controller.name, "TestController")
        self.assertEqual(self.controller.description, "Test controller")

    def test_dict_key_order(self):
        # Controller does not override dict_key_order, but NamedPlcObject does
        self.assertTrue(isinstance(self.controller.dict_key_order, list))

    def test_major_minor_revision(self):
        self.assertEqual(self.controller.major_revision, 33)
        self.assertEqual(self.controller.minor_revision, 11)
        self.controller.major_revision = 34
        self.controller.minor_revision = 12
        self.assertEqual(self.controller.major_revision, 34)
        self.assertEqual(self.controller.minor_revision, 12)

    def test_aois_property(self):
        self.assertIsInstance(self.controller.aois, HashList)

    def test_datatypes_property(self):
        self.assertIsInstance(self.controller.datatypes, HashList)

    def test_modules_property(self):
        self.assertIsInstance(self.controller.modules, HashList)

    def test_programs_property(self):
        self.assertIsInstance(self.controller.programs, HashList)

    def test_tags_property(self):
        self.assertIsInstance(self.controller.tags, HashList)

    def test_raw_aois_property(self):
        self.assertIsInstance(self.controller.raw_aois, list)

    def test_raw_datatypes_property(self):
        self.assertIsInstance(self.controller.raw_datatypes, list)

    def test_raw_modules_property(self):
        self.assertIsInstance(self.controller.raw_modules, list)

    def test_raw_programs_property(self):
        self.assertIsInstance(self.controller.raw_programs, list)

    def test_raw_tags_property(self):
        self.assertIsInstance(self.controller.raw_tags, list)

    def test_compile_and_validate(self):
        self.controller.compile()
        report = self.controller.validate()
        self.assertIsInstance(report, ControllerReportItem)
        self.assertTrue(isinstance(report.pass_fail, bool))
        self.assertIsInstance(report.test_notes, list)

    def test_add_and_remove_assets(self):
        # Add and remove AOI
        aoi = AddOnInstruction(meta_data={"@Name": "AOI1"}, controller=self.controller)
        self.controller.add_aoi(aoi)
        self.assertIn(aoi, self.controller.aois)
        self.controller.remove_aoi(aoi)
        self.assertNotIn(aoi, self.controller.aois)

        # Add and remove Datatype
        dt = Datatype(meta_data={"@Name": "DT1"}, controller=self.controller)
        self.controller.add_datatype(dt)
        self.assertIn(dt, self.controller.datatypes)
        self.controller.remove_datatype(dt)
        self.assertNotIn(dt, self.controller.datatypes)

        # Add and remove Module
        mod = Module(l5x_meta_data={"@Name": "MOD1"}, controller=self.controller)
        self.controller.add_module(mod)
        self.assertIn(mod, self.controller.modules)
        self.controller.remove_module(mod)
        self.assertNotIn(mod, self.controller.modules)

        # Add and remove Program
        prog = Program(meta_data={"@Name": "PROG1"}, controller=self.controller)
        self.controller.add_program(prog)
        self.assertIn(prog, self.controller.programs)
        self.controller.remove_program(prog)
        self.assertNotIn(prog, self.controller.programs)

        # Add and remove Tag
        tag = Tag(meta_data={"@Name": "TAG1"}, controller=self.controller)
        self.controller.add_tag(tag)
        self.assertIn(tag, self.controller.tags)
        self.controller.remove_tag(tag)
        self.assertNotIn(tag, self.controller.tags)

    def test_find_diagnostic_rungs(self):
        result = self.controller.find_diagnostic_rungs()
        self.assertIsInstance(result, list)

    def test_find_unpaired_controller_inputs(self):
        result = self.controller.find_unpaired_controller_inputs()
        self.assertIsInstance(result, dict)

    def test_find_redundant_otes(self):
        result = self.controller.find_redundant_otes()
        self.assertIsInstance(result, dict)

    def test_rename_asset(self):
        # Should not raise
        self.controller.rename_asset(LogixAssetType.TAG, "TAG1", "TAG2")
        self.controller.rename_asset(LogixAssetType.ALL, "TAG1", "TAG2")

    def test_verify(self):
        result = self.controller.verify()
        self.assertIsInstance(result, dict)
        self.assertIn('ControllerReport', result)
        self.assertIn('UnpairedControllerInputs', result)
        self.assertIn('RedundantOutputs', result)

    def test_from_file_and_from_meta_data(self):
        # from_meta_data should return a Controller instance
        ctrl = Controller.from_meta_data(self.meta_data)
        self.assertIsInstance(ctrl, Controller)


class TestControllerModificationSchema(unittest.TestCase):
    def setUp(self):
        self.controller_src = Controller(meta_data={
            "RSLogix5000Content": {
                "Controller": {
                    "@Name": "SourceController",
                    "DataTypes": {"DataType": [{"@Name": "DT1"}]},
                    "Tags": {"Tag": [{"@Name": "TAG1"}]},
                    "Programs": {"Program": [{"@Name": "PROG1", "Routines": {"Routine": [{"@Name": "ROUT1"}]}}]}
                }
            }
        })
        self.controller_dst = Controller(meta_data={
            "RSLogix5000Content": {
                "Controller": {
                    "@Name": "DestController",
                    "DataTypes": {"DataType": []},
                    "Tags": {"Tag": []},
                    "Programs": {"Program": [{"@Name": "PROG1", "Routines": {"Routine": [{"@Name": "ROUT1"}]}}]}
                }
            }
        })
        self.schema = ControllerModificationSchema(self.controller_src, self.controller_dst)

    def test_add_datatype_migration(self):
        self.schema.add_datatype_migration("DT1")
        self.assertEqual(self.schema.actions[-1]['type'], 'datatype')
        self.assertEqual(self.schema.actions[-1]['name'], 'DT1')

    def test_add_tag_import(self):
        tag = Tag(meta_data={"@Name": "TAG2"}, controller=self.controller_dst)
        self.schema.add_tag_import(tag)
        self.assertEqual(self.schema.actions[-1]['type'], 'import_tag')
        self.assertEqual(self.schema.actions[-1]['asset'], tag.meta_data)

    def test_add_tag_migration(self):
        self.schema.add_tag_migration("TAG1")
        self.assertEqual(self.schema.actions[-1]['type'], 'tag')
        self.assertEqual(self.schema.actions[-1]['name'], 'TAG1')

    def test_add_program_tag_import(self):
        tag = Tag(meta_data={"@Name": "TAG3"}, controller=self.controller_dst)
        self.schema.add_program_tag_import("PROG1", tag)
        self.assertEqual(self.schema.actions[-1]['type'], 'import_program_tag')
        self.assertEqual(self.schema.actions[-1]['program'], "PROG1")
        self.assertEqual(self.schema.actions[-1]['asset'], tag.meta_data)

    def test_add_routine_import(self):
        routine = Routine(meta_data={"@Name": "ROUT2"}, controller=self.controller_dst)
        self.schema.add_routine_import("PROG1", routine)
        self.assertEqual(self.schema.actions[-1]['type'], 'import_routine')
        self.assertEqual(self.schema.actions[-1]['program'], "PROG1")
        self.assertEqual(self.schema.actions[-1]['routine'], routine.meta_data)

    def test_add_rung_import(self):
        rung = Rung(meta_data={"@Number": "0", "Text": "XIC(Tag1)"}, controller=self.controller_dst)
        self.schema.add_rung_import("PROG1", "ROUT1", 0, rung)
        self.assertEqual(self.schema.actions[-1]['type'], 'rung_import')
        self.assertEqual(self.schema.actions[-1]['program'], "PROG1")
        self.assertEqual(self.schema.actions[-1]['routine'], "ROUT1")
        self.assertEqual(self.schema.actions[-1]['rung_number'], 0)
        self.assertEqual(self.schema.actions[-1]['new_rung'], rung.meta_data)

    def test_add_routine_migration(self):
        self.schema.add_routine_migration("PROG1", "ROUT1", {"0": {"@Number": "0", "Text": "XIC(Tag2)"}})
        self.assertEqual(self.schema.actions[-1]['type'], 'routine')
        self.assertEqual(self.schema.actions[-1]['program'], "PROG1")
        self.assertEqual(self.schema.actions[-1]['routine'], "ROUT1")
        self.assertIsInstance(self.schema.actions[-1]['rung_updates'], dict)

    def test_add_import_from_l5x_dict(self):
        l5x_dict = {
            "RSLogix5000Content": {
                "Controller": {
                    "DataTypes": {"DataType": [{"@Name": "DTX"}]},
                    "Tags": {"Tag": [{"@Name": "TAGX"}]},
                    "Programs": {"Program": [{"@Name": "PROGX"}]}
                }
            }
        }
        self.schema.add_import_from_l5x_dict(l5x_dict)
        types = [a['type'] for a in self.schema.actions[-3:]]
        self.assertIn('import_datatypes', types)
        self.assertIn('import_tags', types)
        self.assertIn('import_programs', types)

    def test_execute(self):
        # Should not raise
        self.schema.add_datatype_migration("DT1")
        self.schema.add_tag_migration("TAG1")
        self.schema.add_routine_migration("PROG1", "ROUT1")
        self.schema.execute()
        # Check that destination controller has the migrated assets
        self.assertIsNotNone(self.controller_dst.datatypes.get("DT1"))
        self.assertIsNotNone(self.controller_dst.tags.get("TAG1"))


if __name__ == '__main__':
    unittest.main()
