"""Controller Validate Task
"""
from datetime import datetime
from tkinter import Menu

from pyrox.applications.app import App, AppTask
from pyrox.models.plc import validator


class ControllerValidatorTask(AppTask):
    """Controller validator task.
    """

    def __init__(
        self,
        application: App
    ) -> None:
        super().__init__(application=application)

    def run(
        self,
        validate_type: str = 'full'
    ) -> None:
        if not self.controller:
            return
        ctrl_validator = validator.ControllerValidatorFactory.get_validator(self.controller)

        with self.application.multi_stream.temporary_stream(ctrl_validator.log_file_stream):
            ctrl_validator.log().info(f'--- Starting Controller Validation: {validate_type} ---')
            ctrl_validator.log().info(f'Timestamp: {datetime.now().isoformat()}')
            ctrl_validator.log().info(f'Controller: {self.controller.name} (ID: {self.controller.id})')
            ctrl_validator.log().info(f'File: {self.controller.file_location}')
            ctrl_validator.log().info('')
            match validate_type:
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
                    raise ValueError(f'Unknown Validate type: {validate_type}')
            ctrl_validator.log().info(f'--- Controller Validation Complete ---')

    def inject(self) -> None:
        drop_down = Menu(self.application.menu.tools, tearoff=0)
        drop_down.add_command(label='Validate Controller (All)', command=lambda: self.run('full'))
        drop_down.add_separator()
        drop_down.add_command(label='Validate Controller (Properties Only)', command=lambda: self.run('properties'))
        drop_down.add_command(label='Validate Controller (Datatypes Only)', command=lambda: self.run('datatypes'))
        drop_down.add_command(label='Validate Controller (AOIs Only)', command=lambda: self.run('aois'))
        drop_down.add_command(label='Validate Controller (Modules Only)', command=lambda: self.run('modules'))
        drop_down.add_command(label='Validate Controller (Tags Only)', command=lambda: self.run('tags'))
        drop_down.add_command(label='Validate Controller (Program Only)', command=lambda: self.run('programs'))

        self.application.menu.tools.add_cascade(label='Validate', menu=drop_down)
