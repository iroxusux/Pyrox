"""types test suite
    """
from __future__ import annotations


import unittest


from pyrox import Application, ApplicationConfiguration, Model


from .builtin import ExitTask, HelpTask, PreferencesTask


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
        mdl = Model(application=app)

        app.set_model(mdl)

        exit_task = ExitTask(app, mdl)
        exit_task.inject()

        preferences_task = PreferencesTask(app, mdl)
        preferences_task.inject()

        help_task = HelpTask(app, mdl)
        help_task.inject()

        app.stop()
