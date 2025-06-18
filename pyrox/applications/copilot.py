from __future__ import annotations


from tkinter import LabelFrame, BOTH, TOP


from pyrox import Model, ViewModel, View


class CopilotConnectionView(View):
    def __init__(self, view_model=None, config=...):
        super().__init__(view_model, config)

    def build(self):

        self.clear()
        self.my_frame = LabelFrame(self.parent, text='Microsoft Copilot Connection Setup')
        self.my_frame.pack(fill=BOTH, side=TOP, expand=True)
        super().build()


class CopilotConnectionViewModel(ViewModel):
    def __init__(self, model=None, view=None):
        super().__init__(model, view)


class CopilotConnectionModel(Model):
    def __init__(self, app=None, view_model=None):
        super().__init__(app, view_model)
