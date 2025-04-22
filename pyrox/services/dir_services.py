"""General directory services module
    """


import os


def get_appdata() -> str:
    """get app data directory location for this user

    Returns:
        str: app data directory location
    """
    return os.getenv('APPDATA')
