"""testing module for services
    """
import os


from . import directory
from . import plc_services


from ..types.abc.meta import LoggableUnitTest
from ..types.plc.plc import Controller


__all__ = (
    'TestServices',
)


DUPS_TEST_FILE = r'docs\controls\_test_duplicate_coils.L5X'
GM_TEST_FILE = r'docs\controls\_test_gm.L5X'


class TestServices(LoggableUnitTest):
    """test class for meta module
    """

    def test_directory_service_class(self):
        """test id generator generates unique ids
        """
        self.logger.info('Testing directory service class...')
        author_name = 'IndiconLLC'
        app_name = 'TestingDirectory'   # create common name for testing

        # init service with common name
        dir_class = directory.ApplicationDirectoryService(author_name, app_name)

        self.assertEqual(dir_class.author_name, author_name)
        self.assertEqual(dir_class.app_name, app_name)

        self.logger.info('Rebuilding directories...')
        dir_class.build_directory(True)

        self.assertTrue(os.path.isdir(dir_class.user_cache))
        self.assertTrue(os.path.isdir(dir_class.user_config))
        self.assertTrue(os.path.isdir(dir_class.user_data))
        self.assertTrue(os.path.isdir(dir_class.user_documents))
        self.assertTrue(os.path.isdir(dir_class.user_downloads))
        self.logger.info('Available Directories...')
        self.logger.info(dir_class.user_cache)
        self.logger.info(dir_class.user_config)
        self.logger.info(dir_class.user_data)
        self.logger.info(dir_class.user_documents)
        self.logger.info(dir_class.user_downloads)

    def test_plc_services(self):
        """test plc services
        """
        ctrl_dict: dict = plc_services.controller_dict_from_file(DUPS_TEST_FILE)
        self.assertIsInstance(ctrl_dict, dict)

        ctrl: Controller = Controller.from_file(DUPS_TEST_FILE)

        duplicates, all_coils = plc_services.find_redundant_otes(ctrl, True)
        self.assertTrue(len(all_coils) > 0)
        self.assertTrue(len(duplicates) > 0)

        gm_ctrl: Controller = Controller.from_file(GM_TEST_FILE)
        diag_rungs = plc_services.find_diagnostic_rungs(gm_ctrl)
        self.assertTrue(len(diag_rungs) > 0)
