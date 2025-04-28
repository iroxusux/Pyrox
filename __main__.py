"""run this engine locally (for debugging or demonstration purposes)
    """
from pyrox import Application, ApplicationConfiguration


def main():
    """test this engine environment with a default application
    """
    Application(config=ApplicationConfiguration.root('Pyrox Application')).start()


if __name__ == '__main__':
    main()
