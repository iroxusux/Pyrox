"""GUI window base class built-in implimentations.
"""
from tkinter import Toplevel, Tk, Widget
from typing import Tuple, Union
from pyrox.models.gui.default import GuiWindow
from .widget import TkinterGuiWidget


class TkinterGuiWindow(
    TkinterGuiWidget,
    GuiWindow[Union[Tk, Toplevel], Widget],
):
    """Tkinter implementation of IGuiWindow.
    """

    def center_on_screen(self) -> None:
        self.update()
        self.root.geometry(f'{self.width}x{self.height}+{self.x}+{self.y}')

    def close(self) -> None:
        self.destroy()

    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def get_size(self) -> Tuple[int, int]:
        return (self.width, self.height)

    def get_width(self) -> int:
        return self.root.winfo_width()

    def get_state(self) -> str:
        return self.root.state()

    def get_title(self) -> str:
        return self.root.title()

    def initialize(
        self,
        as_root: bool = False,
        **kwargs
    ) -> bool:

        if as_root:
            self.root = Tk(**kwargs)
        else:
            self.root = Toplevel(**kwargs)

        return True

    def is_fullscreen(self) -> bool:
        return bool(self.root.attributes('-fullscreen'))

    def set_fullscreen(self, fullscreen: bool) -> None:
        self.root.attributes('-fullscreen', fullscreen)

    def set_geometry(
        self,
        width: int,
        height: int,
        x: int | None = None,
        y: int | None = None
    ) -> None:
        if x is not None and y is not None:
            self.root.geometry(f'{width}x{height}+{x}+{y}')
        else:
            self.root.geometry(f'{width}x{height}')

    def set_icon(self, icon_path: str) -> None:
        self.root.iconbitmap(icon_path)

    def set_position(self, x: int, y: int) -> None:
        self.root.geometry(f'{self.width}x{self.height}+{x}+{y}')

    def set_resizable(self, resizable: bool) -> None:
        self.root.resizable(resizable, resizable)

    def set_size(self, width: int, height: int) -> None:
        self.root.geometry(f'{width}x{height}')

    def set_state(self, state: str) -> None:
        self.root.state(state)

    def set_title(self, title: str) -> None:
        self.root.title(title)

    def update(self) -> None:
        self.root.update_idletasks()


if __name__ == '__main__':
    # Simple test
    window = TkinterGuiWindow()
    window.initialize(as_root=True)
    window.set_title('Test Window')
    window.set_geometry(400, 300, 100, 100)
    window.center_on_screen()
    window.root.mainloop()
