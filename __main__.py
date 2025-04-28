"""run this engine locally (for debugging or demonstration purposes)
    """
from pyrox import Application, ApplicationConfiguration


def main():
    """test this engine environment with a default application
    """
    app_cgf = ApplicationConfiguration.root('Pyrox Application')
    app = Application(config=app_cgf)
    app.start()


if __name__ == '__main__':
    main()
