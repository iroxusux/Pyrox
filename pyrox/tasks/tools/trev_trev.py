"""PLC Inspection Application
    """
from __future__ import annotations


from pyrox.applications.app import App, AppTask
from pyrox.models import View
from pyrox.models.gui import FrameWithTreeViewAndScrollbar


class TrevorView(View):
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


class TrevorTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)

    def run(self):
        if not self.application.controller:
            self.application.logger.error('No controller loaded to verify.')
            return
        self.logger.info('We are running Trevors task...')

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='TrevTrev', command=self.run)
