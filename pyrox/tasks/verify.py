"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models import View
from pyrox.models.utkinter import FrameWithTreeViewAndScrollbar, populate_tree


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
        report_data = self.application.controller.verify().as_dictionary()
        self.application.logger.info('Finding redundant OTE instructions...')
        duplicate_coils_data = self.application.controller.find_redundant_otes()
        self.application.logger.info('Finding unpaired input instructions...')
        missing_coils_data = self.application.controller.find_unpaired_controller_inputs()
        data = {
            'report': report_data,
            'duplicate_coils': duplicate_coils_data,
            'missing_coils': missing_coils_data
        }
        self.application.logger.info('Creating tree view...')
        verify_view = ControllerVerifyView(self.application.workspace)
        populate_tree(verify_view.frame.tree, '', data)

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='Verify Controller', command=self.run)
