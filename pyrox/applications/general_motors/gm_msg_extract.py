"""Main emulation model
    """
from __future__ import annotations


from ...models import (
    Application,
    ApplicationTask,
    LaunchableModel,
    ViewConfiguration,
    View,
    ViewModel,
    ViewType
)
from ...models.plc.gm import GmController


class GmMsgExtractView(View):
    """General Motors Message Extraction Interface View

    """


class GmMsgExtractViewModel(ViewModel):
    """General Motors Message Extraction View Model

    """


class GmMsgExtractModel(LaunchableModel):
    """General Motors Message Extraction Model.

    .. ------------------------------------------------------------

    Attributes
    -----------
    controller: :class:`Controller`
        Main controller for the emulation application.

    """

    def __init__(self,
                 app: Application):
        super().__init__(application=app,
                         view_model=GmMsgExtractViewModel,
                         view=GmMsgExtractView,
                         view_config=ViewConfiguration(name='Gm Message Extract',
                                                       parent=app.view.frame,
                                                       type_=ViewType.TOPLEVEL))

    def run(self,
            controller: GmController) -> None:
        if not self.application:
            raise RuntimeError

        if not controller:
            raise ValueError('Must have a controller to extract messages from!')

        # all_msgs = controller.kdiags


class GmMsgExtractTask(ApplicationTask):
    """General Motors Human-Machine Interface task.
    """

    def __init__(self,
                 application: Application):
        super().__init__(application=application)

    def run(self):
        GmMsgExtractModel(app=self.application).launch()

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='GM Message Extract', command=self.run)
