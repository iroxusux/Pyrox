"""types test suite
    """
from __future__ import annotations


import unittest


from ..types import Application, ApplicationConfiguration
from ..types.plc import ConnectionParameters


from .connection import ConnectionTask, ConnectionModel


__all__ = (
    'TestModels',
)


class TestModels(unittest.TestCase):
    """Testing class for models
    """

    def test_connection(self):
        """test connection model
        """
        # test generic build with no model

        app = Application(config=ApplicationConfiguration.root())

        task = app.add_task(ConnectionTask(app))
        self.assertTrue(task in app.tasks)
        self.assertIsNone(task.model)
        task.run()
        model: ConnectionModel = task.model
        self.assertIsInstance(model, ConnectionModel)
        params = ConnectionParameters('120.15.35.4', 3, 500)
        model.connect(params)
        self.assertTrue(model.connected)
        model.disconnect()
        self.assertFalse(model.connected)

        app.stop()
