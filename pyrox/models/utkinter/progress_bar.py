"""get a progress bar. also, support updating the progress bar's value and text fields
    """
from __future__ import annotations


import tkinter
from tkinter import ttk


from ..abc import Application, ApplicationConfiguration


__all__ = (
    'ProgressBar',
)


class ProgressBar(Application):
    """A Progress Bar in the form of a :class:`PartialApplication`.

    Supports updating text and percentage complete, to show user about an ongoing process.

    .. ------------------------------------------------------------

    .. package:: types.progress_bar

    .. ------------------------------------------------------------

    Arguments
    -----------

    title: :type:`str`
        Title to show the progress bar with.

    header_text: :type:`str`
        Header text to show above progress text.


    """

    __slots__ = ('_prog_var', '_text_var')

    def __init__(self,
                 title: str,
                 header_text: str):

        config = ApplicationConfiguration.toplevel()
        config.title = title
        config.size_ = '300x100'

        super().__init__(config=config)

        self.tk_app.overrideredirect(True)

        # create header label
        lbl = tkinter.Label(self.view.frame, text=header_text)
        lbl.pack(side='top', fill='x', padx=5, pady=5)

        # create updateable file string
        self._text_var = tkinter.StringVar()
        lbl2 = tkinter.Label(self.view.frame, textvariable=self._text_var)
        lbl2.pack(side='top', fill='x', padx=5, pady=5)

        # create progress bar variable
        self._prog_var = tkinter.DoubleVar()
        prog_bar = ttk.Progressbar(self.view.frame,
                                   variable=self._prog_var,
                                   maximum=100)
        prog_bar.pack(side='top', fill='x', padx=5, pady=5)
        self.center()

    def update(self,
               text: str,
               perc_comp: float) -> None:
        """update the progress bar

        Args:
            text (str): text to display
            perc_comp (float): percent complete
        """
        self._text_var.set(text)
        self._prog_var.set(perc_comp)
        self.view.parent.focus()
        self.view.parent.update()
