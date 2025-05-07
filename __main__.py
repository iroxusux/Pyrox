"""run this engine locally (for debugging or demonstration purposes)
    """
from pyrox import Application, ApplicationConfiguration
from pyrox.models import EmulationModel
from pyrox.types.model import TestModelA, TestModelB, TestModelC


def main():
    """test this engine environment with a default application
    """
    app_config = ApplicationConfiguration.root()
    app_config.view_config.name = 'Pyrox Application'
    app = Application(model=EmulationModel, config=app_config)
    app.add_model(TestModelA(app))
    app.add_model(TestModelB(app))
    app.add_model(TestModelC(app))

    app.start()


if __name__ == '__main__':
    main()
