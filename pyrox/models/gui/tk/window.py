"""GUI window base class built-in implimentations.
"""
from tkinter import Toplevel, Tk
from typing import List, Tuple, Union
from pyrox.interfaces import IGuiWindow, IGuiWidget
from pyrox.services import GuiManager
from pyrox.models.gui.tk.frame import TkinterGuiFrame
from pyrox.models.gui.tk.widget import TkinterGuiWidget


class TkinterGuiWindow(IGuiWindow, TkinterGuiFrame):
    """Tkinter implementation of IGuiWindow.
    """

    def __init__(self):
        TkinterGuiFrame.__init__(self)

    @property
    def window(self) -> Union[Tk, Toplevel]:
        if not self._widget:
            raise RuntimeError("Window not initialized")
        return self._widget

    @window.setter
    def window(self, value: Union[Tk, Toplevel]) -> None:
        if not isinstance(value, (Tk, Toplevel)):
            raise TypeError(f'Expected tkinter.Tk or tkinter.Toplevel, got {type(value)}')
        self._widget = value

    def add_child(self, child: IGuiWidget) -> None:
        child_parent = child.get_parent()
        if child_parent:
            raise RuntimeError('Child widget already has a parent assigned.')

        child.set_parent(self)
        if not child.widget:
            raise RuntimeError('Child widget is not initialized.')

        child.widget.master = self.window
        child.widget.pack()

    def center_on_screen(self) -> None:
        self.update()
        width = self.get_width()
        height = self.get_height()
        x = self.get_x()
        y = self.get_y()
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def clear_children(self) -> None:
        for child in self.window.winfo_children():
            child.destroy()

    def close(self) -> None:
        self.destroy()

    def destroy(self) -> None:
        self.window.destroy()
        self._widget = None

    def get_children(self) -> List[IGuiWidget]:
        children_widgets = []
        for child in self.window.winfo_children():
            gui_widget = TkinterGuiWidget()
            gui_widget.widget = child
            children_widgets.append(gui_widget)
        return children_widgets

    def get_height(self) -> int:
        return self.window.winfo_height()

    def get_position(self) -> Tuple[int, int]:
        return (self.window.winfo_x(), self.window.winfo_y())

    def get_size(self) -> Tuple[int, int]:
        return (self.window.winfo_width(), self.window.winfo_height())

    def get_width(self) -> int:
        return self.window.winfo_width()

    def get_state(self) -> str:
        return self.window.state()

    def get_title(self) -> str:
        return self.window.title()

    def initialize(
        self,
        as_root: bool = False,
        **kwargs
    ) -> bool:
        backend = GuiManager.get_backend()
        if not backend or not backend.is_available():
            raise RuntimeError('GUI backend is not available.')

        if backend.framework_name.lower() != 'tkinter':
            raise RuntimeError(f'Incompatible GUI backend: {backend.framework_name}')

        tk = backend.get_backend()

        if as_root:
            if not hasattr(tk, 'Tk'):
                raise RuntimeError('Tkinter backend does not support root windows.')
            self._widget = tk.Tk(**kwargs)
        else:
            if not hasattr(tk, 'Toplevel'):
                raise RuntimeError('Tkinter backend does not support toplevel windows.')
            self._widget = tk.Toplevel(**kwargs)

        return True

    def is_fullscreen(self) -> bool:
        return bool(self.window.attributes('-fullscreen'))

    def remove_child(self, child: IGuiWidget) -> None:
        child_parent = child.get_parent()
        if child_parent != self:
            raise RuntimeError('Child widget is not a child of this window.')

        child.widget.destroy()
        child.set_parent(None)

    def set_fullscreen(self, fullscreen: bool) -> None:
        self.window.attributes('-fullscreen', fullscreen)

    def set_geometry(
        self,
        width: int,
        height: int,
        x: int | None = None,
        y: int | None = None
    ) -> None:
        if x is not None and y is not None:
            self.window.geometry(f'{width}x{height}+{x}+{y}')
        else:
            self.window.geometry(f'{width}x{height}')

    def set_icon(self, icon_path: str) -> None:
        self.window.iconbitmap(icon_path)

    def set_position(self, x: int, y: int) -> None:
        width = self.get_width()
        height = self.get_height()
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def set_resizable(self, resizable: bool) -> None:
        self.window.resizable(resizable, resizable)

    def set_size(self, width: int, height: int) -> None:
        self.window.geometry(f'{width}x{height}')

    def set_state(self, state: str) -> None:
        self.window.state(state)

    def set_title(self, title: str) -> None:
        self.window.title(title)

    def update(self) -> None:
        self.window.update_idletasks()


if __name__ == '__main__':
    # Simple test
    window = TkinterGuiWindow()
    window.initialize(as_root=True)
    window.set_title('Test Window')
    window.set_geometry(400, 300, 100, 100)
    window.center_on_screen()
    window.window.mainloop()
