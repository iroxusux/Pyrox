"""Test tools module for Pyrox PLC models.
    """
import unittest
from unittest.mock import MagicMock
from pyrox.tasks.tools.generate import ControllerGenerateTask
from pyrox.applications.app import App
from pyrox.models.plc import Controller, Program, Routine


class TestControllerGenerateTask(unittest.TestCase):
    @property
    def program(self):
        return self.mock_app.controller.programs.get('MCP', None)

    def setUp(self):
        self.mock_app = MagicMock(spec=App)
        self.controller = Controller()
        self.mock_app.controller = self.controller
        program = Program(controller=self.controller)
        program.name = 'MCP'
        main_routine = Routine(controller=self.controller, program=program)
        main_routine.name = 'Main'
        program.add_routine(main_routine)
        self.controller.add_program(program)
        self.task = ControllerGenerateTask(application=self.mock_app)

    def test_generate_gm_emulation_routine(self):
        self.assertNotIn('aaa_Emulation', self.program.routines)
        self.task.generate_gm_emulation_routine()
        self.assertIn('aaa_Emulation', self.program.routines)

    def test_generate_ford(self):
        with self.assertRaises(NotImplementedError):
            self.task.generate_ford()

    def test_generate_stellantis(self):
        with self.assertRaises(NotImplementedError):
            self.task.generate_stellantis()


if __name__ == "__main__":
    unittest.main()
