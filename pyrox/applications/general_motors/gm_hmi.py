"""Main emulation model
    """
from __future__ import annotations


from enum import Enum

from tkinter import BOTH, Button, DISABLED, Entry, Frame, Label, LabelFrame, LEFT, StringVar, TOP, W, X
from tkinter.font import Font
from typing import Callable, Optional, TYPE_CHECKING


from pylogix.lgx_response import Response
from ..connection import ConnectionCommand, ConnectionCommandType, ConnectionTask
from ...services.notify_services import notify_warning
from ...models import (
    Application,
    ApplicationTask,
    LaunchableModel,
    ViewConfiguration,
    View,
    ViewModel,
    ViewType
)
from ...utils import read_bit, set_bit, clear_bit


if TYPE_CHECKING:
    from ..connection import ConnectionModel


CIPTypes = {0x00: (1, "UNKNOWN", '<B'),
            0xa0: (88, "STRUCT", '<B'),
            0xc0: (8, "DT", '<Q'),
            0xc1: (1, "BOOL", '<?'),
            0xc2: (1, "SINT", '<b'),
            0xc3: (2, "INT", '<h'),
            0xc4: (4, "DINT", '<i'),
            0xc5: (8, "LINT", '<q'),
            0xc6: (1, "USINT", '<B'),
            0xc7: (2, "UINT", '<H'),
            0xc8: (4, "UDINT", '<I'),
            0xc9: (8, "LWORD", '<Q'),
            0xca: (4, "REAL", '<f'),
            0xcc: (8, "LDT", '<Q'),
            0xcb: (8, "LREAL", '<d'),
            0xd0: (1, "O_STRING", '<B'),
            0xd1: (1, "BYTE", "<B"),
            0xd2: (2, "WORD", "<I"),
            0xd3: (4, "DWORD", '<i'),
            0xd6: (4, "TIME32", '<I'),
            0xd7: (8, "TIME", '<Q'),
            0xda: (1, "STRING", '<B'),
            0xdf: (8, "LTIME", '<Q')}


class _HmiSlotInputAttr(Enum):
    AUTO_PB = 0
    SPARE01 = 1
    SPARE02 = 2
    DO_PB = 3
    UNDO_PB = 4
    SPARE05 = 5
    SPARE06 = 6
    SPARE07 = 7


class _HmiSlotOutputAttr(Enum):
    SPARE00 = 0
    AUTO_LT = 1
    RESET_LT = 2
    SPARE03 = 3
    SPARE04 = 4
    SPARE05 = 5
    SPARE06 = 6
    FAULT_LT = 7


class GmHmiView(View):
    """General Motors Human-Machine Interface View

    """

    def __init__(self,
                 view_model: Optional['GmHmiViewModel'] = None,
                 config: ViewConfiguration = ViewConfiguration()):
        super().__init__(view_model=view_model,
                         config=config)

        self._title: str = config.title
        self._std_input_entry: Optional[Entry] = None
        self._std_output_entry: Optional[Entry] = None
        self._saf_input_entry: Optional[Entry] = None
        self._saf_output_entry: Optional[Entry] = None

        self._flt_lt_Label: Optional[Label] = None

        # ----------------------- button row 1 -------------------------- #

        self._auto_init_pb: Button = None
        self._spare_row1_pb2: Button = None
        self._spare_row1_pb3: Button = None
        self._reset_pb: Button = None

        # ----------------------- button row 2 -------------------------- #

        self._mode_sel_pb: Button = None
        self._spare_row2_pb2: Button = None
        self._spare_row2_pb3: Button = None
        self._spare_row2_pb4: Button = None

        # ----------------------- button row 3 -------------------------- #

        self._enable_pb: Button = None
        self._do_pb: Button = None
        self._undo_pb: Button = None
        self._spare_row4_pb4: Button = None

    @property
    def auto_init_pb(self) -> Button:
        return self._auto_init_pb

    @property
    def enable_pb(self) -> Button:
        return self._enable_pb

    @property
    def fault_lt_lbl(self) -> Label:
        return self._flt_lt_Label

    @property
    def mode_sel_pb(self) -> Button:
        return self._mode_sel_pb

    @property
    def do_pb(self) -> Button:
        return self._do_pb

    @property
    def undo_pb(self) -> Button:
        return self._undo_pb

    @property
    def reset_pb(self) -> Button:
        return self._reset_pb

    @property
    def safe_input_entry(self) -> Entry:
        return self._saf_input_entry

    @property
    def safe_output_entry(self) -> Entry:
        return self._saf_output_entry

    @property
    def std_input_entry(self) -> Entry:
        return self._std_input_entry

    @property
    def std_output_entry(self) -> Entry:
        return self._std_output_entry

    def build(self):

        lblfrm = LabelFrame(self.frame,
                            text=f'General Motors ECS5022 @{self._title}',
                            padx=5,
                            pady=5)
        lblfrm.pack(side=TOP, fill=BOTH, expand=True)

        # ----------------------- I/O Tag Inputs -------------------------- #

        io_frm = LabelFrame(lblfrm,
                            text='IO Tags',
                            padx=5,
                            pady=5)
        io_frm.pack(side=TOP)

        # std io

        _std_io_frm = LabelFrame(io_frm, text='Standard I/O', padx=5, pady=5)
        _std_io_frm.pack(side=TOP)

        # inputs

        _std_i_frm = Frame(_std_io_frm, padx=5)
        _std_i_frm.pack(side=TOP)

        _std_i_txt = Label(_std_i_frm, text='Inputs', padx=5, width=-20, anchor=W)
        _std_i_txt.pack(side=LEFT)

        _std_input = StringVar(_std_i_frm, 'sz_GDR05D1:2:I.Data')
        self._std_input_entry = Entry(_std_i_frm, textvariable=_std_input)
        self._std_input_entry.pack(side=LEFT)

        # outputs

        _std_o_frm = Frame(_std_io_frm, padx=5)
        _std_o_frm.pack(side=TOP)

        _std_o_txt = Label(_std_o_frm, text='Outputs', padx=5, width=-20, anchor=W)
        _std_o_txt.pack(side=LEFT)

        _std_output = StringVar(_std_o_frm, 'sz_GDR05D1:2:O.Data')
        self._std_output_entry = Entry(_std_o_frm, textvariable=_std_output)
        self._std_output_entry.pack(side=LEFT)

        # safe io

        _saf_io_frm = LabelFrame(io_frm, text='Safe I/O', padx=5, pady=5)
        _saf_io_frm.pack(side=TOP)

        # inputs

        _saf_i_frm = Frame(_saf_io_frm, padx=5)
        _saf_i_frm.pack(side=TOP)

        _saf_i_txt = Label(_saf_i_frm, text='s_Inputs', padx=5, width=-20, anchor=W)
        _saf_i_txt.pack(side=LEFT)

        _saf_input = StringVar(_saf_i_frm, 'sz_GDR05D1:1:I')
        self._saf_input_entry = Entry(_saf_i_frm, textvariable=_saf_input)
        self._saf_input_entry.pack(side=LEFT)

        # outputs

        _saf_o_frm = Frame(_saf_io_frm, padx=5)
        _saf_o_frm.pack(side=TOP)

        _saf_o_txt = Label(_saf_o_frm, text='s_Outputs', padx=5, width=-20, anchor=W)
        _saf_o_txt.pack(side=LEFT)

        _saf_output = StringVar(_saf_o_frm, 'sz_GDR05D1:1:O')
        self._saf_output_entry = Entry(_saf_o_frm, textvariable=_saf_output)
        self._saf_output_entry.pack(side=LEFT)

        _flt = StringVar(lblfrm, 'FLT')
        self._flt_lt_Label = Label(lblfrm,
                                   height=-5,
                                   width=-5,
                                   textvariable=_flt,
                                   relief='solid',
                                   borderwidth=1,
                                   padx=5,
                                   pady=5)
        self._flt_lt_Label.pack(side=TOP)

        hmi_scn = Frame(lblfrm,
                        height=300,
                        width=400,
                        relief="solid",
                        borderwidth=1,
                        padx=5,
                        pady=5)
        hmi_scn.pack(side=TOP, fill=X, expand=True)

        hmi_txt = Label(hmi_scn,
                        text='HMI SCREEN',
                        font=Font(family='Helvetica', size=20, weight='bold'),
                        padx=5,
                        pady=5)
        hmi_txt.pack(side=TOP, fill=BOTH, expand=True)

        # ----------------------- button row 1 -------------------------- #

        btn_row1 = LabelFrame(lblfrm,
                              text='Button Row 1',
                              height=75,
                              width=400,
                              relief="solid",
                              borderwidth=1,
                              padx=5,
                              pady=5)
        btn_row1.pack(side=TOP, fill=BOTH, expand=True)

        btn_row1_sub = Frame(btn_row1)
        btn_row1_sub.pack(side=TOP, fill=BOTH, expand=True)

        self._auto_init_pb = Button(btn_row1_sub, text='Auto Initiate', width=-10, padx=5)
        self._auto_init_pb.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row1_pb1 = Button(btn_row1_sub, text='Spare01', width=-10, padx=5, state=DISABLED)
        spare_row1_pb1.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row1_pb2 = Button(btn_row1_sub, text='Spare02', width=-10, padx=5, state=DISABLED)
        spare_row1_pb2.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row1_pb3 = Button(btn_row1_sub, text='Spare03', width=-10, padx=5, state=DISABLED)
        spare_row1_pb3.pack(side=LEFT, fill=BOTH, expand=True)

        self._reset_pb = Button(btn_row1_sub, text='Reset', width=-10, padx=5)
        self._reset_pb.pack(side=LEFT, fill=BOTH, expand=True)

        # ----------------------- button row 2 -------------------------- #

        btn_row2 = LabelFrame(lblfrm,
                              text='Button Row 2',
                              height=75,
                              width=400,
                              relief="solid",
                              borderwidth=1,
                              padx=5,
                              pady=5)
        btn_row2.pack(side=TOP, fill=BOTH, expand=True)

        btn_row2_sub = Frame(btn_row2)
        btn_row2_sub.pack(side=TOP, fill=BOTH, expand=True)

        self._mode_sel_pb = Button(btn_row2_sub, text='Mode Select', width=-10)
        self._mode_sel_pb.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row2_pb1 = Button(btn_row2_sub, text='Spare01', width=-10, state=DISABLED)
        spare_row2_pb1.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row2_pb2 = Button(btn_row2_sub, text='Spare02', width=-10, state=DISABLED)
        spare_row2_pb2.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row2_pb3 = Button(btn_row2_sub, text='Spare03', width=-10, state=DISABLED)
        spare_row2_pb3.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row2_pb4 = Button(btn_row2_sub, text='Spare04', width=-10, state=DISABLED)
        spare_row2_pb4.pack(side=LEFT, fill=BOTH, expand=True)

        # ----------------------- button row 3 -------------------------- #

        btn_row3 = LabelFrame(lblfrm,
                              text='Button Row 3',
                              height=75,
                              width=400,
                              relief="solid",
                              borderwidth=1,
                              padx=5,
                              pady=5)
        btn_row3.pack(side=TOP, fill=BOTH, expand=True)

        btn_row3_sub = Frame(btn_row3)
        btn_row3_sub.pack(side=TOP, fill=BOTH, expand=True)

        self._enable_pb = Button(btn_row3_sub, text='Enable', width=-10)
        self._enable_pb.pack(side=LEFT, fill=BOTH, expand=True)

        self._do_pb = Button(btn_row3_sub, text='Do', width=-10)
        self._do_pb.pack(side=LEFT, fill=BOTH, expand=True)

        self._undo_pb = Button(btn_row3_sub, text='Undo', width=-10)
        self._undo_pb.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row3_pb3 = Button(btn_row3_sub, text='Spare03', width=-10, state=DISABLED)
        spare_row3_pb3.pack(side=LEFT, fill=BOTH, expand=True)

        spare_row4_pb4 = Button(btn_row3_sub, text='Spare04', width=-10, state=DISABLED)
        spare_row4_pb4.pack(side=LEFT, fill=BOTH, expand=True)


class GmHmiViewModel(ViewModel):
    """General Motors Human-Machine Interface View Model

    """

    @property
    def model(self) -> 'GmHmiModel':
        return self._model

    @property
    def view(self) -> GmHmiView:
        return self._view

    def _on_read(self,
                 output_status: int):
        if not self.model._connection_model.running:
            return

        self.logger.info('HMI Output Status -> %s', output_status)

        if read_bit(output_status, _HmiSlotOutputAttr.FAULT_LT.value):
            self.view.fault_lt_lbl.config(background='red')
        else:
            self.view.fault_lt_lbl.config(background='grey')

        if read_bit(output_status, _HmiSlotOutputAttr.AUTO_LT.value):
            self.view.auto_init_pb.config(background='light green', activebackground='light green')
        else:
            self.view.auto_init_pb.config(background='dark green', activebackground='dark green')

        if read_bit(output_status, _HmiSlotOutputAttr.RESET_LT.value):
            self.view.reset_pb.config(background='light blue', activebackground='light blue')
        else:
            self.view.reset_pb.config(background='dark blue', activebackground='dark blue')

    def _on_clear_bit(self, bit_position: int):
        self.model._std_input_value = clear_bit(self.model._std_input_value, bit_position)

    def _on_set_bit(self, bit_position: int):
        self.model._std_input_value = set_bit(self.model._std_input_value, bit_position)

    def build(self):
        super().build()

        self.model.on_read.append(self._on_read)

        self.view.auto_init_pb.bind('<ButtonPress-1>', lambda _: self._on_set_bit(_HmiSlotInputAttr.AUTO_PB.value))
        self.view.auto_init_pb.bind(
            '<ButtonRelease-1>', lambda _: self._on_clear_bit(_HmiSlotInputAttr.AUTO_PB.value))

        self.view.do_pb.bind('<ButtonPress-1>', lambda _: self._on_set_bit(_HmiSlotInputAttr.DO_PB.value))
        self.view.do_pb.bind('<ButtonRelease-1>', lambda _: self._on_clear_bit(_HmiSlotInputAttr.DO_PB.value))

        self.view.undo_pb.bind('<ButtonPress-1>', lambda _: self._on_set_bit(_HmiSlotInputAttr.UNDO_PB.value))
        self.view.undo_pb.bind('<ButtonRelease-1>', lambda _: self._on_clear_bit(_HmiSlotInputAttr.UNDO_PB.value))


class GmHmiModel(LaunchableModel):
    """General Motors Human-Machine Interface Model.

    .. ------------------------------------------------------------

    Attributes
    -----------
    controller: :class:`Controller`
        Main controller for the emulation application.

    """

    def __init__(self,
                 app: Application,
                 connection_model: ConnectionModel):
        super().__init__(application=app,
                         view_model=GmHmiViewModel,
                         view=GmHmiView,
                         view_config=ViewConfiguration(title='Gm HMI Emulate',
                                                       parent=app.view.frame,
                                                       type_=ViewType.TOPLEVEL))

        if not connection_model:
            raise RuntimeError('Must have a connection model to continue!')

        self._connection_model: ConnectionModel = connection_model

        self._std_input_value = 0
        self._last_std_input_value = 0
        self._std_output_value = 0
        self._last_std_output_value = 0

        self._saf_output_value = 0
        self._last_saf_output_value = 0
        self._saf_input_value = 0
        self._last_saf_input_value = 0

        self.on_read: list[Callable] = []

    @property
    def view_model(self) -> GmHmiViewModel:
        return self._view_model

    def _read_outputs(self,
                      response: Response):
        if self._std_output_value == response.Value or response.Value is None:
            return  # return early if there's no new data value

        self._std_output_value = response.Value
        _ = [x(self._std_output_value) for x in self.on_read]  # write to all callbacks our new value

    def _read_safe_outputs(self,
                           response: Response):
        if not response.Value:
            return
        # _card = AB_1734_IB8S_Safety5_O_0(response.Value)

    def run(self):
        if not self.running:
            return

        if self._connection_model.connected is False:
            return

        if self._last_std_input_value != self._std_input_value:
            # register a write command to the connection model
            w_cmd = ConnectionCommand(ConnectionCommandType.WRITE,
                                      self.view_model.view.std_input_entry.get(),
                                      self._std_input_value,
                                      0xc2,
                                      lambda sts: self.logger.info('Response -> %s | %s',
                                                                   sts.Status, sts.Value))
            self._connection_model.add_command(w_cmd)
            self._last_std_input_value = self._std_input_value

        # register a standard read command to the connection model
        r_cmd = ConnectionCommand(ConnectionCommandType.READ,
                                  self.view_model.view.std_output_entry.get(),
                                  self._std_output_value,
                                  0xc2,
                                  self._read_outputs)
        self._connection_model.add_command(r_cmd)

        # register a safety read command to the connection model
        r_cmd = ConnectionCommand(ConnectionCommandType.READ,
                                  self.view_model.view.safe_output_entry.get(),
                                  self._saf_output_value,
                                  None,
                                  self._read_safe_outputs)
        self._connection_model.add_command(r_cmd)


class GmHmiTask(ApplicationTask):
    """General Motors Human-Machine Interface task.
    """

    def __init__(self,
                 application: Application):
        super().__init__(application=application)

        self._connection_task = next((application.tasks.hashes[x] for x in application.tasks.hashes if isinstance(
            application.tasks.hashes[x], ConnectionTask)), None)
        if not self._connection_task:
            raise RuntimeError('Could not resolve connection task! This task is inoperable!')

    @property
    def model(self) -> 'GmHmiModel':
        return self._model

    def run(self):
        try:
            GmHmiModel(app=self.application, connection_model=self._connection_task.model).launch()
        except RuntimeError:
            notify_warning('No Connection Module Running!',
                           'You must set up a connection before launching the HMI module!')

    def inject(self) -> None:
        self.application.menu.tools.add_command(label='GM HMI Simulate', command=self.run)
