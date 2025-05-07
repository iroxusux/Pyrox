from ..abc.model import Model
from ..view_model.inspect import InspectVm


class Inspect(Model):
    """Inspect PLC Object model

    Args:
        Model (_type_): Base Model
    """

    def __init__(self,
                 config):
        self._exit: bool = False
        super().__init__(config,
                         InspectVm)

    def _setup(self):
        self._logger.info('setting up...')
        self.viewmodel.setup()

    def _run(self):
        self._logger.info('run...')
        self._logger.info('Config: %s', self._config)
        self._logger.info('Running boot...')
        self._boot()
        self._logger.info('Running mainloop...')
        self._vm.view.root.focus()
        self._vm.view.root.mainloop()

    def run(self) -> int:
        """run this manager

        Returns:
            int: exit code
        """
        self._logger.info('initializing...')
        self._setup()
        self._run()
        return 0
