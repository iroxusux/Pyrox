"""pyrox application
    """
from __future__ import annotations


from typing import Callable, Optional, TYPE_CHECKING, Union


from tkinter import (
    BOTH,
    BOTTOM,
    END,
    LabelFrame,
    LEFT,
    TOP,
    X,
    Y,
    Menu,
    TclError,
    Tk,
    Toplevel,
)


from .abc import (
    PartialApplication,
    PartialApplicationTask,
    BaseMenu,
    PartialApplicationConfiguration,
    HashList,
    SnowFlake
)

from .utkinter.frames import LogWindow, OrganizerWindow, PyroxFrame


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

    __slots__ = ('_active_models', '_file', '_edit', '_tools', '_view', '_help', '_on_new_model')

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

        # add a builtin cascade to view all active models
        self._active_models: Menu = Menu(self.view, name='active_models', tearoff=0)
        self._on_new_model: list[Callable] = []
        self.view.add_cascade(label='Active Models', menu=self.active_models)

        self.root.config(menu=self.menu)

    @property
    def active_models(self) -> Menu:
        """
        The currently active models within this :class:`MainApplicationMenu`'s :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        -----------
            active_models: :class:`Menu`
        """
        return self._active_models

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
    def on_new_model(self) -> list[Callable]:
        return self._on_new_model

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

    def on_model_select(self, model: Model):
        self.logger.info('model selected -> %s', str(model))
        _ = [x(model=model) for x in self._on_new_model]

    def socket_update_models(self, *args, **kwargs):
        if not kwargs['models'] or not kwargs['models']['hash_list']:
            return

        self.active_models.delete(0, END)

        for x in kwargs['models']['hash_list']:
            mdl: Model = kwargs['models']['hash_list'][x]
            self.active_models.add_command(label=str(mdl), command=lambda y=mdl: self.on_model_select(y))


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
                 model: Model = None):
        super().__init__(application=application,
                         model=model)

    def __repr__(self):
        return self.__class__.__name__

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

    __slots__ = ('_menu', '_tasks', '_log_window')

    def __init__(self,
                 config: PartialApplicationConfiguration = None):
        super().__init__(config=config)

        self._log_window = None
        self._model_hash: HashList[Model] = None
        self._organizer = None
        self._tasks = None
        self._workspace = None

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
    def model_hash(self) -> HashList[Model]:
        """Hashed list of all models associated with this application.

        Returns
        ----------
            model_hash :class:`HashList`
        """
        return self._model_hash

    @property
    def organizer(self) -> Optional[OrganizerWindow]:
        """The organizer window for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            organizer: :class:`OrganizerWindow`
        """
        return self._organizer

    @property
    def tasks(self) -> HashList[PartialApplicationTask]:
        """Hashed list of tasks for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            tasks: :class:`HashList` [:class:`ApplicationTask`]
        """
        return self._tasks

    @property
    def workspace(self) -> Optional[LabelFrame]:
        """The workspace window for this :class:`Application`.

        .. ------------------------------------------------------------

        Returns
        --------
            workspace: :class:`LabelFrame`
        """
        return self._workspace

    def add_model(self,
                  model: Model) -> Model:
        """Add a :class:`Model` to this :class:`Application`.

        Arguments
        ----------
        model :class:`PartialModel`
            Model to add to this application.

        .. ------------------------------------------------------------

        Raises
        -----------
        :class:`ValueError`
            Incorrect model type was passed to application

        .. ------------------------------------------------------------

        Returns
        ----------
        model :class:`PartialModel`
            Model to add to this application.
        """
        if not issubclass(type(model), Model):
            raise TypeError(f'Model must be of type `Model`, not {type(model)}...')

        self._model_hash.append(model)

        return model

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
            tsk = task(self, model)
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
        if not tasks:
            return

        _ = [self.add_task(x, model) for x in tasks]

    def build(self):
        """Build this :class:`Application`.

        This method will build the main menu, organizer window, log window and workspace if they are enabled in the configuration.

        """
        super().build()

        if not self.application:
            self.logger.error('Cannot build application, no application root found')
            return

        self._tasks: HashList[PartialApplicationTask] = HashList('id')
        self._menu = None if self.config.headless is True else MainApplicationMenu(self.application)
        self._model_hash = HashList(SnowFlake.id.__name__)

        if self.config.inc_organizer is True:
            self._organizer = OrganizerWindow(master=self.frame)
            self._organizer.pack(side=LEFT, fill=Y)

        if self._config.inc_log_window is True:
            self._log_window = LogWindow(self.frame)
            self._log_window.pack(side=BOTTOM, fill=X)
            self._log_handler.set_callback(self.log)

        if self._config.inc_workspace is True:
            self._workspace = PyroxFrame(self.frame, text='Workspace')
            self._workspace.pack(side=TOP, fill=BOTH, expand=True)

    def clear_workspace(self) -> None:
        """Clear workspace of all children.

        """
        for child in self.workspace.winfo_children():
            child.pack_forget()

    def log(self,
            message: str):
        """Post a message to this :class:`Application`'s logger frame.

        Arguments
        ----------
        message: :type:`str`
            Message to be sent to this :class:`Application`'s log frame.
        """
        if not self._log_window or not self._log_window.log_text:
            return

        try:
            self._log_window.log_text.config(state='normal')
            self._log_window.log_text.insert(END, f'{message}\n')
            self._log_window.log_text.see(END)
            self._log_window.log_text.config(state='disabled')
        except TclError as e:
            print('Tcl error, original msg -> %s' % e)

        self._log_window.update()

    def set_model(self,
                  model: Model) -> None:
        """Set a new model for this :class:`Application`.

        Will trigger a `build` event if a model is given (Not `None`).

        .. ------------------------------------------------------------

        Arguments
        -----------

        model: :class:`Model`
            Model to set as application main model.


        """
        # undo packing for all child widgets. This will allow us to rebuild a model in our frame
        self.clear_workspace()
        if not model:
            self.logger.warning('No model given, cannot set model for application')
            return

        self._main_model_id = self.add_model(model).id
        self.model_hash[self._main_model_id].build()
