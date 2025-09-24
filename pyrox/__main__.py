"""run this app
    """
from pyrox.applications import App
from pyrox.models import ApplicationConfiguration

if __name__ == '__main__':
    config = ApplicationConfiguration.root()
    config.application_name = 'pyrox'
    config.author_name = 'physirox'
    config.title = 'Pyrox - PLC Programming Toolset'
    app = App(config=config).start()
