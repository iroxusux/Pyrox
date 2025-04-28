"""General directory services module
    """


import os


import platformdirs


from . import file


class ApplicationDirectoryService:
    """Application Directory Service

    Manage Application Directories with this service class

    .. ------------------------------------------------------------

    .. package:: services.directory

    .. ------------------------------------------------------------

    Attributes
    -----------
    root: :class:`str`
        Root directory for this service.
    """

    def __init__(self,
                 author_name: str,
                 app_name: str):
        if not author_name or author_name == '':
            raise ValueError('A valid, non-null author name must be supplied for this class!')

        if not app_name or app_name == '':
            raise ValueError('A valid, non-null application name must be supplied for this class!')

        self._app_name = app_name
        self._author_name = author_name

    @property
    def app_name(self) -> str:
        """Application Name supplied to this service class

        .. ------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return self._app_name

    @property
    def author_name(self) -> str:
        """Author Name supplied to this service class

        .. ------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return self._author_name

    @property
    def user_cache(self):
        """User cache directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_cache_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_config(self):
        """User config directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_config_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_data(self):
        """User data directory.

        Example >>> 'C:/Users/JohnSmith/AppData/Local/JSmithEnterprises/MyApplication'

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_data_dir(self._app_name, self._author_name, ensure_exists=True)

    @property
    def user_documents(self):
        """User documents directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_documents_dir()

    @property
    def user_downloads(self):
        """User downloads directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_downloads_dir()

    @property
    def user_log(self):
        """User log directory.

        .. ---------------------------------------------------------------------------

        Returns
        ----------
        :class:`str`
        """
        return platformdirs.user_log_dir(self._app_name, self._author_name)

    def build_directory(self,
                        as_refresh: bool = False):
        """Build the directory for the parent application.

        Uses the supplied name for directory naming.
        """
        # --- cache --- #
        if os.path.isdir(self.user_cache):
            if as_refresh:
                file.remove_all_files(self.user_cache)

        else:
            os.mkdir(self.user_cache)

        # --- config --- #
        if os.path.isdir(self.user_config):
            if as_refresh:
                file.remove_all_files(self.user_config)

        else:
            os.mkdir(self.user_config)

        # --- data --- #
        if os.path.isdir(self.user_data):
            if as_refresh:
                file.remove_all_files(self.user_data)

        else:
            os.mkdir(self.user_data)


def get_appdata() -> str:
    """get app data directory location for this user

    Returns:
        str: app data directory location
    """
    return os.getenv('APPDATA')
