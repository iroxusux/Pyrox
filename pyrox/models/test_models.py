"""types test suite
    """
from __future__ import annotations


import unittest


from ..types import Application, ApplicationConfiguration
from ..types.plc import ConnectionParameters


from .connection import ConnectionModel


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
        model = ConnectionModel(app)

        task = model.connection_task
        self.assertTrue(task in app.tasks)

        params = ConnectionParameters('120.15.35.4', 3, 500)

        model.connect(params)

        self.assertTrue(model.connected)

        model.disconnect()

        self.assertFalse(model.connected)

        app.close()
