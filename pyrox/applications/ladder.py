"""Ladder logic application module.
"""
from __future__ import annotations
from typing import Optional

from .app import AppTask
from ..models import plc
from ..models.gui import ladder


class LadderEditorApplicationTask(AppTask):
    """Ladder editor application task.
    """

    def __init__(self, application):
        super().__init__(application)
        self._task_frame: Optional[ladder.LadderEditorTaskFrame] = None

    def run(self,
            routine: Optional[plc.Routine] = None,
            controller: Optional[plc.Controller] = None
            ):
        """Run the ladder editor task."""
        if not self._task_frame:
            self._task_frame = ladder.LadderEditorTaskFrame(
                master=self.application.workspace,
                controller=controller or self.application.controller,
                routine=routine
            )
        self.application.register_frame(self._task_frame, raise_=True)
