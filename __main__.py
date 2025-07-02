"""run this app locally
    """
from pyrox import App, ApplicationConfiguration

if __name__ == '__main__':
    config = ApplicationConfiguration.root()
    config.title = 'Pyrox - PLC Programming Toolset'
    app = App(config=config)
    app.start()
