"""Splash screen widget for Pyrox applications."""
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QColor, QPainter, QFont, QPen
from PyQt6.QtWidgets import QWidget, QApplication

from pyrox.models.gui.theme import DefaultTheme

__all__ = ('SplashScreen',)

_ACCENT_COLOR = '#0078d4'
_WIDTH = 520
_HEIGHT = 290


class SplashScreen(QWidget):
    """Frameless splash screen shown during application startup.

    Show this widget immediately after *QApplication* is created, call
    :py:meth:`set_status` as each loading phase completes, then call
    :py:meth:`close_splash` when the main window is ready to appear.
    """

    def __init__(self, app_name: str = '', app_description: str = '') -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._app_name = app_name
        self._app_description = app_description
        self._status = 'Initializing'
        self._dot_count = 0
        self._theme = DefaultTheme()

        self.setFixedSize(_WIDTH, _HEIGHT)
        self._center_on_screen()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(400)

        self.show()
        QApplication.processEvents()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_status(self, message: str) -> None:
        """Update the status message and force a repaint.

        Args:
            message: Short phrase describing the current loading step.
        """
        self._status = message
        self._dot_count = 0
        self.update()
        QApplication.processEvents()

    def close_splash(self) -> None:
        """Stop animation and close the splash window."""
        self._timer.stop()
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            self.move(
                (geo.width() - _WIDTH) // 2,
                (geo.height() - _HEIGHT) // 2,
            )

    def _tick(self) -> None:
        self._dot_count = (self._dot_count + 1) % 4
        self.update()

    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def paintEvent(self, _event) -> None:  # type: ignore[override]
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = self._theme

        # Background
        p.fillRect(self.rect(), QColor(theme.widget_background))

        # Outer border
        p.setPen(QPen(QColor('#3c3c3c'), 1))
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Top accent bar
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(_ACCENT_COLOR))
        p.drawRect(QRect(0, 0, _WIDTH, 4))

        # App name
        name_font = QFont(theme.font_family, 20, QFont.Weight.Bold)
        p.setFont(name_font)
        p.setPen(QColor(theme.foreground_selected))
        p.drawText(
            QRect(40, 28, _WIDTH - 80, 52),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._app_name,
        )

        # Description
        desc_font = QFont(theme.font_family, 9)
        p.setFont(desc_font)
        p.setPen(QColor(theme.foreground))
        p.drawText(
            QRect(40, 84, _WIDTH - 80, 28),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._app_description,
        )

        # Horizontal divider
        p.setPen(QPen(QColor('#3c3c3c'), 1))
        p.drawLine(40, 124, _WIDTH - 40, 124)

        # Status message with animated ellipsis
        status_font = QFont(theme.font_family, 9)
        p.setFont(status_font)
        p.setPen(QColor(_ACCENT_COLOR))
        p.drawText(
            QRect(40, 148, _WIDTH - 80, 30),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f'{self._status}{"." * self._dot_count}',
        )

        # Footer
        footer_font = QFont(theme.font_family, 8)
        p.setFont(footer_font)
        p.setPen(QColor('#555555'))
        p.drawText(
            QRect(40, _HEIGHT - 38, _WIDTH - 80, 20),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            'Powered by Pyrox',
        )

        p.end()
