"""run this app locally
    """
from pyrox import App, ApplicationConfiguration

if __name__ == '__main__':
    app = App(config=ApplicationConfiguration.root())
    app.start()
