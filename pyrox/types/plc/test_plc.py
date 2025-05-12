"""testing module for plc types
    """
from __future__ import annotations


from fnmatch import fnmatch


from .plc import (
    PlcObject,
    Controller,
    ControllerConfiguration,
    ControllerReport,
    Datatype,
    DatatypeMember,
    Tag,
    AddOnInstruction,
    Module,
    Program,
    Routine,
    SupportsClass,
    SupportsExternalAccess,
)

from .gm import (
    GmController,
    GmProgram,
    GmRoutine,
    GmRung,
    KDiag,
    KDiagType,
)


from ..abc.meta import LoggableUnitTest


TESTING_FILE = r'docs\controls\_test.L5X'
TESTING_GM_FILE = r'docs\controls\_test_gm.L5X'
TESTING_GM_DUP_ALARMS_FILE = r'docs\controls\_test_gm_dup_alarms.L5X'
TESTING_DATA = {
    '@Name': 'Test Object',
    'Description': 'Test Description'
}


class TestPLC(LoggableUnitTest):
    """testing class for emulation preparation
    """

    def test_controller(self):
        """test controller type
        """
        # test ctrl raises bad file extension
        with self.assertRaises(ValueError) as context:
            ctrl = Controller.from_file('abc.bad.file.extension')
        self.assertTrue(isinstance(context.exception, ValueError))

        # test ctrl raises bad file location
        with self.assertRaises(FileNotFoundError) as context:
            ctrl = Controller.from_file('abc.bad.file.L5X')
        self.assertTrue(isinstance(context.exception, FileNotFoundError))

        # test ctrl loads from good file
        ctrl: Controller = Controller.from_file(TESTING_FILE)
        self.assertIsNotNone(ctrl)
        self.assertIsInstance(ctrl.root_meta_data, dict)

        # test controller aois are compiled as expected
        self.assertIsInstance(ctrl.aois, list)
        self.assertIsInstance(ctrl.aois[0], AddOnInstruction)
        self.assertIsInstance(ctrl.raw_aois, list)
        self.assertIsInstance(ctrl.raw_aois[0], dict)

        # test controller datatypes are compiled as expected
        self.assertIsInstance(ctrl.datatypes, list)
        self.assertIsInstance(ctrl.datatypes[0], Datatype)
        self.assertIsInstance(ctrl.raw_datatypes, list)
        self.assertIsInstance(ctrl.raw_datatypes[0], dict)

        # test controller tags are compiled as expected
        self.assertIsInstance(ctrl.tags, list)
        self.assertIsInstance(ctrl.tags[0], Tag)
        self.assertIsInstance(ctrl.raw_tags, list)
        self.assertIsInstance(ctrl.raw_tags[0], dict)

        # test controller modules are compiled as expected
        self.assertIsInstance(ctrl.modules, list)
        self.assertIsInstance(ctrl.modules[0], Module)
        self.assertIsInstance(ctrl.raw_modules, list)
        self.assertIsInstance(ctrl.raw_modules[0], dict)

        # test controller programs are compiled as expected
        self.assertIsInstance(ctrl.programs, list)
        self.assertIsInstance(ctrl.programs[0], Program)
        self.assertIsInstance(ctrl.raw_programs, list)
        self.assertIsInstance(ctrl.raw_programs[0], dict)

        # test controller attributes
        self.assertIsInstance(ctrl.comm_path, str)
        self.assertIsInstance(ctrl.file_location, str)
        self.assertIsInstance(ctrl.ip_address, str)
        self.assertIsInstance(ctrl.l5x_meta_data, dict)
        self.assertIsInstance(ctrl.major_revision, int)
        self.assertIsInstance(ctrl.minor_revision, int)
        self.assertIsInstance(ctrl.name, str)
        self.assertIsInstance(ctrl.plc_module, dict)
        # the supplied file doesn't have this property. maybe update later?
        self.assertIsInstance(ctrl.plc_module_icp_port, dict)
        self.assertIsInstance(ctrl.plc_module_ports, list)
        self.assertIsInstance(ctrl.plc_module_ports[0], dict)
        self.assertIsInstance(ctrl.slot, int)

    def test_plc_object(self):
        """test plc types
        """
        # test plc object won't load without meta data
        with self.assertRaises(ValueError) as context:
            PlcObject(None, None)
        self.assertTrue(isinstance(context.exception, ValueError))

        # test plc object can load without a controller
        plc = PlcObject(TESTING_DATA, None)
        self.assertIsNotNone(plc)
        self.assertIsNone(plc.controller)
        self.assertIsNone(plc.config)
        self.assertIsInstance(plc.name, str)
        self.assertIsInstance(plc.description, str)
        self.assertIsInstance(plc.meta_data, dict)
        self.assertEqual(plc.name, TESTING_DATA['@Name'])
        self.assertEqual(plc.description, TESTING_DATA['Description'])
        del plc

        # load from testing file to check configs
        ctrl: Controller = Controller.from_file(TESTING_FILE)
        plc = PlcObject(TESTING_DATA, ctrl)
        self.assertIsInstance(plc.meta_data, dict)
        self.assertIsNotNone(plc.controller)
        self.assertIsInstance(plc.controller, Controller)
        self.assertIsInstance(plc.config, ControllerConfiguration)

        # test __getitem__ / __setitem__
        plc._meta_data['TestAttr'] = 'abc'
        self.assertEqual(plc['TestAttr'], 'abc')
        plc['TestAttr'] = '123'
        self.assertEqual(plc._meta_data['TestAttr'], '123')

    def test_datatype(self):
        """test datatype plc class
        """
        ctrl: Controller = Controller.from_file(TESTING_FILE)

        for dt in ctrl.raw_datatypes:
            datatype = Datatype(controller=ctrl,
                                l5x_meta_data=dt)
            self.logger.info('Datatype found -> %s', datatype.name)
            self.assertIsNotNone(datatype)
            self.assertIsInstance(datatype.name, str)
            self.assertIsInstance(datatype.class_, str)
            self.assertIsInstance(datatype.members, list)
            self.assertIsInstance(datatype.raw_members, list)

    def test_supports_class(self):
        """test supports class class
        """
        obj = SupportsClass(TESTING_DATA, None)
        obj.class_ = 'SomeData'
        self.assertEqual(obj.class_, 'SomeData')
        self.assertEqual(obj._meta_data['@Class'], 'SomeData')

    def test_supports_external_access(self):
        """test supports external access class
        """
        obj = SupportsExternalAccess(TESTING_DATA, None)
        obj.external_access = 'SomeData'
        self.assertEqual(obj.external_access, 'SomeData')
        self.assertEqual(obj._meta_data['@ExternalAccess'], 'SomeData')

    def test_datatype_member(self):
        """test datatype member plc class
        """
        ctrl: Controller = Controller.from_file(TESTING_FILE)
        self.assertTrue(len(ctrl.raw_datatypes) > 0)

        dt = Datatype(ctrl.raw_datatypes[0], ctrl)

        for mem in dt.raw_members:
            member = DatatypeMember(mem, dt, ctrl)
            self.logger.info('Member found -> %s', member.name)
            self.assertIsNotNone(member)
            self.assertIsInstance(member.name, str)
            self.assertIsInstance(member.dimension, str)
            self.assertIsInstance(member.external_access, str)
            self.assertIsInstance(member.hidden, str)
            self.assertIsInstance(member.radix, str)

    def test_tag(self):
        """test tag plc class
        """
        ctrl: Controller = Controller.from_file(TESTING_FILE)

        for t in ctrl.raw_tags:
            tag = Tag(controller=ctrl,
                      l5x_meta_data=t)
            self.logger.info('Tag found -> %s', tag.name)
            self.assertIsNotNone(tag)
            self.assertIsInstance(tag.name, str)
            self.assertTrue((isinstance(tag.description, str) or tag.description is None))
            self.assertIsInstance(tag.class_, str)
            self.assertIsInstance(tag.external_access, str)
            self.assertIsInstance(tag.opc_ua_access, str)
            self.assertIsInstance(tag.datatype, str)
            self.assertIsInstance(tag.data, list)

    def test_addon_instruction(self):
        """test addon instruction class
        """

        ctrl: Controller = Controller.from_file(TESTING_FILE)

        for a in ctrl.raw_aois:
            aoi = AddOnInstruction(controller=ctrl,
                                   l5x_meta_data=a)
            self.logger.info('AOI found -> %s', aoi.name)
            self.assertIsNotNone(aoi)
            self.assertIsInstance(aoi.name, str)
            self.assertTrue((isinstance(aoi.description, str) or aoi.description is None))
            self.assertTrue((isinstance(aoi.revision, str) or aoi.revision is None))
            self.assertIsInstance(aoi.execute_prescan, str)
            self.assertIsInstance(aoi.execute_postscan, str)
            self.assertIsInstance(aoi.execute_enable_in_false, str)
            self.assertIsInstance(aoi.created_by, str)
            self.assertIsInstance(aoi.created_date, str)
            self.assertIsInstance(aoi.edited_by, str)
            self.assertIsInstance(aoi.edited_date, str)
            self.assertTrue((isinstance(aoi.software_revision, str) or aoi.software_revision is None))
            self.assertTrue((isinstance(aoi.revision_note, str) or aoi.revision_note is None))
            self.assertIsInstance(aoi.parameters, list)
            self.assertIsInstance(aoi.local_tags, list)
            self.assertIsInstance(aoi.routines, list)

    def test_module(self):
        """test module class
        """
        ctrl: Controller = Controller.from_file(TESTING_FILE)

        for m in ctrl.raw_modules:
            module = Module(controller=ctrl,
                            l5x_meta_data=m)
            self.logger.info('Module found -> %s', module.name)
            self.assertIsNotNone(module)
            self.assertIsNotNone(module.meta_data)

            self.assertIsInstance(module.name, str)
            self.assertEqual(module.name, module.meta_data['@Name'])

            self.assertTrue((isinstance(module.description, str) or module.description is None))
            if module.description:
                self.assertEqual(module.description, module.meta_data['Description'])

            self.assertIsInstance(module.catalog_number, str)
            self.assertEqual(module.catalog_number, module.meta_data['@CatalogNumber'])

            self.assertIsInstance(module.vendor, str)
            self.assertEqual(module.vendor, module.meta_data['@Vendor'])

            self.assertIsInstance(module.product_type, str)
            self.assertEqual(module.product_type, module.meta_data['@ProductType'])

            self.assertIsInstance(module.product_code, str)
            self.assertEqual(module.product_code, module.meta_data['@ProductCode'])

            self.assertIsInstance(module.major, str)
            self.assertEqual(module.major, module.meta_data['@Major'])

            self.assertIsInstance(module.minor, str)
            self.assertEqual(module.minor, module.meta_data['@Minor'])

            self.assertIsInstance(module.parent_module, str)
            self.assertEqual(module.parent_module, module.meta_data['@ParentModule'])

            self.assertIsInstance(module.parent_mod_port_id, str)
            self.assertEqual(module.parent_mod_port_id, module.meta_data['@ParentModPortId'])

            self.assertIsInstance(module.inhibited, str)
            self.assertEqual(module.inhibited, module.meta_data['@Inhibited'])

            self.assertIsInstance(module.major_fault, str)
            self.assertEqual(module.major_fault, module.meta_data['@MajorFault'])

            self.assertIsInstance(module.ekey, dict)
            self.assertTrue(len(module.ekey.items()) > 0)

            self.assertIsInstance(module.ports, list)
            self.assertTrue(len(module.ports) > 0)

            self.assertIsInstance(module.communications, dict)
            self.assertTrue(len(module.communications.items()) > 0)

    def test_programs(self):
        '''test programs class
        '''
        ctrl: Controller = Controller.from_file(TESTING_FILE)

        for p in ctrl.raw_programs:
            program = Program(controller=ctrl,
                              l5x_meta_data=p)
            self.logger.info('Program found -> %s', program.name)
            self.assertIsNotNone(program)
            self.assertIsInstance(program.name, str)
            self.assertTrue((isinstance(program.description, str) or program.description is None))
            self.assertIsInstance(program.test_edits, str)
            self.assertIsInstance(program.main_routine_name, str)
            self.assertIsInstance(program.disabled, str)
            self.assertIsInstance(program.use_as_folder, str)
            self.assertIsInstance(program.tags, list)
            self.assertIsInstance(program.raw_routines, list)

    def test_routines(self):
        """test routines class
        """
        '''test programs class
        '''
        ctrl: Controller = Controller.from_file(TESTING_FILE)

        program: Program = next((x for x in ctrl.programs if len(x.routines) > 1), None)
        self.assertIsNotNone(program)
        routine: Routine = next((x for x in program.routines if len(x.rungs) > 1), None)
        self.assertIsNotNone(routine)
        self.assertIsInstance(routine.program, Program)
        self.assertIsInstance(routine.rungs, list)
        self.assertIsInstance(routine.raw_rungs, list)

    def test_controller_report(self):
        """test controller report class
        """
        ctrl: Controller = Controller.from_file(TESTING_FILE)
        report = ControllerReport(ctrl).run()
        self.assertIsInstance(report, ControllerReport)


class TestGM(LoggableUnitTest):

    def test_gm_plc(self):
        """test gm implimentation of plc class
        """

        # test ctrl loads from good file
        ctrl: GmController = GmController.from_file(TESTING_GM_FILE)
        self.assertIsNotNone(ctrl)

        self.assertTrue(len(ctrl.gm_programs) > 0)

        self.assertIsInstance(ctrl.kdiags, list)
        self.assertTrue(len(ctrl.kdiags) > 0)
        self.assertIsInstance(ctrl.kdiags[0], KDiag)

    def test_gm_program(self):
        """test gm program class
        """
        ctrl: GmController = GmController.from_file(TESTING_GM_FILE)
        program: GmProgram = next((x for x in ctrl.programs if x.is_gm_owned), None)
        self.assertIsNotNone(program)
        self.assertIsInstance(program, GmProgram)
        self.logger.info('Analyzing program -> %s', program.name)

        test_string = GmProgram.PARAM_RTN_STR
        param_found = False

        for routine in program.routines:
            if fnmatch(routine.name, test_string):
                self.logger.info('Match found -> %s', routine.name)
                param_found = True
                break
            else:
                self.logger.info('No Match -> %s', routine.name)

        self.assertTrue(param_found)

    def test_gm_rung(self):
        """test gm rung class
        """

        ctrl: GmController = GmController.from_file(TESTING_GM_FILE)
        program: GmProgram = next((x for x in ctrl.programs if x.is_gm_owned), None)
        self.assertIsNotNone(program)
        self.logger.info('Program found -> %s', program.name)
        routine: GmRoutine = next((x for x in program.routines if len(x.kdiags) > 0), None)
        self.logger.info('Routine found -> %s', routine.name)
        self.assertIsNotNone(routine)
        rung: GmRung = next((x for x in routine.rungs if x.has_kdiag), None)
        self.assertIsNotNone(rung)
        self.assertTrue(len(rung.kdiags) > 0)

    def test_gm_kdiag(self):
        """test gm kdiag class
        """
        ctrl: GmController = GmController.from_file(TESTING_GM_FILE)
        program: GmProgram = next((x for x in ctrl.programs if x.is_gm_owned), None)
        self.assertIsNotNone(program)
        self.logger.info('Program found -> %s', program.name)
        routine: GmRoutine = next((x for x in program.routines if len(x.kdiags) > 0), None)
        self.logger.info('Routine found -> %s', routine.name)
        self.assertIsNotNone(routine)
        rung: GmRung = next((x for x in routine.rungs if x.has_kdiag), None)
        self.assertIsNotNone(rung)
        self.assertTrue(len(rung.kdiags) > 0)
        kdiag: KDiag = next((x for x in rung.kdiags if x.diag_type is KDiagType.ALARM), None)
        self.assertIsNotNone(kdiag)
        self.logger.info('Text -> %s', kdiag.text)
        self.assertIsInstance(kdiag.text, str)
        self.logger.info('Number -> %s', kdiag.number)
        self.assertIsInstance(kdiag.number, int)
        self.assertTrue(kdiag.number > 0)
        self.logger.info('Parent Offset -> %s', kdiag.parent_offset)
        self.assertIsInstance(kdiag.parent_offset, int)
        self.logger.info('Global Number -> %s', kdiag.global_number)
        self.assertTrue(kdiag.global_number > 0)
        self.assertEqual(kdiag.global_number, (kdiag.number + kdiag.parent_offset))

        dups = ctrl.validate_text_lists()
        self.assertTrue(len(dups) == 0)

        dup_ctrl: GmController = GmController.from_file(TESTING_GM_DUP_ALARMS_FILE)
        dups = dup_ctrl.validate_text_lists()
        self.assertTrue(len(dups) > 0)
