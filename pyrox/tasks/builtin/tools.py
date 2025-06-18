""" manage PLC tasks as built-ins
    """
from __future__ import annotations


from typing import Callable, TYPE_CHECKING


from ...models.application import ApplicationTask
from ...models import SafeList


if TYPE_CHECKING:
    from ...models import Model, Application


class ControllerVerifyTask(ApplicationTask):
    """PLC Controller Verify Task

    Verify controller for anomolies / errors

    .. ------------------------------------------------------------
    """

    def __init__(self,
                 application: Application,
                 model: Model):
        super().__init__(application=application,
                         model=model)
        self.on_verify: SafeList[Callable] = []

    def _on_verify(self):
        _ = [x() for x in self.on_verify]

    def inject(self) -> None:
        if not self.application.menu:
            return

        self.application.menu.tools.insert_command(0, label='Verify Controller', command=self._on_verify)

        if self.model:  # only bind to the correct model when creating
            self.on_verify.append(self.model.verify_controller)
