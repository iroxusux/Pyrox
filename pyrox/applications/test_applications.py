"""types test suite
    """
from __future__ import annotations
from unittest.mock import MagicMock

from .general_motors.gm import (
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


import unittest


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
        self.obj = GmPlcObject(meta_data="za_Action")
        self.obj._controller = None

    def test_config(self):
        config = self.obj.config
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
