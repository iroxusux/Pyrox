"""Controller Verify Task
"""
from tkinter import Menu

from pyrox.applications.app import App, AppTask
from pyrox.models.plc import validator


class ControllerVerifyTask(AppTask):
    """Controller verification task for the PLC verification Application.
    """

    def __init__(
        self,
        application: App
    ) -> None:
        super().__init__(application=application)

    def run(
        self,
        verify_type: str = 'full'
    ) -> None:
        if not self.controller:
            return
        ctrl_validator = validator.ControllerValidatorFactory.get_validator(self.controller)

        match verify_type:
            case 'full':
                ctrl_validator.validate_all(self.controller)
            case 'properties':
                ctrl_validator.validate_properties(self.controller)
            case 'datatypes':
                ctrl_validator.validate_datatypes(self.controller)
            case 'aois':
                ctrl_validator.validate_aois(self.controller)
            case 'tags':
                ctrl_validator.validate_tags(self.controller)
            case 'modules':
                ctrl_validator.validate_modules(self.controller)
            case 'programs':
                ctrl_validator.validate_programs(self.controller)
            case _:
                raise ValueError(f'Unknown verify type: {verify_type}')

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
