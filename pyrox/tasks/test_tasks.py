"""types test suite
    """
from __future__ import annotations


from pyrox.models.plc import Controller


import unittest


__all__ = (
    'TestTasks',
)


UNITTEST_PLC_FILE = r'docs\controls\unittest.L5X'


class TestTasks(unittest.TestCase):
    """Testing class for tasks
    """

    def test_verify_task(self):
        """test builtin tasks
        """
        ctrl = Controller.from_file(UNITTEST_PLC_FILE)
        self.assertIsNotNone(ctrl)
        report = ctrl.verify()
        self.assertTrue(len(report['UnpairedControllerInputs']) == 2)
        self.assertTrue(len(report['RedundantOutputs']) == 3)
        self.assertIsNotNone(report)
