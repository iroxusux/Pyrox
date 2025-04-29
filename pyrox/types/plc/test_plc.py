"""testing module for plc types
    """
from __future__ import annotations


from .plc import (
    PlcObject,
    Controller,
    ControllerConfiguration,
    Datatype,
    DatatypeMember,
    Tag,
    AddOnInstruction,
    Module,
    Program,
    ProgramTag,
    Routine,
    Rung,
    SupportsClass,
    SupportsExternalAccess,
    SupportsRadix
)

from .gm import (
    GmController,
    GmProgram,
    GmRoutine,
    SupportsGmNaming
)


from ..abc.meta import LoggableUnitTest


TESTING_FILE = r'C:\Users\MH8243\OneDrive - EQUANS\Documents\Physirox\rox_workspace\_test.L5X'
TESTING_GM_FILE = TESTING_FILE.replace('_test.L5X', '_test_gm.L5X')


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
        self.assertIsInstance(ctrl.aois, list)
        self.assertIsInstance(ctrl.raw_aois, list)
        self.assertIsInstance(ctrl.raw_aois[0], dict)
        self.assertIsInstance(ctrl.comm_path, str)
        self.assertIsInstance(ctrl.datatypes, list)
        self.assertIsInstance(ctrl.raw_datatypes, list)
        self.assertIsInstance(ctrl.raw_datatypes[0], dict)
        self.assertIsInstance(ctrl.tags, list)
        self.assertIsInstance(ctrl.raw_tags, list)
        self.assertIsInstance(ctrl.raw_tags[0], dict)
        self.assertIsInstance(ctrl.file_location, str)
        self.assertIsInstance(ctrl.ip_address, str)
        self.assertIsInstance(ctrl.l5x_meta_data, dict)
        self.assertIsInstance(ctrl.major_revision, int)
        self.assertIsInstance(ctrl.minor_revision, int)
        self.assertIsInstance(ctrl.modules, list)
        self.assertIsInstance(ctrl.raw_modules, list)
        self.assertIsInstance(ctrl.raw_modules[0], dict)
        self.assertIsInstance(ctrl.name, str)
        self.assertIsInstance(ctrl.programs, list)
        self.assertIsInstance(ctrl.raw_programs, list)
        self.assertIsInstance(ctrl.raw_programs[0], dict)
        self.assertIsInstance(ctrl.plc_module, dict)
        self.assertIsNone(ctrl.plc_module_icp_port)  # the supplied file doesn't have this property. maybe update later?
        self.assertIsInstance(ctrl.plc_module_ports, list)
        self.assertIsInstance(ctrl.plc_module_ports[0], dict)
        self.assertIsInstance(ctrl.root_meta_data, dict)
        self.assertIsInstance(ctrl.slot, int)

    def test_plc_object(self):
        """test plc types
        """
        # test plc object won't load without meta data
        with self.assertRaises(ValueError) as context:
            PlcObject(None, None)
        self.assertTrue(isinstance(context.exception, ValueError))

        testing_data = {
            '@Name': 'Test object',
            'Description': 'description'
        }

        # test plc object can load without a controller
        plc = PlcObject(testing_data, None)
        self.assertIsNotNone(plc)
        self.assertIsNone(plc.controller)
        self.assertIsNone(plc.config)
        self.assertIsInstance(plc.name, str)
        self.assertIsInstance(plc.description, str)
        self.assertIsInstance(plc.meta_data, dict)
        self.assertEqual(plc.name, 'Test object')
        self.assertEqual(plc.description, 'description')
        del plc

        # load from testing file to check configs
        ctrl: Controller = Controller.from_file(TESTING_FILE)
        plc = PlcObject(testing_data, ctrl)
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
            self.assertIsInstance(datatype.plc_class, str)
            self.assertIsInstance(datatype.members, list)
            self.assertIsInstance(datatype.raw_members, list)

    def test_supports_class(self):
        """test supports class class
        """
        testing_data = {
            '@Name': 'Test object',
            'Description': 'description'
        }
        obj = SupportsClass(testing_data, None)
        obj.plc_class = 'SomeData'
        self.assertEqual(obj.plc_class, 'SomeData')
        self.assertEqual(obj._meta_data['@Class'], 'SomeData')

    def test_supports_external_access(self):
        """test supports external access class
        """
        testing_data = {
            '@Name': 'Test object',
            'Description': 'description'
        }
        obj = SupportsExternalAccess(testing_data, None)
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
            self.assertIsInstance(tag.plc_class, str)
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
            self.assertIsInstance(module.name, str)
            self.assertTrue((isinstance(module.description, str) or module.description is None))
            self.assertIsInstance(module.catalog_number, str)
            self.assertIsInstance(module.vendor, str)
            self.assertIsInstance(module.product_type, str)
            self.assertIsInstance(module.product_code, str)
            self.assertIsInstance(module.major, str)
            self.assertIsInstance(module.minor, str)
            self.assertIsInstance(module.parent_module, str)
            self.assertIsInstance(module.parent_mod_port_id, str)
            self.assertIsInstance(module.inhibited, str)
            self.assertIsInstance(module.major_fault, str)
            self.assertIsInstance(module.ekey, dict)
            self.assertIsInstance(module.ports, list)
            self.assertIsInstance(module.communications, list)

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


class TestGM(LoggableUnitTest):

    def test_gm_plc(self):
        """test gm implimentation of plc class
        """

        # test ctrl loads from good file
        ctrl: GmController = GmController.from_file(TESTING_GM_FILE)
        self.assertIsNotNone(ctrl)
        self.assertIsInstance(ctrl.raw_aois, list)
        self.assertIsInstance(ctrl.raw_aois[0], dict)
        self.assertIsInstance(ctrl.comm_path, str)
        self.assertIsInstance(ctrl.datatypes, list)
        self.assertIsInstance(ctrl.raw_datatypes, list)
        self.assertIsInstance(ctrl.raw_datatypes[0], dict)
        self.assertIsInstance(ctrl.tags, list)
        self.assertIsInstance(ctrl.raw_tags, list)
        self.assertIsInstance(ctrl.raw_tags[0], dict)
        self.assertIsInstance(ctrl.file_location, str)
        self.assertIsInstance(ctrl.ip_address, str)
        self.assertIsInstance(ctrl.l5x_meta_data, dict)
        self.assertIsInstance(ctrl.major_revision, int)
        self.assertIsInstance(ctrl.minor_revision, int)
        self.assertIsInstance(ctrl.raw_modules, list)
        self.assertIsInstance(ctrl.raw_modules[0], dict)
        self.assertIsInstance(ctrl.name, str)
        self.assertIsInstance(ctrl.raw_programs, list)
        self.assertIsInstance(ctrl.raw_programs[0], dict)
        self.assertIsInstance(ctrl.plc_module, dict)
        self.assertIsInstance(ctrl.plc_module_icp_port, dict)
        self.assertIsInstance(ctrl.plc_module_ports, list)
        self.assertIsInstance(ctrl.plc_module_ports[0], dict)
        self.assertIsInstance(ctrl.root_meta_data, dict)
        self.assertIsInstance(ctrl.slot, int)

        self.assertTrue(len(ctrl.gm_programs) > 0)
