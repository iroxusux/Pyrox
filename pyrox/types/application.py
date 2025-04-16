"""pyrox application
    """
from __future__ import annotations


from typing import Optional, Union


from tkinter import Menu, Tk, Toplevel, Event


from .abc import PartialApplication, ApplicationTask
from .abc import BaseMenu, Model, PartialApplicationConfiguration
from .hashlist import HashList


__all__ = (
    'MainApplicationMenu',
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
        self._edit: Menu = Menu(self.menu, name='edit', tearoff=0)
        self._file: Menu = Menu(self.menu, name='file', tearoff=0)
        self._help: Menu = Menu(self.menu, name='help', tearoff=0)
        self._tools: Menu = Menu(self.menu, name='tools', tearoff=0)
        self._view: Menu = Menu(self.menu, name='view', tearoff=0)

        self.menu.add_cascade(label='Edit', menu=self.edit)
        self.menu.add_cascade(label='File', menu=self.file)
        self.menu.add_cascade(label='Help', menu=self.help)
        self.menu.add_cascade(label='Tools', menu=self.tools)
        self.menu.add_cascade(label='View', menu=self.view)

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


class Application(PartialApplication):
    """Represents a :class:`PartialApplication` in the form of an Application.

    .. ------------------------------------------------------------

    Arguments
    -----------

    config: Optional[:class:`PartialApplicationConfiguration`]
        Configuration for this partial application.

    model: Optional[:class:`Model`]
        Optional model to build application with.

    Attributes
    -----------
    menu: :class:`MainApplicationMenu`
        Main Tk :class:`Menu` for this :class:`Application`.

    tasks: :class:`HashList` [:class:`ApplicationTask`]
        Hashed list of tasks for this :class:`Application`.


    """

    def __init__(self,
                 model: Optional[Model],
                 config: Optional[PartialApplicationConfiguration]):
        super().__init__(model=model,
                         config=config)
        self._menu = MainApplicationMenu(self.parent)
        self._tasks: HashList[ApplicationTask] = HashList('id')
        self.frame.grid(column=0, row=0, sticky=('n', 'e', 's', 'w'))

        self.parent.columnconfigure(0, weight=1)
        self.parent.rowconfigure(0, weight=1)

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
    def tasks(self) -> HashList[ApplicationTask]:
        """Hashed list of tasks for this :class:`PartialApplication`.

        .. ------------------------------------------------------------

        Returns
        --------
            tasks: :class:`HashList` [:class:`ApplicationTask`]
        """
        return self._tasks

    def set_model(self,
                  model: Model):
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
        if model is not None and not isinstance(model, Model):
            raise TypeError(f'Model must be of type `Model`, not {type(model)}...')

        self._model = model

        if self.model:
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
