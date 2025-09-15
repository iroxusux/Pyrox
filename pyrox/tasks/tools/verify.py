"""PLC Inspection Application
    """
from __future__ import annotations

from tkinter import Menu, Scrollbar, VERTICAL, Y, RIGHT
from typing import Optional, Union

from pyrox.applications.app import App, AppTask
from pyrox.models.gui import TaskFrame
from pyrox.models.gui.treeview import LazyLoadingTreeView
from pyrox.models.plc import Controller, ControllerValidator, ControllerValidatorFactory


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

        vscrollbar = Scrollbar(self.content_frame, orient=VERTICAL, command=self._tree.yview)
        vscrollbar.pack(fill=Y, side=RIGHT)

        self._tree['yscrollcommand'] = vscrollbar.set
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

    def _precheck(self) -> Union[Controller, None]:
        controller = self.application.controller

        if not controller:
            self.logger.error('No controller set in the application.')
            return None

        return controller

    def _get_validator(
        self,
        controller: Controller
    ) -> ControllerValidator:
        validator: ControllerValidator = ControllerValidatorFactory.get_registered_type_by_supporting_class(controller.__class__.__name__)
        if not isinstance(validator, type(ControllerValidator)):
            self.logger.error(f'No validator found for controller type {controller.__class__.__name__}.')
            return None
        return validator()

    def run(
        self,
        verify_type: str = 'full'
    ) -> None:
        controller = self._precheck()
        if not controller:
            return
        validator = self._get_validator(controller)
        if not validator:
            return
        self.logger.info(f'Running {verify_type} verification using {validator.__class__.__name__}...')

        match verify_type:
            case 'full':
                validator.validate_all(controller)
            case 'properties':
                validator.validate_properties(controller)
            case 'datatypes':
                validator.validate_datatypes(controller)
            case 'aois':
                validator.validate_aois(controller)
            case 'tags':
                validator.validate_tags(controller)
            case 'modules':
                validator.validate_modules(controller)
            case 'programs':
                validator.validate_programs(controller)
            case _:
                self.logger.error(f'Unknown verification type: {verify_type}')

    def inject(self) -> None:
        drop_down = Menu(self.application.menu.tools, tearoff=0)
        drop_down.add_command(label='Verify Controller (All)', command=lambda: self.run('full'))
        drop_down.add_separator()
        drop_down.add_command(label='Verify Controller (Properties Only)', command=lambda: self.run('properties'))
        drop_down.add_command(label='Verify Controller (Datatypes Only)', command=lambda: self.run('datatypes'))
        drop_down.add_command(label='Verify Controller (AOIs Only)', command=lambda: self.run('aois'))
        drop_down.add_command(label='Verify Controller (Modules Only)', command=lambda: self.run('modules'))
        drop_down.add_command(label='Verify Controller (Tags Only)', command=lambda: self.run('tags'))
        drop_down.add_command(label='Verify Controller (Program Only)', command=lambda: self.run('programs'))

        self.application.menu.tools.add_cascade(label='Verify', menu=drop_down)
