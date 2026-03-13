"""Unit tests for GuiManager in pyrox/services/gui.py."""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

from pyrox.interfaces.constants import EnvironmentKeys
from pyrox.services.gui import GuiManager, _tk_binding_to_qt_sequence
from pyrox.services.menu_registry import MenuRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_manager() -> None:
    """Reset all GuiManager class-level state between tests."""
    GuiManager._initialized = False
    GuiManager._app = None
    GuiManager._root_window = None
    GuiManager._menu_bar = None
    GuiManager._scheduled_timers = {}
    GuiManager._timer_counter = 0
    GuiManager._after_id = None


# ---------------------------------------------------------------------------
# Instantiation
# ---------------------------------------------------------------------------

class TestGuiManagerInstantiation(unittest.TestCase):
    """GuiManager is a static class — instantiation must be prevented."""

    def test_cannot_be_instantiated(self):
        """Calling GuiManager() raises TypeError."""
        with self.assertRaises(TypeError):
            GuiManager()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Root Window Management
# ---------------------------------------------------------------------------

class TestGuiManagerRootWindow(unittest.TestCase):
    """Tests for root window creation and retrieval."""

    def setUp(self):
        _reset_manager()
        MenuRegistry.clear()

    def tearDown(self):
        _reset_manager()
        MenuRegistry.clear()

    # ---- get_root ----

    def test_get_root_raises_before_initialization(self):
        """get_root() raises RuntimeError when no window exists yet."""
        with self.assertRaises(RuntimeError):
            GuiManager.get_root()

    # ---- get_app ----

    def test_get_app_raises_before_initialization(self):
        """get_app() raises RuntimeError when QApplication has not been created."""
        with self.assertRaises(RuntimeError):
            GuiManager.get_app()

    # ---- create_root ----

    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui._PyQt6MainWindow')
    @patch('pyrox.services.gui.QApplication')
    def test_create_root_returns_main_window(
        self, mock_qapp_class, mock_window_class, mock_env
    ):
        """create_root() constructs and returns a _PyQt6MainWindow instance."""
        mock_qapp_class.instance.return_value = None
        mock_window = MagicMock()
        mock_window_class.return_value = mock_window
        mock_env.get.side_effect = lambda key, default=None, cast_type=None: default

        result = GuiManager.create_root()

        mock_window_class.assert_called_once()
        self.assertIs(result, mock_window)

    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui._PyQt6MainWindow')
    @patch('pyrox.services.gui.QApplication')
    def test_create_root_is_idempotent(
        self, mock_qapp_class, mock_window_class, mock_env
    ):
        """create_root() returns the existing window on subsequent calls."""
        mock_qapp_class.instance.return_value = None
        mock_window = MagicMock()
        mock_window_class.return_value = mock_window
        mock_env.get.side_effect = lambda key, default=None, cast_type=None: default

        first = GuiManager.create_root()
        second = GuiManager.create_root()

        mock_window_class.assert_called_once()
        self.assertIs(first, second)

    @patch('pyrox.services.gui.EnvManager')
    @patch('pyrox.services.gui._PyQt6MainWindow')
    @patch('pyrox.services.gui.QApplication')
    def test_get_root_returns_created_window(
        self, mock_qapp_class, mock_window_class, mock_env
    ):
        """get_root() returns the window after create_root()."""
        mock_qapp_class.instance.return_value = None
        mock_window = MagicMock()
        mock_window_class.return_value = mock_window
        mock_env.get.side_effect = lambda key, default=None, cast_type=None: default

        GuiManager.create_root()
        result = GuiManager.get_root()

        self.assertIs(result, mock_window)

    # ---- focus / quit / run loop ----

    def _with_mock_root(self):
        """Inject a mock root and app directly. Returns (mock_root, mock_app)."""
        mock_root = MagicMock()
        mock_app = MagicMock()
        GuiManager._root_window = mock_root
        GuiManager._app = mock_app
        return mock_root, mock_app

    def test_focus_root_calls_activate_and_raise(self):
        """focus_root() calls activateWindow() and raise_() on the root window."""
        mock_root, _ = self._with_mock_root()
        GuiManager.focus_root()
        mock_root.activateWindow.assert_called_once()
        mock_root.raise_.assert_called_once()

    def test_quit_application_calls_app_quit(self):
        """quit_application() delegates to the QApplication's quit()."""
        _, mock_app = self._with_mock_root()
        GuiManager.quit_application()
        mock_app.quit.assert_called_once()

    def test_run_main_loop_calls_app_exec(self):
        """run_main_loop() calls exec() on the QApplication."""
        _, mock_app = self._with_mock_root()
        GuiManager.run_main_loop()
        mock_app.exec.assert_called_once()


# ---------------------------------------------------------------------------
# Window Title
# ---------------------------------------------------------------------------

class TestGuiManagerTitle(unittest.TestCase):
    """Tests for get_title() and set_title()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        GuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()

    def test_set_title_updates_window(self):
        """set_title() calls setWindowTitle() on the root window."""
        GuiManager.set_title("My Application")
        self.mock_root.setWindowTitle.assert_called_with("My Application")

    def test_set_title_raises_type_error_for_non_string(self):
        """set_title() raises TypeError when title is not a string."""
        for bad in (42, None, ['title'], object()):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    GuiManager.set_title(bad)  # type: ignore[arg-type]

    def test_get_title_returns_window_title(self):
        """get_title() returns the value reported by the window."""
        self.mock_root.windowTitle.return_value = "App Title"
        result = GuiManager.get_title()
        self.assertEqual(result, "App Title")

    def test_set_title_with_explicit_window(self):
        """set_title() uses the supplied window instead of root."""
        custom = MagicMock()
        GuiManager.set_title("Custom", window=custom)
        custom.setWindowTitle.assert_called_with("Custom")
        self.mock_root.setWindowTitle.assert_not_called()

    def test_get_title_with_explicit_window(self):
        """get_title() uses the supplied window instead of root."""
        custom = MagicMock()
        custom.windowTitle.return_value = "Custom Title"
        result = GuiManager.get_title(custom)
        self.assertEqual(result, "Custom Title")
        self.mock_root.windowTitle.assert_not_called()


# ---------------------------------------------------------------------------
# Window Icon
# ---------------------------------------------------------------------------

class TestGuiManagerIcon(unittest.TestCase):
    """Tests for set_icon()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        GuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()

    def test_set_icon_raises_type_error_for_non_string(self):
        """set_icon() raises TypeError when path is not a string."""
        for bad in (123, None, ['icon.ico']):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    GuiManager.set_icon(bad)  # type: ignore[arg-type]

    @patch('pyrox.services.gui.QIcon')
    def test_set_icon_on_root_window(self, mock_qicon_class):
        """set_icon() calls setWindowIcon() with a QIcon on the root window."""
        mock_icon = MagicMock()
        mock_qicon_class.return_value = mock_icon
        GuiManager.set_icon("resources/icon.ico")
        mock_qicon_class.assert_called_with("resources/icon.ico")
        self.mock_root.setWindowIcon.assert_called_with(mock_icon)

    @patch('pyrox.services.gui.QIcon')
    def test_set_icon_on_custom_window(self, mock_qicon_class):
        """set_icon() calls setWindowIcon() on a supplied window."""
        mock_icon = MagicMock()
        mock_qicon_class.return_value = mock_icon
        custom = MagicMock()
        GuiManager.set_icon("resources/icon.ico", window=custom)
        custom.setWindowIcon.assert_called_with(mock_icon)
        self.mock_root.setWindowIcon.assert_not_called()


# ---------------------------------------------------------------------------
# Event Handling
# ---------------------------------------------------------------------------

class TestGuiManagerEvents(unittest.TestCase):
    """Tests for hotkey binding, event scheduling, and protocol hooks."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        self.mock_root._configure_callbacks = []
        self.mock_root._close_callback = None
        GuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()

    # ---- bind_hotkey ----

    @patch('pyrox.services.gui.QShortcut')
    @patch('pyrox.services.gui.QKeySequence')
    def test_bind_hotkey_creates_shortcut(self, mock_key_seq_class, mock_shortcut_class):
        """bind_hotkey() creates a QShortcut bound to the root window."""
        callback = Mock()
        GuiManager.bind_hotkey('<Control-s>', callback)
        mock_shortcut_class.assert_called_once()

    @patch('pyrox.services.gui.QShortcut')
    @patch('pyrox.services.gui.QKeySequence')
    def test_bind_hotkey_connects_callback(self, mock_key_seq_class, mock_shortcut_class):
        """bind_hotkey() connects the callback to the shortcut's activated signal."""
        callback = Mock()
        mock_shortcut = MagicMock()
        mock_shortcut_class.return_value = mock_shortcut
        GuiManager.bind_hotkey('<Control-s>', callback)
        mock_shortcut.activated.connect.assert_called_once_with(callback)

    # ---- schedule / cancel ----

    @patch('pyrox.services.gui.QTimer')
    def test_schedule_event_returns_string_id(self, mock_qtimer_class):
        """schedule_event() returns a string timer ID."""
        mock_qtimer_class.return_value = MagicMock()
        result = GuiManager.schedule_event(500, Mock())
        self.assertIsInstance(result, str)

    @patch('pyrox.services.gui.QTimer')
    def test_schedule_event_starts_single_shot_timer(self, mock_qtimer_class):
        """schedule_event() creates a single-shot QTimer started with the given delay."""
        mock_timer = MagicMock()
        mock_qtimer_class.return_value = mock_timer

        GuiManager.schedule_event(500, Mock())

        mock_timer.setSingleShot.assert_called_once_with(True)
        mock_timer.start.assert_called_once_with(500)

    @patch('pyrox.services.gui.QTimer')
    def test_cancel_scheduled_event_stops_timer(self, mock_qtimer_class):
        """cancel_scheduled_event() stops and deletes the timer for the given ID."""
        mock_timer = MagicMock()
        mock_qtimer_class.return_value = mock_timer

        event_id = GuiManager.schedule_event(100, Mock())
        GuiManager.cancel_scheduled_event(event_id)

        mock_timer.stop.assert_called_once()
        mock_timer.deleteLater.assert_called_once()

    def test_cancel_nonexistent_event_is_safe(self):
        """cancel_scheduled_event() with an unknown ID does not raise."""
        GuiManager.cancel_scheduled_event('nonexistent')  # should not raise

    # ---- window event subscriptions ----

    def test_subscribe_to_window_change_event_appends_callback(self):
        """subscribe_to_window_change_event() appends the callback to _configure_callbacks."""
        callback = Mock()
        GuiManager.subscribe_to_window_change_event(callback)
        self.assertIn(callback, self.mock_root._configure_callbacks)

    def test_subscribe_to_window_change_event_does_not_replace_existing(self):
        """Multiple subscribers are accumulated in _configure_callbacks."""
        cb1, cb2 = Mock(), Mock()
        GuiManager.subscribe_to_window_change_event(cb1)
        GuiManager.subscribe_to_window_change_event(cb2)
        self.assertIn(cb1, self.mock_root._configure_callbacks)
        self.assertIn(cb2, self.mock_root._configure_callbacks)

    def test_subscribe_to_window_close_event_sets_callback(self):
        """subscribe_to_window_close_event() sets the window's _close_callback."""
        callback = Mock()
        GuiManager.subscribe_to_window_close_event(callback)
        self.assertIs(self.mock_root._close_callback, callback)

    # ---- reroute_excepthook ----

    def test_reroute_excepthook_sets_sys_excepthook(self):
        """reroute_excepthook() assigns the callback to sys.excepthook."""
        original = sys.excepthook
        callback = Mock()
        try:
            GuiManager.reroute_excepthook(callback)
            self.assertIs(sys.excepthook, callback)
        finally:
            sys.excepthook = original


# ---------------------------------------------------------------------------
# Root Menu Management
# ---------------------------------------------------------------------------

class TestGuiManagerRootMenu(unittest.TestCase):
    """Tests for root menu creation and sub-menu accessors."""

    def setUp(self):
        _reset_manager()
        MenuRegistry.clear()
        self.mock_root = MagicMock()
        self.mock_menu_bar = MagicMock()
        self.mock_root.menuBar.return_value = self.mock_menu_bar
        GuiManager._root_window = self.mock_root

    def tearDown(self):
        _reset_manager()
        MenuRegistry.clear()

    def test_create_root_menu_returns_menu_bar(self):
        """create_root_menu() retrieves and returns the QMenuBar from the root."""
        result = GuiManager.create_root_menu()
        self.mock_root.menuBar.assert_called_once()
        self.assertIs(result, self.mock_menu_bar)

    def test_create_root_menu_is_idempotent(self):
        """create_root_menu() returns the same menu bar on repeated calls."""
        first = GuiManager.create_root_menu()
        second = GuiManager.create_root_menu()
        self.mock_root.menuBar.assert_called_once()
        self.assertIs(first, second)

    def test_create_root_menu_adds_five_menus(self):
        """create_root_menu() calls addMenu() five times for the standard menus."""
        GuiManager.create_root_menu()
        self.assertEqual(self.mock_menu_bar.addMenu.call_count, 5)

    def test_create_root_menu_registers_five_submenus(self):
        """create_root_menu() registers all five standard menus in MenuRegistry."""
        GuiManager.create_root_menu()
        for menu_id in ('file_menu', 'edit_menu', 'view_menu', 'tools_menu', 'help_menu'):
            with self.subTest(menu_id=menu_id):
                self.assertIsNotNone(MenuRegistry.get_item(menu_id))

    def test_get_root_menu_raises_before_initialization(self):
        """get_root_menu() raises RuntimeError if menu has not been created."""
        with self.assertRaises(RuntimeError):
            GuiManager.get_root_menu()

    def test_get_root_menu_after_creation(self):
        """get_root_menu() returns the menu bar after create_root_menu()."""
        created = GuiManager.create_root_menu()
        self.assertIs(GuiManager.get_root_menu(), created)

    def test_submenu_accessors_raise_before_creation(self):
        """All sub-menu getters raise RuntimeError before create_root_menu()."""
        accessors = [
            GuiManager.get_file_menu,
            GuiManager.get_edit_menu,
            GuiManager.get_view_menu,
            GuiManager.get_tools_menu,
            GuiManager.get_help_menu,
        ]
        for accessor in accessors:
            with self.subTest(accessor=accessor.__name__):
                with self.assertRaises(RuntimeError):
                    accessor()

    def test_submenu_accessors_after_creation(self):
        """All sub-menu getters return valid widgets after create_root_menu()."""
        GuiManager.create_root_menu()
        for accessor in (
            GuiManager.get_file_menu,
            GuiManager.get_edit_menu,
            GuiManager.get_view_menu,
            GuiManager.get_tools_menu,
            GuiManager.get_help_menu,
        ):
            with self.subTest(accessor=accessor.__name__):
                self.assertIsNotNone(accessor())

    def test_submenus_owned_by_pyqt6_gui_manager(self):
        """All registered sub-menus are owned by 'PyQt6GuiManager'."""
        GuiManager.create_root_menu()
        items = MenuRegistry.get_items_by_owner('PyQt6GuiManager')
        self.assertEqual(len(items), 5)
        for item in items:
            with self.subTest(menu_id=item.menu_id):
                self.assertEqual(item.owner, 'PyQt6GuiManager')


# ---------------------------------------------------------------------------
# Window Geometry Save / Restore
# ---------------------------------------------------------------------------

class TestGuiManagerWindowGeometry(unittest.TestCase):
    """Tests for save_root_geometry() and restore_root_geometry()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        GuiManager._root_window = self.mock_root
        GuiManager._app = MagicMock()
        GuiManager._after_id = None

    def tearDown(self):
        _reset_manager()

    # ---- save_root_geometry ----

    @patch('pyrox.services.gui.QTimer')
    def test_save_root_geometry_schedules_delayed_event(self, mock_qtimer_class):
        """save_root_geometry() schedules a 500 ms single-shot timer."""
        mock_timer = MagicMock()
        mock_qtimer_class.return_value = mock_timer

        GuiManager.save_root_geometry()

        mock_timer.setSingleShot.assert_called_once_with(True)
        mock_timer.start.assert_called_once_with(500)
        self.assertIsNotNone(GuiManager._after_id)

    @patch('pyrox.services.gui.QTimer')
    def test_save_root_geometry_cancels_pending_event(self, mock_qtimer_class):
        """save_root_geometry() stops the previous timer before scheduling a new one."""
        mock_timer_old = MagicMock()
        mock_timer_new = MagicMock()
        mock_qtimer_class.side_effect = [mock_timer_old, mock_timer_new]

        GuiManager.save_root_geometry()
        GuiManager.save_root_geometry()

        mock_timer_old.stop.assert_called_once()

    @patch('pyrox.services.gui.QTimer')
    def test_save_root_geometry_no_cancel_when_no_pending(self, mock_qtimer_class):
        """save_root_geometry() does not stop any timer when none is pending."""
        mock_timer = MagicMock()
        mock_qtimer_class.return_value = mock_timer
        GuiManager._after_id = None

        GuiManager.save_root_geometry()

        mock_timer.stop.assert_not_called()

    # ---- restore_root_geometry ----

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_root_geometry_enables_fullscreen(self, mock_env):
        """restore_root_geometry() calls showFullScreen() when env flag is True."""
        def _get(key, default=None, cast_type=None):
            if key == EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN:
                return True
            return default

        mock_env.get.side_effect = _get

        GuiManager.restore_root_geometry()

        self.mock_root.showFullScreen.assert_called_once()

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_root_geometry_applies_size(self, mock_env):
        """restore_root_geometry() calls resize() when a size is present."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_SIZE: '1024x768',
                EnvironmentKeys.ui.UI_WINDOW_POSITION: None,
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'normal',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        GuiManager.restore_root_geometry()

        self.mock_root.resize.assert_called_with(1024, 768)

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_root_geometry_applies_position(self, mock_env):
        """restore_root_geometry() calls move() when a position is present."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_SIZE: None,
                EnvironmentKeys.ui.UI_WINDOW_POSITION: (100, 200),
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'normal',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        GuiManager.restore_root_geometry()

        self.mock_root.move.assert_called_with(100, 200)

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_root_geometry_maximized_state(self, mock_env):
        """restore_root_geometry() calls showMaximized() for 'zoomed' state."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_SIZE: None,
                EnvironmentKeys.ui.UI_WINDOW_POSITION: None,
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'zoomed',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        GuiManager.restore_root_geometry()

        self.mock_root.showMaximized.assert_called_once()

    @patch('pyrox.services.gui.EnvManager')
    def test_restore_root_geometry_minimized_state(self, mock_env):
        """restore_root_geometry() calls showMinimized() for 'iconic' state."""
        def _get(key, default=None, cast_type=None):
            mapping = {
                EnvironmentKeys.ui.UI_WINDOW_FULLSCREEN: False,
                EnvironmentKeys.ui.UI_WINDOW_SIZE: None,
                EnvironmentKeys.ui.UI_WINDOW_POSITION: None,
                EnvironmentKeys.ui.UI_WINDOW_STATE: 'iconic',
            }
            return mapping.get(key, default)

        mock_env.get.side_effect = _get

        GuiManager.restore_root_geometry()

        self.mock_root.showMinimized.assert_called_once()


# ---------------------------------------------------------------------------
# Tk binding → Qt key-sequence conversion
# ---------------------------------------------------------------------------

class TestTkBindingToQtSequence(unittest.TestCase):
    """Tests for the module-level _tk_binding_to_qt_sequence() helper."""

    def test_ctrl_alpha_converts(self):
        """<Control-s> becomes Ctrl+S."""
        self.assertEqual(_tk_binding_to_qt_sequence('<Control-s>'), 'Ctrl+S')

    def test_ctrl_shift_alpha_converts(self):
        """<Control-Shift-S> becomes Ctrl+Shift+S."""
        self.assertEqual(_tk_binding_to_qt_sequence('<Control-Shift-S>'), 'Ctrl+Shift+S')

    def test_function_key_only(self):
        """<F1> becomes F1."""
        self.assertEqual(_tk_binding_to_qt_sequence('<F1>'), 'F1')

    def test_alt_function_key(self):
        """<Alt-F4> becomes Alt+F4."""
        self.assertEqual(_tk_binding_to_qt_sequence('<Alt-F4>'), 'Alt+F4')

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        self.assertIsNone(_tk_binding_to_qt_sequence(''))

    def test_no_angle_brackets_returns_none(self):
        """String without angle brackets returns None."""
        self.assertIsNone(_tk_binding_to_qt_sequence('Control-s'))

    def test_multiple_modifiers(self):
        """<Control-Alt-Delete> becomes Ctrl+Alt+Delete."""
        self.assertEqual(_tk_binding_to_qt_sequence('<Control-Alt-Delete>'), 'Ctrl+Alt+Delete')


# ---------------------------------------------------------------------------
# GuiManager.insert_menu_command_with_accelerator
# ---------------------------------------------------------------------------

class TestInsertMenuCommandWithAccelerator(unittest.TestCase):
    """Tests for GuiManager.insert_menu_command_with_accelerator()."""

    def setUp(self):
        _reset_manager()
        self.mock_root = MagicMock()
        GuiManager._root_window = self.mock_root
        self.mock_menu = MagicMock()
        self.mock_menu.actions.return_value = []

    def tearDown(self):
        _reset_manager()

    @patch('pyrox.services.gui.QAction')
    def test_creates_action_and_adds_to_menu(self, mock_qaction_class):
        """insert_menu_command_with_accelerator() creates a QAction and adds it to the menu."""
        mock_action = MagicMock()
        mock_qaction_class.return_value = mock_action

        GuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=Mock(),
            accelerator='Ctrl+Q',
        )

        mock_qaction_class.assert_called_once_with('Exit', self.mock_menu)
        self.mock_menu.addAction.assert_called_once_with(mock_action)

    @patch('pyrox.services.gui.QKeySequence')
    @patch('pyrox.services.gui.QAction')
    def test_sets_shortcut_when_accelerator_provided(self, mock_qaction_class, mock_key_seq_class):
        """An accelerator string results in setShortcut() being called on the action."""
        mock_action = MagicMock()
        mock_qaction_class.return_value = mock_action
        mock_key_seq = MagicMock()
        mock_key_seq_class.return_value = mock_key_seq

        GuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=Mock(),
            accelerator='Ctrl+Q',
        )

        mock_action.setShortcut.assert_called_once_with(mock_key_seq)

    @patch('pyrox.services.gui.QAction')
    def test_no_shortcut_when_empty_accelerator(self, mock_qaction_class):
        """No shortcut is set when accelerator is an empty string."""
        mock_action = MagicMock()
        mock_qaction_class.return_value = mock_action

        GuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=Mock(),
            accelerator='',
        )

        mock_action.setShortcut.assert_not_called()

    @patch('pyrox.services.gui.QAction')
    def test_connects_command_to_triggered(self, mock_qaction_class):
        """The command is connected to the action's triggered signal."""
        mock_action = MagicMock()
        mock_qaction_class.return_value = mock_action
        cmd = Mock()

        GuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=cmd,
        )

        mock_action.triggered.connect.assert_called_once_with(cmd)

    @patch('pyrox.services.gui.QAction')
    def test_no_connection_when_command_is_none(self, mock_qaction_class):
        """No triggered connection is made when command is None."""
        mock_action = MagicMock()
        mock_qaction_class.return_value = mock_action

        GuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='Exit',
            command=None,
        )

        mock_action.triggered.connect.assert_not_called()

    @patch('pyrox.services.gui.QAction')
    def test_inserts_at_correct_index_when_actions_exist(self, mock_qaction_class):
        """insertAction() is used when the target index is within existing actions."""
        mock_action = MagicMock()
        mock_qaction_class.return_value = mock_action
        existing_action = MagicMock()
        self.mock_menu.actions.return_value = [existing_action, MagicMock()]

        GuiManager.insert_menu_command_with_accelerator(
            menu=self.mock_menu,
            index=0,
            label='First',
            command=Mock(),
        )

        self.mock_menu.insertAction.assert_called_once_with(existing_action, mock_action)


if __name__ == '__main__':
    unittest.main()
