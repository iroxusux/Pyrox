"""run this engine locally (for debugging or demonstration purposes)
    """
from pyrox import Application, ApplicationConfiguration


def main():
    """test this engine environment with a default application
    """
    app_config = ApplicationConfiguration.root()
    app_config.view_config.name = 'Pyrox Application'
    Application(config=app_config).start()


if __name__ == '__main__':
    main()
