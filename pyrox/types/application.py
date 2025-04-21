"""pyrox application
    """
from __future__ import annotations


from typing import Optional, TYPE_CHECKING, Union


from tkinter import Menu, Tk, Toplevel, Event


from .abc import PartialApplication, PartialApplicationTask
from .abc import BaseMenu, PartialModel, PartialApplicationConfiguration
from .abc.list import HashList
from .loggable import Loggable


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


class ApplicationTask(PartialApplicationTask, Loggable):
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

    def __init__(self,
                 application: 'Application',
                 model: Model):
        PartialApplicationTask.__init__(self,
                                        application=application,
                                        model=model)
        Loggable.__init__(self)

    @property
    def application(self) -> 'Application':
        """The parent application of this task.

        .. ------------------------------------------------------------

        Returns
        -----------
            application: :class:`Application`
        """
        return self._application

    @property
    def model(self) -> Model:
        """The model this task reflects.

        .. ------------------------------------------------------------

        Returns
        -----------
            model: :class:`Model`
        """
        return self._model


class Application(PartialApplication, Loggable):
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

    def __init__(self,
                 model: Optional[PartialModel] = None,
                 config: Optional[PartialApplicationConfiguration] = None):

        if not config:
            config = PartialApplicationConfiguration.generic_root()

        PartialApplication.__init__(self,
                                    model=model,
                                    config=config)
        Loggable.__init__(self)
        # setup running status and closing callback
        self._running: bool = False
        self._parent.protocol('WM_DELETE_WINDOW', self.on_closing)

        self._menu = MainApplicationMenu(self.parent)
        self._tasks: HashList[PartialApplicationTask] = HashList('id')
        self.frame.grid(column=0, row=0, sticky=('n', 'e', 's', 'w'))

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

        if self.main_model:
            self.build()

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
    def running(self) -> bool:
        """Running status of this :class:`Application`'s `Tk` interpreter.

        Returns
        ----------
            running: :type:`bool`
        """
        return self._running

    @property
    def tasks(self) -> HashList[PartialApplicationTask]:
        """Hashed list of tasks for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            tasks: :class:`HashList` [:class:`ApplicationTask`]
        """
        return self._tasks

    def on_closing(self) -> None:
        """method called when the tk interpreter intends on closing.
        """
        self._running = False
        self.parent.destroy()

    def on_pre_run(self) -> None:
        """Method that is called directly before calling parent Tk `mainloop`.

        By this point, all models, view models and views should be created.

        This allows some extra logic to occur before our app begins.

        .. ------------------------------------------------------------

        Note: it is recommenbed to override this method to create your own functionality.
        """

    def run(self) -> None:
        """run this main :class:`Application`.

        this hands the pointer off to tkinter mainloop.
        """
        self.on_pre_run()
        self._running = True
        self.parent.focus()
        self.parent.mainloop()

    def set_model(self,
                  model: PartialModel):
        """Set a new model for this :class:`Application`.

        Will trigger a `build` event if a model is given (Not `None`).

        .. ------------------------------------------------------------

        Arguments
        -----------

        model: :class:`Model`
            Model to set as application main model.

        .. ------------------------------------------------------------

        Raises
        -----------
        :class:`ValueError`
            Incorrect model type was passed to application


        """
        if model is not None and not isinstance(model, PartialModel):
            raise TypeError(f'Model must be of type `Model`, not {type(model)}...')

        self._model_hash.append(model)
        self._main_model_id = model.id

        if self.main_model:
            self.build()

    def toggle_fullscreen(self, event: Optional[Event] = None) -> None:
        """Toggle full-screen for this :class:`Application`.

        .. ------------------------------------------------------------

        Arguments
        -----------

        event: Optional[:class:`Event`]
            Optional key event passed to this method.

        """
        if event.keysym == 'F11':
            state = not self.parent.attributes('-fullscreen')
            self.parent.attributes('-fullscreen', state)
        elif self.parent.attributes('-fullscreen'):
            self.parent.attributes('-fullscreen', False)
