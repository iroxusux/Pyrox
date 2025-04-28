"""types test suite
    """
from __future__ import annotations


import unittest


from pyrox import Application, ApplicationConfiguration, Model


from .builtin import ExitTask


__all__ = (
    'TestTasks',
)


class TestTasks(unittest.TestCase):
    """Testing class for tasks
    """

    def test_builtins(self):
        """test builtin tasks
        """
        app = Application(config=ApplicationConfiguration.root())
        mdl = Model(app=app)

        app.set_model(mdl)

        task = ExitTask(app, mdl)
        task.inject()
