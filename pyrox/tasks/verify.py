"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models import View
from pyrox.models.utkinter import FrameWithTreeViewAndScrollbar
from pyrox.services.utkinter import populate_tree


class ControllerVerifyView(View):
    """Connection view for PLC.
    """

    def __init__(self,
                 parent=None):
        super().__init__(parent,
                         custom_frame_class=FrameWithTreeViewAndScrollbar)

    @property
    def frame(self) -> FrameWithTreeViewAndScrollbar:
        """Returns the frame of this view.
        """
        return super().frame


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
        report_data = self.application.controller.verify()
        self.application.logger.info('Creating tree view...')
        self.application.clear_workspace()
        verify_view = ControllerVerifyView(self.application.workspace)
        populate_tree(verify_view.frame.tree, '', report_data)

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='Verify Controller', command=self.run)
