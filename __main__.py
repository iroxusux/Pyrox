"""run this engine locally
    """
from __future__ import annotations
from pyrox import App, ApplicationConfiguration


def main():
    """test this engine environment with a default application
    """
    app = App(config=ApplicationConfiguration.root())
    app.start()


if __name__ == '__main__':
    main()
