"""PLC Inspection Application
    """
from __future__ import annotations


from typing import Optional


from pyrox.applications.app import App, AppTask
from pyrox.models import ViewConfiguration, View


class ControllerVerifyView(View):
    """Connection view for PLC.
    """

    def __init__(self,
                 view_model=None,
                 config: Optional[ViewConfiguration] = ViewConfiguration()):
        super().__init__(view_model=view_model,
                         config=config)

    def build(self,
              **kwargs):
        pass


class ControllerVerifyTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)

    def run(self):
        if not self.application.controller:
            self.application.logger.error('No controller loaded to verify.')
            return
        self.application.logger.info('Verifying controller...')
        self.application.controller.verify()

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='Verify Controller', command=self.run)
