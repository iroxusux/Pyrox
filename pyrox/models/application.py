"""pyrox application
    """
from __future__ import annotations


from typing import Optional, Union


from tkinter import (
    BOTTOM,
    END,
    LabelFrame,
    LEFT,
    PanedWindow,
    TOP,
    Menu,
    TclError,
    Tk,
    Toplevel,
)


from .abc import (
    PartialApplication,
    PartialApplicationTask,
    BaseMenu,
    ApplicationConfiguration,
    HashList,
    SnowFlake
)

from .plc import Controller
from .utkinter.frames import LogWindow, FrameWithTreeViewAndScrollbar, PyroxFrame


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
                 application: 'Application'):
        super().__init__(application=application)

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
                 config: ApplicationConfiguration = None):
        super().__init__(config=config)

        self._log_window = None
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
    def organizer(self) -> Optional[FrameWithTreeViewAndScrollbar]:
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

    def add_task(self,
                 task: Union[ApplicationTask, type[ApplicationTask]]) -> Optional[ApplicationTask]:
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
            tsk = task(self)
            self._tasks.append(tsk)
            tsk.inject()
            return tsk

        return None

    def add_tasks(self,
                  tasks: Union[list[ApplicationTask], list[type[ApplicationTask]]]) -> Optional[ApplicationTask]:
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

        _ = [self.add_task(x) for x in tasks]

    def build(self):
        """Build this :class:`Application`.

        This method will build the main menu, organizer window, log window and workspace if they are enabled in the configuration.

        """
        super().build()

        if not self.tk_app:
            self.logger.error('Cannot build application, no application root found')
            return

        self._tasks: HashList[PartialApplicationTask] = HashList('id')
        self._menu = None if self.config.headless is True else MainApplicationMenu(self.tk_app)
        self._model_hash = HashList(SnowFlake.id.__name__)
        self._paned_window = PanedWindow(self.frame, orient='horizontal')

        if self.config.inc_organizer is True:
            self._organizer = FrameWithTreeViewAndScrollbar(master=self._paned_window, text='Organizer')
            self._organizer.pack(side=LEFT, fill='y')
            self._paned_window.add(self._organizer)

        # use an additional sub frame to pack widgets on left side of screen neatly
        sub_frame = PanedWindow(self._paned_window, orient='vertical')

        if self._config.inc_workspace is True:
            self._workspace = PyroxFrame(sub_frame, text='Workspace')
            self._workspace.pack(side=TOP, fill='x')
            sub_frame.add(self._workspace)

        if self._config.inc_log_window is True:
            self._log_window = LogWindow(sub_frame)
            self._log_window.pack(side=BOTTOM, fill='x')
            self._log_handler.set_callback(self.log)
            sub_frame.add(self._log_window)

        sub_frame.pack(fill='both', expand=True)
        sub_frame.configure(sashrelief='groove', sashwidth=5, sashpad=5)

        self._paned_window.add(sub_frame)
        self._paned_window.pack(fill='both', expand=True)
        self._paned_window.configure(sashrelief='groove', sashwidth=5, sashpad=5)

    def clear_organizer(self) -> None:
        """Clear organizer of all children.

        This method will remove all children from the organizer window, if it exists.

        """
        if not self.organizer:
            return

        self.organizer.tree.delete(*self.organizer.tree.get_children())

    def clear_workspace(self) -> None:
        """Clear workspace of all children.
        """
        if not self.workspace:
            return

        for child in self.workspace.winfo_children():
            child.pack_forget()

    def create_controller(self) -> Optional[Controller]:
        """Create a new :class:`Controller` instance for this :class:`Application`."""
        self.logger.info('Creating new controller instance...')
        ctrl = Controller()
        return ctrl

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
