"""run this engine locally (for debugging or demonstration purposes)
    """
from pyrox import Application, ApplicationConfiguration
from pyrox.models import EmulationModel, ConnectionTask


def main():
    """test this engine environment with a default application
    """
    app_config = ApplicationConfiguration.root()
    app_config.app_config.name = 'Pyrox Application'
    app = Application(model=EmulationModel, config=app_config)

    app.add_task(ConnectionTask(application=app))

    app.start()


if __name__ == '__main__':
    main()
