"""testing module for services
    """
import os


from . import directory


from ..types.abc.meta import LoggableUnitTest


__all__ = (
    'TestServices',
)


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
