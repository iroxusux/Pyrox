import tkinter as tk
from pyrox.models.gui import TaskFrame, FrameWithTreeViewAndScrollbar


class PlcIoFrame(TaskFrame):
    """Connection view for PLC i/o.
    """

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(
            parent,
            name='PLC I/O',
        )

        self.plccfgframe = tk.LabelFrame(self.content_frame, text='PLC Connection Configuration')
        self.plccfgframe.pack(side=tk.TOP, fill=tk.X)

        self.status_canvas = tk.Canvas(self.plccfgframe, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side=tk.LEFT, padx=8)
        self.status_led = self.status_canvas.create_oval(4, 4, 16, 16, fill="grey", outline="black")

        ctrl_ip_addr = tk.StringVar(self.plccfgframe, '', 'PLC IP Address')
        self.ip_addr_entry = tk.Entry(self.plccfgframe, textvariable=ctrl_ip_addr)
        self.ip_addr_entry.pack(side=tk.LEFT)

        ctrl_slot = tk.StringVar(self.plccfgframe, '', 'PLC Slot Number')
        self.slot_entry = tk.Entry(self.plccfgframe, textvariable=ctrl_slot)
        self.slot_entry.pack(side=tk.LEFT)

        self.connect_pb = tk.Button(self.plccfgframe, text='Connect')
        self.connect_pb.pack(side=tk.LEFT, fill=tk.X)

        self.disconnect_pb = tk.Button(self.plccfgframe, text='Disconnect')
        self.disconnect_pb.pack(side=tk.LEFT, fill=tk.X)

        self.plccmdframe = tk.LabelFrame(self.content_frame, text='PLC Commands')
        self.plccmdframe.pack(side=tk.TOP, fill=tk.X)

        self.gettags_pb = tk.Button(self.plccmdframe, text='Read Tags')
        self.gettags_pb.pack(side=tk.LEFT, fill=tk.X)

        self.watchtable_pb = tk.Button(self.plccmdframe, text='Watch Table')
        self.watchtable_pb.pack(side=tk.LEFT, fill=tk.X)

        self.tags_frame = FrameWithTreeViewAndScrollbar(self.content_frame)
        self.tags_frame.pack(side=tk.TOP, fill='both', expand=True)

    def on_connect_pb_clicked(self, callback) -> None:
        self.connect_pb.config(command=callback)

    def on_disconnect_pb_clicked(self, callback) -> None:
        self.disconnect_pb.config(command=callback)
