"""run this engine locally (for debugging or demonstration purposes)
    """
from __future__ import annotations


from pyrox.applications import App
from pyrox import ApplicationConfiguration


def main():
    """test this engine environment with a default application
    """
    app = App(config=ApplicationConfiguration.root())
    app.start()


if __name__ == '__main__':
    main()
