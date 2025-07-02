"""PLC Inspection Application
    """
from __future__ import annotations

from typing import Optional

from pyrox.applications.app import App, AppTask
from pyrox.models.utkinter import TaskFrame
from pyrox.models.utkinter.treeview import LazyLoadingTreeView


class ControllerVerifyFrame(TaskFrame):
    """Connection view for PLC.
    """

    def __init__(self,
                 parent=None):
        super().__init__(parent,
                         name='Controller Verification',)
        self._tree = LazyLoadingTreeView(master=self.content_frame,
                                         columns=('Value',))
        self._tree.heading('#0', text='Name')
        self._tree.heading('Value', text='Value')
        self._tree.pack(fill='both', expand=True, side='top')

    @property
    def tree(self) -> LazyLoadingTreeView:
        """Returns the tree view of this view.
        """
        return self._tree


class ControllerVerifyTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def __init__(self,
                 application: App):
        super().__init__(application=application)
        self._frame: Optional[ControllerVerifyFrame] = None

    def run(self):
        if not self.application.controller:
            self.application.logger.error('No controller loaded to verify.')
            return
        if not self._frame or not self._frame.winfo_exists():
            self._frame = ControllerVerifyFrame(self.application.workspace)
            self._frame.on_destroy.append(lambda: self.application.unregister_frame(self._frame))
            self.application.register_frame(self._frame, raise_=True)

        self.application.logger.info('Verifying controller...')
        self._frame.tree.clear()
        self._frame.tree.populate_tree('', self.application.controller.verify())
        self.application.set_frame(self._frame)

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='Verify Controller', command=self.run)
