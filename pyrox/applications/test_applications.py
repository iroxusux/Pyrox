"""types test suite
    """
from __future__ import annotations


import unittest


from ..services.plc_services import get_xml_string_from_file
from ..models import Application, ApplicationConfiguration
from ..models.plc import ConnectionParameters


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


class TestTrevorsCode(unittest.TestCase):
    """ Trevor Hurley Industries Testing Class
    """

    def test_my_code(self):
        my_file = get_xml_string_from_file(r"C:\Users\XX6021\OneDrive - EQUANS\Downloads\Fudt_VFD_MS_Simple_DataType.L5X")
        self.assertIsNotNone(my_file)
        print('this is just a print')
