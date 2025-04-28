"""pyrox application
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING, Union


from tkinter import Menu, Tk, Toplevel


from .abc import PartialApplication, PartialApplicationTask
from .abc import BaseMenu, PartialModel, PartialApplicationConfiguration, Loggable
from .abc.list import HashList


if TYPE_CHECKING:
    from .model import Model


__all__ = (
    'MainApplicationMenu',
    'ApplicationTask',
    'Application',
)


class MainApplicationMenu(BaseMenu):
    """Application `Main` Menu.

    Inherited from :class:`BaseMenu`, this parent class acts as the main menu for a root application

    .. ------------------------------------------------------------

    .. package:: types.application

    .. ------------------------------------------------------------

    Arguments
    -----------
    root: Union[:class:`Tk`, :class:`Toplevel`]
        The root tk object this menu belongs to.

    .. ------------------------------------------------------------

    Attributes
    -----------
    edit: :class:`Menu`
        The Edit :class:`Menu` for this :class:`MainApplicationMenu`.

    file: :class:`Menu`
        The File :class:`Menu` for this :class:`MainApplicationMenu`

    help: :class:`Menu`
        The Help :class:`Menu` for this :class:`MainApplicationMenu`

    tools: :class:`Menu`
        The Tools :class:`Menu` for this :class:`MainApplicationMenu`

    view: :class:`Menu`
        The View :class:`Menu` for this :class:`MainApplicationMenu`
    """

    __slots__ = ('_file', '_edit', '_tools', '_view', '_help')

    def __init__(self,
                 root: Union[Tk, Toplevel]):
        super().__init__(root=root)
        self._file: Menu = Menu(self.menu, name='file', tearoff=0)
        self._edit: Menu = Menu(self.menu, name='edit', tearoff=0)
        self._tools: Menu = Menu(self.menu, name='tools', tearoff=0)
        self._view: Menu = Menu(self.menu, name='view', tearoff=0)
        self._help: Menu = Menu(self.menu, name='help', tearoff=0)

        self.menu.add_cascade(label='File', menu=self.file)
        self.menu.add_cascade(label='Edit', menu=self.edit)
        self.menu.add_cascade(label='Tools', menu=self.tools)
        self.menu.add_cascade(label='View', menu=self.view)
        self.menu.add_cascade(label='Help', menu=self.help)

        self.root.config(menu=self.menu)

    @property
    def edit(self) -> Menu:
        """
        The Edit :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            edit: :class:`Menu`
        """
        return self._edit

    @property
    def file(self) -> Menu:
        """
        The File :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            file: :class:`Menu`
        """
        return self._file

    @property
    def help(self) -> Menu:
        """
        The Help :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            help: :class:`Menu`
        """
        return self._help

    @property
    def tools(self) -> Menu:
        """
        The Tools :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            tools: :class:`Menu`
        """
        return self._tools

    @property
    def view(self) -> Menu:
        """
        The View :class:`Menu` for this :class:`MainApplicationMenu`.

        .. ------------------------------------------------------------

        Returns
        -----------
            view: :class:`Menu`
        """
        return self._view

    @staticmethod
    def get_menu_commands(menu: Menu) -> dict:
        """Get all menu commands for a specified tk :class:`Menu`.

        .. ------------------------------------------------------------

        Arguments
        -----------

        menu: :class:`Menu`
            Menu to get all commands for.

        """
        cmds = {}
        try:
            for x in range(menu.index('end')+1):
                if menu.type(x) == 'command':
                    label = menu.entrycget(x, 'label')
                    cmd = menu.entrycget(x, 'command')
                    cmds[label] = cmd
        except TypeError:
            pass

        return cmds


class ApplicationTask(PartialApplicationTask):
    """model task for injecting functionality into an existing model.

    .. ------------------------------------------------------------

    .. package:: types.application

    .. ------------------------------------------------------------

    Attributes
    -----------
    application: :class:`PartialApplication`
        The parent application of this task.

    model: :class:`Model`
        The model this task reflects.
    """

    __slots__ = ()

    def __init__(self,
                 application: 'Application',
                 model: Model):
        super().__init__(application=application,
                         model=model)

    @property
    def application(self) -> 'Application':
        """The parent application of this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: :class:`Application`
        """
        return self._application

    @application.setter
    def application(self, value: 'Application'):
        self._application = value

    @property
    def model(self) -> Model:
        """The model this task reflects.

        .. ------------------------------------------------------------

        Returns
        -----------
            model: :class:`Model`
        """
        return self._model

    def inject(self) -> None:
        """Inject this task into the hosting application
        """

    def start(self) -> None:
        """Run this task
        """


class Application(PartialApplication):
    """Represents a :class:`PartialApplication` in the form of an :class:`Application`.

    .. ------------------------------------------------------------

    .. package:: types.application

    .. ------------------------------------------------------------

    Arguments
    -----------

    config: Optional[:class:`PartialApplicationConfiguration`]
        Configuration for this partial application. If not supplied, defaults to `generic_root` configuration.

    model: Optional[:class:`Model`]
        Optional model to build application with. Defaults to None.

    Attributes
    -----------
    menu: :class:`MainApplicationMenu`
        Main Tk :class:`Menu` for this :class:`Application`.

    running: :type:`bool`
        Running status of this :class:`Application`'s `Tk` interpreter.

    tasks: :class:`HashList` [:class:`ApplicationTask`]
        Hashed list of tasks for this :class:`Application`.


    """

    __slots__ = ('_menu', '_tasks')

    def __init__(self,
                 model: Optional[PartialModel] = None,
                 config: Optional[PartialApplicationConfiguration] = None):

        if not config:
            config = PartialApplicationConfiguration.root()

        super().__init__(model=model,
                         config=config)

        self._menu = None if config.headless else MainApplicationMenu(self.parent)
        self._tasks: HashList[PartialApplicationTask] = HashList('id')

        # when building a 'main' application, insert the app's handler into the global pool
        # a full application should be able to manage all child loggers
        Loggable.global_handlers.append(self._log_handler)

        # append all tasks from config into this application
        self.add_tasks(config.tasks)

    @property
    def menu(self) -> MainApplicationMenu:
        """Main Tk :class:`Menu` for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            menu: :class:`MainApplicationMenu`
        """
        return self._menu

    @property
    def tasks(self) -> HashList[PartialApplicationTask]:
        """Hashed list of tasks for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            tasks: :class:`HashList` [:class:`ApplicationTask`]
        """
        return self._tasks

    def add_task(self,
                 task: Union[ApplicationTask, type[ApplicationTask]],
                 model: Optional[Model] = None) -> Optional[ApplicationTask]:
        """Add an :class:`ApplicationTask` to this `Application`.

        This method calls the task's `inject` method.

        .. ---------------------------------------------------------------------

        Arguments
        ----------
        task: Union[:class:`ApplicationTask`, type[:class:`ApplicationTask`]]
            :class:`ApplicationTask` to add.

        .. ---------------------------------------------------------------------

        Returns
        ----------
        task: :class:`ApplicationTask` | `None`
            The built / injected task


        """
        if isinstance(task, ApplicationTask):
            self._tasks.append(task)
            task.inject()
            return task

        if isinstance(task, type):
            tsk = task(self, model if model else self.main_model)
            self._tasks.append(tsk)
            tsk.inject()
            return tsk

        return None

    def add_tasks(self,
                  tasks: Union[list[ApplicationTask], list[type[ApplicationTask]]],
                  model: Optional[Model] = None) -> Optional[ApplicationTask]:
        """Add a list of :class:`ApplicationTask`s to this `Application`.

        This method calls the task's `inject` method.

        .. ---------------------------------------------------------------------

        Arguments
        ----------
        task: Union[:class:`ApplicationTask`, type[:class:`ApplicationTask`]]
            :class:`ApplicationTask` to add.

        .. ---------------------------------------------------------------------

        Returns
        ----------
        task: :class:`ApplicationTask` | `None`
            The built / injected task


        """
        _ = [self.add_task(x, model) for x in tasks]
